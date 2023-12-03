# votreactivite/views.py

from django.shortcuts import render, redirect
from .forms import DevisForm

def demande_devis(request):
    if request.method == 'POST':
        form = DevisForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('demande_devis')  # Utilisez 'demande_devis' ici
    else:
        form = DevisForm()
    return render(request, 'app/demande_devis.html', {'form': form})
