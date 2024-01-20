

from django.shortcuts import render, redirect

def demande_devis(request):

    return render(request, 'app/demande_devis.html' )
