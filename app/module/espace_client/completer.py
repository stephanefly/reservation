from django.shortcuts import redirect, get_object_or_404, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from app.models import Event, EventDetails, EventTemplate


@require_http_methods(["POST"])
def update_event_and_redirect(request, event_id, data_type, update_field, redirect_view):
    event = get_object_or_404(Event, pk=event_id)
    new_data = request.POST.get(data_type)

    # Vérifier si le champ à mettre à jour est event_details ou event_template
    if update_field == 'event_details':
        model_instance = event.event_details
    elif update_field == 'event_template':
        model_instance = event.event_template


    # Si l'instance du modèle existe, mettre à jour les données
    if model_instance:
        setattr(model_instance, data_type, new_data)
        model_instance.save()
    else:
        # Si l'instance n'existe pas, en créer une nouvelle avec les données
        model_class = EventDetails if update_field == 'event_details' else EventTemplate
        setattr(event, update_field, model_class(**{data_type: new_data}))
        event.save()

    # Redirection vers l'URL "choix client" avec le token approprié
    client_token = request.session.get('client_token')
    if client_token:
        url = reverse(redirect_view, args=[event_id, client_token])
        return redirect(url)
    else:
        return render(request, 'app/page_client/logging.html')
