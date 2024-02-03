from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_protect
from datetime import datetime, timedelta
from django.http import QueryDict
from .models import Client, Event
from threading import Thread

from .module.post_form import initialize_event


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
        thread = Thread(target=initialize_event, args=(post_data,))
        thread.start()

        return redirect('remerciement')  # Redirigez vers une URL de succès après la sauvegarde

    return render(request, 'app/confirmation.html')


def remerciement(request):
    return render(request, 'app/remerciement.html')

def info_lst_devis(request):
    all_event = Event.objects.all()
    return render(request, 'app/lst_devis.html', {'all_event': all_event,})
