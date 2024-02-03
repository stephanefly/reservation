from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_protect
from datetime import datetime, timedelta
from django.http import QueryDict
from .models import Client, EventDetails, Event


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

        client_mail = request.POST.get('mail')
        client_mail = request.POST.get('mail')
        client_mail = request.POST.get('mail')
        client_telephone = request.POST.get('numero_telephone')
        client_how_find = request.POST.get('client_how_find')

        event_date = request.POST.get('date_evenement')
        event_adresse = request.POST.get('adresse_evenement')
        event_ville = request.POST.get('ville_evenement')
        event_code_postal = request.POST.get('code_postal_evenement')

        image = request.POST.get('selectedImages')
        livraison = request.POST.get('livraison')
        heure_range = request.POST.get('heure_range')

        # # Création de l'objet Client
        # client = Client(
        #     nom=client_nom,
        #     prenom=client_prenom,
        #     mail=client_mail,
        #     numero_telephone=client_telephone,
        #     how_find=client_how_find
        # )
        # client.save()
        #
        # # Création de l'objet EventDetails
        # event_details = EventDetails(
        #     date_evenement=event_date,
        #     adresse_evenement=event_adresse,
        #     ville_evenement=event_ville,
        #     code_postal_evenement=event_code_postal
        # )
        # event_details.save()

        # event = Event(
        #     client=client,
        #     event_details = event_details,
        #     service_details =
        #     status = 'Initied',
        #     )

        return redirect('remerciement')  # Redirigez vers une URL de succès après la sauvegarde

    return render(request, 'app/confirmation.html')


def remerciement(request):
    return render(request, 'app/remerciement.html')

def info_lst_devis(request):
    all_event = Client.objects.all()
    return render(request, 'app/lst_devis.html', {'all_event': all_event,})
