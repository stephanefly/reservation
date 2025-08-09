from django.shortcuts import redirect, get_object_or_404, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from app.models import Event, EventDetails, EventTemplate


@require_http_methods(["POST"])
def update_event_and_redirect(request, event_id, data_type_template, update_field, redirect_view):
    event = get_object_or_404(Event, pk=event_id)
    token = request.session.get('client_token')
    new_data = request.POST.get(data_type_template)

    if update_field == 'event_details':
        setattr(event.event_details, data_type_template, new_data)
        event.event_details.save()
    elif update_field == 'event_option':
        setattr(event.event_option, data_type_template, new_data)
        event.event_option.save()
    elif update_field == 'event_template':
        if event.event_template:
            setattr(event.event_template, data_type_template, new_data)
            event.event_template.save()
        else:
            event_template = EventTemplate(**{data_type_template: new_data})
            event_template.save()
            event.event_template = event_template
            event.save()

    return redirect(redirect_view, event_id, token)


    # Redirection vers l'URL "choix client" avec le token approprié
    client_token = request.session.get('client_token')
    if client_token:
        url = reverse(redirect_view, args=[event_id, client_token])
        return redirect(url)
    else:
        return render(request, 'app/page_client/logging.html')
