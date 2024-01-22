from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_protect
from .forms import EventForm
from datetime import datetime, timedelta


def demande_devis(request):
    today_date = datetime.now().date()
    date_dans_deux_ans = today_date + timedelta(days=365 * 2)
    today_date_str = today_date.strftime("%Y-%m-%d")
    date_dans_deux_ans_str = date_dans_deux_ans.strftime("%Y-%m-%d")

    if request.method == 'POST':
        form = EventForm(request.POST)
        if form.is_valid():
            form.save()  # Enregistrez le formulaire en base de données
            return redirect('remerciement')        # Redirigez l'utilisateur vers une page de confirmation
        else:
            errors = form.errors
            print(errors)
    else:
        form = EventForm()

    return render(request, 'app/demande_devis.html', {
        'form': form,
        'today_date': today_date_str,
        'date_dans_deux_ans': date_dans_deux_ans_str,
    })


def remerciement(request):
    return render(request, 'app/remerciement.html')