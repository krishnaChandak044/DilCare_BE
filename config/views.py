from django.http import HttpResponse

def root_view(request):
    return HttpResponse("DilCare Backend API is running.")
