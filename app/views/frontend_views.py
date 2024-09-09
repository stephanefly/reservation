from django.http import QueryDict
from django.shortcuts import render, redirect
from datetime import timedelta, datetime
from ..module.data_bdd.post_form import initialize_event, get_confirmation_data
from ..module.data_bdd.price import PRIX_PRODUITS
from ..module.trello.create_card import create_card

today_date = datetime.now().date()

def demande_devis(request):
    date_dans_deux_ans = today_date + timedelta(days=365 * 2)
    today_date_str = today_date.strftime("%Y-%m-%d")
    date_dans_deux_ans_str = date_dans_deux_ans.strftime("%Y-%m-%d")

    if request.method == 'POST':
        form_data = request.POST.dict()
        request.session['demande_devis_data'] = form_data
        return render(request, 'app/frontend/confirmation.html', {'form_data': form_data})

    form_data = request.session.get('demande_devis_data', {})
    initial_data = QueryDict(mutable=True)
    initial_data.update(form_data)

    return render(request, 'app/frontend/demande_devis.html', {
        'today_date': today_date_str,
        'date_dans_deux_ans': date_dans_deux_ans_str,
        'form': initial_data
    })

def confirmation(request):
    if request.method == 'POST':
        post_data = get_confirmation_data(request)
        event = initialize_event(post_data)
        id_card = create_card(post_data)
        event.id_card = id_card
        event.save()
        return redirect('remerciement')

    return render(request, 'app/frontend/confirmation.html')

def remerciement(request):
    return render(request, 'app/frontend/remerciement.html')

def tarifs(request):
    return render(request, 'app/frontend/tarifs.html', {'data_price': PRIX_PRODUITS})