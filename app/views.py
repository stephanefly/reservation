from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_protect
from datetime import datetime, timedelta
from django.http import QueryDict
from .models import Client, Event
from threading import Thread
from django.views.decorators.http import require_http_methods
from django.shortcuts import render
from django.http import FileResponse
from .module.post_form import initialize_event
from .module.trello.create_card import create_card
from django.http import HttpResponse
from reportlab.pdfgen import canvas
from io import BytesIO


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
    client = event.client
    event_details = event.event_details
    event_product = event.event_product
    event_option = event.event_option

    # Mise à jour des informations du client
    client.nom = request.POST.get('client_nom')
    client.prenom = request.POST.get('client_prenom')
    client.mail = request.POST.get('client_mail')
    client.numero_telephone = request.POST.get('client_numero_telephone')
    client.how_find = request.POST.get('client_how_find')
    client.save()

    # Mise à jour des détails de l'événement
    event_details.date_evenement = request.POST.get('date_evenement')
    event_details.adresse_evenement = request.POST.get('adresse_evenement')
    event_details.ville_evenement = request.POST.get('ville_evenement')
    event_details.code_postal_evenement = request.POST.get('code_postal_evenement')
    event_details.save()

    # Mise à jour des produits de l'événement
    event_product.photobooth = request.POST.get('photobooth') == 'on'
    event_product.miroirbooth = request.POST.get('miroirbooth') == 'on'
    event_product.videobooth = request.POST.get('videobooth') == 'on'
    event_product.save()

    # Mise à jour des options de l'événement
    event_option.mur_floral = request.POST.get('mur_floral') == 'on'
    event_option.phonebooth = request.POST.get('phonebooth') == 'on'
    event_option.magnets_value = request.POST.get('magnets', None)
    event_option.livraison = request.POST.get('livraison') == 'on'
    event_option.duree = request.POST.get('duree', None)
    event_option.save()

    # Mise à jour des autres informations de l'événement
    event.prix_brut = request.POST.get('prix_brut')
    event.prix_proposed = request.POST.get('prix_proposed')
    event.save()

    # Rediriger vers la page de détails de l'événement mise à jour ou toute autre page appropriée
    return redirect('info_event', id=event.id)


def generate_pdf(request, event_id):
    # Récupérez les données de l'événement en fonction de l'event_id
    event = Event.objects.get(id=event_id)

    # Créez un objet BytesIO pour stocker le PDF en mémoire
    buffer = BytesIO()

    # Créez un objet Canvas pour générer le PDF
    pdf = canvas.Canvas(buffer)

    # Informations sur la facture
    client_name = "Nom du Client"
    invoice_date = datetime.now().strftime("%d/%m/%Y")
    invoice_number = "2024001"
    items = [
        {"description": "Service Photobooth", "quantity": 1, "price": 200},
        {"description": "Location Miroirbooth", "quantity": 2, "price": 150},
        {"description": "Location 360booth", "quantity": 1, "price": 300},
    ]

    # Titre de la facture
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(200, 750, "FACTURE")

    # Informations du client
    pdf.setFont("Helvetica", 12)
    pdf.drawString(50, 700, f"Client : {client_name}")
    pdf.drawString(50, 680, f"Date : {invoice_date}")
    pdf.drawString(50, 660, f"Numéro de Facture : {invoice_number}")

    # Tableau des articles
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(50, 620, "Description")
    pdf.drawString(250, 620, "Quantité")
    pdf.drawString(350, 620, "Prix unitaire")
    pdf.drawString(450, 620, "Total")

    y_position = 600
    total_amount = 0

    for item in items:
        description = item["description"]
        quantity = item["quantity"]
        price = item["price"]
        total_item = quantity * price

        pdf.drawString(50, y_position, description)
        pdf.drawString(250, y_position, str(quantity))
        pdf.drawString(350, y_position, f"${price}")
        pdf.drawString(450, y_position, f"${total_item}")

        y_position -= 20
        total_amount += total_item

    # Total de la facture
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(350, y_position - 20, "Montant Total :")
    pdf.drawString(450, y_position - 20, f"${total_amount}")

    # Terminez le PDF
    pdf.showPage()
    pdf.save()

    # Réinitialisez le tampon et renvoyez le PDF en tant que réponse HTTP
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="facture.pdf"'
    return response
