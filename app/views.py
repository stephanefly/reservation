from django.shortcuts import redirect, get_object_or_404
from datetime import datetime, timedelta
from django.http import QueryDict

from myselfiebooth.settings import MP
from .models import Event
from threading import Thread
from django.views.decorators.http import require_http_methods
from django.shortcuts import render
from django.core.mail import EmailMessage
from .module.data_bdd.post_form import initialize_event
from .module.data_bdd.update_event import update_data
from .module.devis_pdf.generate_pdf import generate_devis_pdf
from .module.trello.create_card import create_card
from django.http import HttpResponse
from reportlab.pdfgen import canvas
from io import BytesIO
import win32com.client as win32




def demande_devis(request):
    today_date = datetime.now().date()
    date_dans_deux_ans = today_date + timedelta(days=365 * 2)
    today_date_str = today_date.strftime("%Y-%m-%d")
    date_dans_deux_ans_str = date_dans_deux_ans.strftime("%Y-%m-%d")

    if request.method == 'POST':
        form_data = request.POST.dict()
        request.session['demande_devis_data'] = form_data
        return render(request, 'app/confirmation.html', {'form_data': form_data})

    # Vérifiez d'abord s'il y a des données préremplies dans la session
    form_data = request.session.get('demande_devis_data', {})

    # Créez un objet QueryDict à partir des données pour préremplir le formulaire
    initial_data = QueryDict(mutable=True)
    initial_data.update(form_data)

    return render(request, 'app/demande_devis.html', {
        'today_date': today_date_str,
        'date_dans_deux_ans': date_dans_deux_ans_str,
        'form': initial_data  # Utilisez initial_data pour préremplir le formulaire
    })


def confirmation(request):

    if request.method == 'POST':

        post_data = {
            "client": {
                "nom": request.POST.get('nom'),
                "prenom": request.POST.get('prenom'),
                "mail": request.POST.get('mail'),
                "telephone": request.POST.get('numero_telephone'),
                "how_find": request.POST.get('client_how_find'),
            },
            "event": {
                "date": request.POST.get('date_evenement'),
                "adresse": request.POST.get('adresse_evenement'),
                "ville": request.POST.get('ville_evenement'),
                "code_postal": request.POST.get('code_postal_evenement'),
            },
            "product": request.POST.get('selectedImages'),
            "options": {
                "murfloral": True if request.POST.get('murfloral') else False,
                "phonebooth": True if request.POST.get('phonebooth') else False,
                "magnets_range": int(request.POST.get('magnets_range', 0)) if int(request.POST.get('magnets_range', 0))>0 else None,
                "livraison": True if request.POST.get('livraison') else False,
                "heure_range": int(request.POST.get('heure_range', 0)) if request.POST.get('heure_range', 0) else None,
            }
        }
        print(post_data)
        initialize_event(post_data)
        # thread_bdd = Thread(target=initialize_event, args=(post_data,))
        # thread_bdd.start()
        # thread_trello = Thread(target=create_card, args=(post_data,))
        # thread_trello.start()

        return redirect('remerciement')  # Redirigez vers une URL de succès après la sauvegarde

    return render(request, 'app/confirmation.html')


def remerciement(request):
    return render(request, 'app/remerciement.html')


def info_lst_devis(request):
    all_event = Event.objects.all()
    return render(request, 'app/lst_devis.html', {'all_event': all_event,})


def info_event(request, id):
    event = get_object_or_404(Event, id=id)
    return render(request, 'app/info_event.html', {'event': event})


@require_http_methods(["POST"])
def update_event(request, id):
    event = get_object_or_404(Event, id=id)
    update_data(event, request)

    # Rediriger vers la page de détails de l'événement mise à jour
    return redirect('info_event', id=event.id)


def generate_pdf(request, event_id):
    # Récupérez les données de l'événement en fonction de l'event_id
    event = Event.objects.get(id=event_id)

    buffer = generate_devis_pdf(event)

    # Réinitialisez le tampon et renvoyez le PDF en tant que réponse HTTP
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="facture.pdf"'
    return response

def envoi_mail_devis(request, event_id):
    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText

    # Connexion sécurisée au serveur SMTP via SSL
    server = smtplib.SMTP_SSL('smtp.ionos.fr', 465)

    try:
        name = "Name"  # Remplissez le nom ici
        server.login("stephane.faure@3dmouvstudio.com", MP)

        TOADDR = "stephane.faure@safrangroup.com"
        FromADDR = "stephane.faure@3dmouvstudio.com"

        msg = MIMEMultipart('alternative')
        msg['Subject'] = "Sujet de l'email"
        msg['From'] = FromADDR
        msg['To'] = TOADDR

        # Corps de l'email
        html = """\
                <html>
                  <body>
                    <p><span style="color: rgb(0,0,0);">Cher {0},</span></p>
                   <p>
                      Votre corps de l'email ici.
                    </p>
                    <p>Cordialement,<br />
                    Votre nom ici...
                    </p>
                    </body>
                </html>
                """.format(name.split()[0])
        msg.attach(MIMEText(html, 'html'))
        server.sendmail(FromADDR, TOADDR, msg.as_string())
    except Exception as e:
        # Afficher les messages d'erreur
        print(e)
    finally:
        server.quit()
