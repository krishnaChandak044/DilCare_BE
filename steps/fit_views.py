import requests
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.utils import timezone
from datetime import timedelta
from .models import DailyStepLog

def _get_or_create_today_log(user):
    today = timezone.localdate()
    log, _ = DailyStepLog.objects.get_or_create(user=user, date=today)
    return log

class GoogleFitSyncView(APIView):
    """
    POST: Sync Google Fit steps manually from FE token
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        access_token = request.data.get('access_token')
        if not access_token:
            return Response({"error": "No access token provided"}, status=status.HTTP_400_BAD_REQUEST)

        now = timezone.now()
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)
        
        start_millis = int(start_of_day.timestamp() * 1000)
        end_millis = int(end_of_day.timestamp() * 1000)

        headers = {'Authorization': f'Bearer {access_token}'}
        body = {
            "aggregateBy": [{"dataTypeName": "com.google.step_count.delta"}],
            "bucketByTime": {"durationMillis": 86400000},
            "startTimeMillis": start_millis,
            "endTimeMillis": end_millis
        }
        
        try:
            res = requests.post(
                'https://www.googleapis.com/fitness/v1/users/me/dataset:aggregate',
                headers=headers,
                json=body,
                timeout=10
            )
            res.raise_for_status()
            data = res.json()
            
            steps = 0
            for bucket in data.get('bucket', []):
                for dataset in bucket.get('dataset', []):
                    for point in dataset.get('point', []):
                        for value in point.get('value', []):
                            steps += value.get('intVal', 0)
                            
            log = _get_or_create_today_log(request.user)
            log.synced_steps = steps
            log.source = 'google_fit'
            log.save()
                
            return Response({"status": "success", "steps_synced": steps}, status=status.HTTP_200_OK)
            
        except requests.exceptions.RequestException as e:
            return Response({"error": f"Failed to connect to Google Fit: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            return Response({"error": f"Unexpected error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
