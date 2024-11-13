
from ..models import EventTemplate, Event
from datetime import datetime, timedelta, timezone
from django.shortcuts import redirect, get_object_or_404
from django.shortcuts import render
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
import os
from myselfiebooth.settings import FTP_SERVER, FTP_PORT, FTP_USER, FTP_PASS, PREPA_EVENT_PATH, NAS_EVENT_PATH

from ..module.ftp_myselfiebooth.connect_ftp import FTPStorage

today_date = datetime.now().date()

def template_to_do(request):
    today_date = datetime.now()
    end_week_date = today_date + timedelta(days=30)

    lst_event_prio = Event.objects.filter(
        signer_at__isnull=False,
        event_details__date_evenement__range=[today_date, end_week_date]
    ).order_by('event_details__date_evenement')

    return render(request, 'app/team/template_to_do.html', {
        'lst_event_prio': lst_event_prio,
    })

def change_status(request, pk):
    event_template = get_object_or_404(EventTemplate, pk=pk)
    event_template.statut = not event_template.statut
    event_template.save()
    return redirect('tableau_de_bord')


def upload_image(request, event_id):
    if request.method == 'POST':
        image = request.FILES.get('myTemplate')
        if image:
            print(image)
            print(event_id)
            # Sauvegarder l'image sur le NAS via SFTPStorage
            # Créer une instance de FTPStorage
            ftp_storage = FTPStorage(
                hostname=FTP_SERVER,
                username=FTP_USER,
                password=FTP_PASS,
                prepa_event_path=PREPA_EVENT_PATH,
                nas_event_path=NAS_EVENT_PATH,
                port=FTP_PORT
            )

            saved_path = ftp_storage._save_png(image, event_id)

            return redirect('template_to_do')

    return redirect('template_to_do')

def view_image(request, event_id):
    sftp_storage = FTPStorage  # Utilisez votre instance de connexion SFTP
    file_data, file_name = sftp_storage._get_last_image(event_id)  # Récupérer l'image

    # Détectez le type de contenu (vous pouvez ajuster selon votre fichier)
    content_type = "image/jpeg" if file_name.endswith(".jpg") or file_name.endswith(".jpeg") else "image/png"

    # Retourne l'image sans forcer le téléchargement
    response = HttpResponse(file_data, content_type=content_type)
    return response
