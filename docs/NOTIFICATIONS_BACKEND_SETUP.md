# /**
#  * BACKEND IMPLEMENTATION EXAMPLES
#  * 
#  * This file contains example code for implementing the notification endpoints
#  * in your Django backend (DilCare_BE).
#  * 
#  * Copy and adapt these examples to your project structure.
#  */

# // ============================================================================
# // DJANGO MODELS
# // ============================================================================

# /**
#  * Add to models.py in accounts app:
#  * 
#  * from django.db import models
#  * from django.contrib.auth.models import User
#  * 
#  * class UserDeviceToken(models.Model):
#  *     '''Store device tokens for push notifications'''
#  *     user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='device_token_record')
#  *     token = models.CharField(max_length=500, unique=True)
#  *     platform = models.CharField(
#  *         max_length=20,
#  *         choices=[('ios', 'iOS'), ('android', 'Android'), ('web', 'Web')],
#  *         default='android'
#  *     )
#  *     app_version = models.CharField(max_length=20, blank=True)
#  *     registered_at = models.DateTimeField(auto_now_add=True)
#  *     last_used = models.DateTimeField(auto_now=True)
#  * 
#  *     class Meta:
#  *         db_table = 'account_device_tokens'
#  * 
#  *     def __str__(self):
#  *         return f'{self.user} - {self.platform}'
#  * 
#  * 
#  * class NotificationRecord(models.Model):
#  *     '''Track all notifications sent'''
#  *     notification_id = models.CharField(max_length=100, unique=True, primary_key=True)
#  *     user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
#  *     title = models.CharField(max_length=255)
#  *     body = models.TextField()
#  *     notification_type = models.CharField(
#  *         max_length=50,
#  *         choices=[
#  *             ('sos_alert', 'SOS Alert'),
#  *             ('medication_reminder', 'Medication Reminder'),
#  *             ('health_update', 'Health Update'),
#  *             ('family_message', 'Family Message'),
#  *             ('appointment_reminder', 'Appointment Reminder'),
#  *             ('activity_goal', 'Activity Goal'),
#  *         ]
#  *     )
#  *     action = models.CharField(max_length=100, blank=True)
#  *     data = models.JSONField(default=dict)
#  *     read = models.BooleanField(default=False)
#  *     opened = models.BooleanField(default=False)
#  *     opened_at = models.DateTimeField(null=True, blank=True)
#  *     created_at = models.DateTimeField(auto_now_add=True)
#  *     sent_at = models.DateTimeField(auto_now_add=True)
#  * 
#  *     class Meta:
#  *         db_table = 'notification_records'
#  *         ordering = ['-created_at']
#  * 
#  *     def __str__(self):
#  *         return f'{self.title} - {self.user}'
#  */

# // ============================================================================
# // DJANGO VIEWS/ENDPOINTS
# // ============================================================================

