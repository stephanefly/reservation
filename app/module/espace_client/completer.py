from django.shortcuts import redirect, get_object_or_404, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from app.models import Event, EventDetails, EventTemplate


@require_http_methods(["POST"])
def update_event_and_redirect(request, event_id, data_type_template, update_field, redirect_view):
    event = get_object_or_404(Event, pk=event_id)
    new_data = request.POST.get(data_type_template)

    if update_field == 'event_details':
        model_class = EventDetails
    elif update_field == 'event_template':
        model_class = EventTemplate

    # Récupérer ou créer l'objet lié
    model_instance, created = model_class.objects.get_or_create(event=event, defaults={data_type_template: new_data})
    if not created:
        setattr(model_instance, data_type_template, new_data)
    model_instance.save()

    # Redirection vers l'URL "choix client" avec le token approprié
    client_token = request.session.get('client_token')
    if client_token:
        url = reverse(redirect_view, args=[event_id, client_token])
        return redirect(url)
    else:
        return render(request, 'app/page_client/logging.html')
