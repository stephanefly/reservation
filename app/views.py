from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_protect
from datetime import datetime, timedelta

from .models import Client, EventDetails, Event


def demande_devis(request):
    today_date = datetime.now().date()
    date_dans_deux_ans = today_date + timedelta(days=365 * 2)
    today_date_str = today_date.strftime("%Y-%m-%d")
    date_dans_deux_ans_str = date_dans_deux_ans.strftime("%Y-%m-%d")

    if request.method == 'POST':
        # Extraction des données du formulaire
        client_nom = request.POST.get('nom')
        client_prenom = request.POST.get('prenom')
        client_mail = request.POST.get('mail')
        client_telephone = request.POST.get('numero_telephone')
        client_how_find = request.POST.get('client_how_find')

        event_date = request.POST.get('date_evenement')
        event_adresse = request.POST.get('adresse_evenement')
        event_ville = request.POST.get('ville_evenement')
        event_code_postal = request.POST.get('code_postal_evenement')

        image = request.POST.get('selectedImage')
        print(image)

        # Création de l'objet Client
        client = Client(
            nom=client_nom,
            prenom=client_prenom,
            mail=client_mail,
            numero_telephone=client_telephone,
            how_find=client_how_find
        )
        client.save()

        # Création de l'objet EventDetails
        event_details = EventDetails(
            date_evenement=event_date,
            adresse_evenement=event_adresse,
            ville_evenement=event_ville,
            code_postal_evenement=event_code_postal
        )
        event_details.save()

        # event = Event(
        #     client=client,
        #     event_details = event_details,
        #     service_details =
        #     status = 'Initied',
        #     )

        return redirect('remerciement')        # Redirigez l'utilisateur vers une page de confirmation

    return render(request, 'app/demande_devis.html', {
        'today_date': today_date_str,
        'date_dans_deux_ans': date_dans_deux_ans_str,
    })


def remerciement(request):
    return render(request, 'app/remerciement.html')

def info_lst_devis(request):

    all_event = Client.objects.all()

    return render(request, 'app/lst_devis.html', {'all_event': all_event,})