# /**
#  * Add to views.py in accounts app:
#  * 
#  * from rest_framework import status, viewsets
#  * from rest_framework.decorators import action
#  * from rest_framework.response import Response
#  * from rest_framework.permissions import IsAuthenticated
#  * import requests
#  * import uuid
#  * from datetime import datetime
#  * 
#  * class NotificationViewSet(viewsets.ViewSet):
#  *     permission_classes = [IsAuthenticated]
#  * 
#  *     @action(detail=False, methods=['post'])
#  *     def register_token(self, request):
#  *         '''Register device token for push notifications'''
#  *         try:
#  *             token = request.data.get('device_token')
#  *             platform = request.data.get('platform', 'android')
#  *             app_version = request.data.get('app_version', '')
#  * 
#  *             if not token:
#  *                 return Response(
#  *                     {'success': False, 'error': 'device_token required'},
#  *                     status=status.HTTP_400_BAD_REQUEST
#  *                 )
#  * 
#  *             # Update or create device token record
#  *             UserDeviceToken.objects.update_or_create(
#  *                 user=request.user,
#  *                 defaults={
#  *                     'token': token,
#  *                     'platform': platform,
#  *                     'app_version': app_version
#  *                 }
#  *             )
#  * 
#  *             return Response({
#  *                 'success': True,
#  *                 'message': 'Device token registered'
#  *             })
#  * 
#  *         except Exception as e:
#  *             return Response(
#  *                 {'success': False, 'error': str(e)},
#  *                 status=status.HTTP_500_INTERNAL_SERVER_ERROR
#  *             )
#  * 
#  *     @action(detail=False, methods=['post'])
#  *     def send_push(self, request):
#  *         '''Send push notification to a user'''
#  *         try:
#  *             user_id = request.data.get('user_id')
#  *             title = request.data.get('title')
#  *             body = request.data.get('body')
#  *             action = request.data.get('action')
#  *             notification_type = request.data.get('type', 'info')
#  *             data = request.data.get('data', {})
#  * 
#  *             user = User.objects.get(id=user_id)
#  *             device_record = UserDeviceToken.objects.filter(user=user).first()
#  * 
#  *             if not device_record:
#  *                 return Response({
#  *                     'success': False,
#  *                     'error': 'User has no registered device'
#  *                 })
#  * 
#  *             notification_id = f'notif-{uuid.uuid4()}'
#  * 
#  *             # Send via Expo Push API
#  *             expo_response = requests.post(
#  *                 'https://exp.host/--/api/v2/push/send',
#  *                 headers={
#  *                     'Accept': 'application/json',
#  *                     'Content-Type': 'application/json',
#  *                 },
#  *                 json={
#  *                     'to': device_record.token,
#  *                     'title': title,
#  *                     'body': body,
#  *                     'data': {
#  *                         'notification_id': notification_id,
#  *                         'action': action,
#  *                         **data
#  *                     },
#  *                     'badge': 1,
#  *                     'sound': 'default'
#  *                 }
#  *             )
#  * 
#  *             if expo_response.status_code == 200:
#  *                 # Save notification record
#  *                 NotificationRecord.objects.create(
#  *                     notification_id=notification_id,
#  *                     user=user,
#  *                     title=title,
#  *                     body=body,
#  *                     notification_type=notification_type,
#  *                     action=action,
#  *                     data=data
#  *                 )
#  * 
#  *                 return Response({
#  *                     'success': True,
#  *                     'notification_id': notification_id,
#  *                     'sent_to': 1
#  *                 })
#  *             else:
#  *                 return Response({
#  *                     'success': False,
#  *                     'error': 'Expo API error'
#  *                 }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
#  * 
#  *         except Exception as e:
#  *             return Response(
#  *                 {'success': False, 'error': str(e)},
#  *                 status=status.HTTP_500_INTERNAL_SERVER_ERROR
#  *             )
#  * 
#  *     @action(detail=False, methods=['post'])
#  *     def send_broadcast(self, request):
#  *         '''Send notification to multiple users'''
#  *         try:
#  *             user_ids = request.data.get('user_ids', [])
#  *             title = request.data.get('title')
#  *             body = request.data.get('body')
#  *             action = request.data.get('action')
#  *             notification_type = request.data.get('type', 'info')
#  *             data = request.data.get('data', {})
#  * 
#  *             users = User.objects.filter(id__in=user_ids)
#  *             notification_id = f'notif-{uuid.uuid4()}'
#  *             sent_count = 0
#  * 
#  *             for user in users:
#  *                 device_record = UserDeviceToken.objects.filter(user=user).first()
#  *                 if device_record:
#  *                     requests.post(
#  *                         'https://exp.host/--/api/v2/push/send',
#  *                         json={
#  *                             'to': device_record.token,
#  *                             'title': title,
#  *                             'body': body,
#  *                             'data': {
#  *                                 'notification_id': notification_id,
#  *                                 'action': action,
#  *                                 **data
#  *                             },
#  *                             'badge': 1,
#  *                             'sound': 'default'
#  *                         }
#  *                     )
#  * 
#  *                     # Save notification record
#  *                     NotificationRecord.objects.create(
#  *                         notification_id=f'{notification_id}-{user.id}',
#  *                         user=user,
#  *                         title=title,
#  *                         body=body,
#  *                         notification_type=notification_type,
#  *                         action=action,
#  *                         data=data
#  *                     )
#  *                     sent_count += 1
#  * 
#  *             return Response({
#  *                 'success': True,
#  *                 'notification_id': notification_id,
#  *                 'sent_to': sent_count
#  *             })
#  * 
#  *         except Exception as e:
#  *             return Response(
#  *                 {'success': False, 'error': str(e)},
#  *                 status=status.HTTP_500_INTERNAL_SERVER_ERROR
#  *             )
#  * 
#  *     @action(detail=False, methods=['post'])
#  *     def log_interaction(self, request):
#  *         '''Log notification interaction'''
#  *         try:
#  *             notification_id = request.data.get('notification_id')
#  *             interaction_type = request.data.get('interaction_type')
#  * 
#  *             notification = NotificationRecord.objects.filter(
#  *                 notification_id=notification_id
#  *             ).first()
#  * 
#  *             if notification:
#  *                 if interaction_type == 'opened':
#  *                     notification.opened = True
#  *                     notification.opened_at = datetime.now()
#  *                     notification.save()
#  * 
#  *             return Response({'success': True})
#  * 
#  *         except Exception as e:
#  *             return Response(
#  *                 {'success': False, 'error': str(e)},
#  *                 status=status.HTTP_500_INTERNAL_SERVER_ERROR
#  *             )
#  * 
#  *     @action(detail=False, methods=['get'])
#  *     def history(self, request):
#  *         '''Get notification history'''
#  *         limit = int(request.query_params.get('limit', 20))
#  *         offset = int(request.query_params.get('offset', 0))
#  * 
#  *         notifications = NotificationRecord.objects.filter(
#  *             user=request.user
#  *         )[offset:offset+limit]
#  * 
#  *         return Response({
#  *             'success': True,
#  *             'total': NotificationRecord.objects.filter(user=request.user).count(),
#  *             'notifications': [
#  *                 {
#  *                     'id': n.notification_id,
#  *                     'title': n.title,
#  *                     'body': n.body,
#  *                     'type': n.notification_type,
#  *                     'action': n.action,
#  *                     'read': n.read,
#  *                     'created_at': n.created_at.isoformat(),
#  *                     'data': n.data
#  *                 }
#  *                 for n in notifications
#  *             ]
#  *         })
#  */

