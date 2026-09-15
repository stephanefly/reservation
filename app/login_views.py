from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import redirect


@login_required
def login_redirect(request):
    """Ouvre l'espace autorisé après la connexion."""
    if request.user.is_staff:
        return redirect('lst_devis')
    if request.user.groups.filter(name='team').exists():
        return redirect('team_planning')
    return HttpResponseForbidden(
        "Votre compte n'a pas accès à l'espace équipe. Contactez l'administrateur."
    )
