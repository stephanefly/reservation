from django.shortcuts import redirect
from django.urls import reverse
from django.contrib.auth.models import Group


class BackendAuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        # Ignorer la page de connexion pour éviter la boucle de redirection
        if request.path == reverse('login'):
            return None

        # Vérifie que l'utilisateur est authentifié et est un administrateur pour accéder à /backend/
        if request.path.startswith('/backend/'):
            if not request.user.is_authenticated or not request.user.is_staff:
                return redirect(reverse('login'))
        return None


class TeamOnlyMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        # Ignorer la page de connexion pour éviter la boucle de redirection
        if request.path == reverse('login'):
            return None

        # Vérifie si l'utilisateur est authentifié
        if request.path.startswith('/team/'):
            if not request.user.is_authenticated:
                return redirect(reverse('login'))

            # Vérifie si l'utilisateur est dans le groupe "team"
            if not request.user.groups.filter(name="team").exists():
                return redirect(reverse('login'))  # Redirige si l'utilisateur n'est pas dans le groupe "team"

        return None
