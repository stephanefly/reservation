from django.shortcuts import redirect
from django.urls import reverse

class BackendAuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        if request.path.startswith('/backend/') and not request.user.is_authenticated:
            return redirect(reverse('login'))
        return None