# // ============================================================================
# // URLS CONFIGURATION
# // ============================================================================

# /**
#  * Add to urls.py in config:
#  * 
#  * from rest_framework.routers import DefaultRouter
#  * from accounts.views import NotificationViewSet
#  * 
#  * router = DefaultRouter()
#  * router.register('notifications', NotificationViewSet, basename='notifications')
#  * 
#  * urlpatterns = [
#  *     path('api/', include(router.urls)),
#  * ]
#  */

# // ============================================================================
# // SENDING NOTIFICATIONS FROM OTHER VIEWS
# // ============================================================================

# /**
#  * Example: Send notification when SOS alert is triggered
#  * 
#  * from services.notificationService import send_push_notification
#  * 
#  * @api_view(['POST'])
#  * @permission_classes([IsAuthenticated])
#  * def trigger_sos(request):
#  *     try:
#  *         user = request.user
#  *         
#  *         # Create SOS record
#  *         sos = SOS.objects.create(
#  *             user=user,
#  *             location_lat=request.data.get('latitude'),
#  *             location_lng=request.data.get('longitude'),
#  *             description=request.data.get('description')
#  *         )
#  * 
#  *         # Get family members
#  *         family_members = user.family_members.all()
#  * 
#  *         # Send notification to each family member
#  *         for member in family_members:
#  *             member_user = User.objects.get(id=member.user_id)
#  *             send_push_notification(
#  *                 user_id=member_user.id,
#  *                 title=f'SOS Alert: {user.get_full_name()} is calling for help!',
#  *                 body=f'Last location: {sos.location_address}. Last seen {sos.created_at}.',
#  *                 action='sos_alert',
#  *                 notification_type='error',
#  *                 data={
#  *                     'sos_id': str(sos.id),
#  *                     'action': 'sos_alert'
#  *                 }
#  *             )
#  * 
#  *         return Response({
#  *             'success': True,
#  *             'sos_id': sos.id,
#  *             'notification_sent_to': family_members.count()
#  *         })
#  * 
#  *     except Exception as e:
#  *         return Response(
#  *             {'success': False, 'error': str(e)},
#  *             status=status.HTTP_500_INTERNAL_SERVER_ERROR
#  *         )
#  */

# export default {};
