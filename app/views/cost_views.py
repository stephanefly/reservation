from django.shortcuts import render, redirect, get_object_or_404
from ..forms import CostForm
from ..models import Cost, NameCost


def lst_cost(request):
    all_cost = Cost.objects.all().order_by('-created_at')[:20]
    return render(request, 'app/backend/lst_cost.html', {'all_cost': all_cost})


def info_cost(request, id):
    cost = get_object_or_404(Cost, pk=id)
    form = CostForm(instance=cost)
    return render(request, 'app/backend/info_cost.html', {'cost': cost, 'form': form, 'id': id})


def edit_cost(request, id):
    cost = get_object_or_404(Cost, pk=id)
    form = CostForm(request.POST, instance=cost)
    if form.is_valid():
        form.save()
        return redirect('lst_cost')


def delete_cost(request, id):
    cost = get_object_or_404(Cost, pk=id)
    cost.delete()
    return redirect('lst_cost')


def create_cost(request):
    name_costs = NameCost.objects.all().order_by('name')  # Pour peupler la liste déroulante
    if request.method == 'POST':
        form = CostForm(request.POST)
        if form.is_valid():
            # Vérifiez si un nouveau NameCost a été saisi
            new_name_cost = request.POST.get('new_name_cost')
            if new_name_cost:  # Si un nouveau nom est fourni
                name_cost, created = NameCost.objects.get_or_create(name=new_name_cost)
            else:  # Sinon, utilisez le NameCost sélectionné
                name_cost_id = request.POST.get('name_cost')
                name_cost = NameCost.objects.get(id=name_cost_id)

            # Enregistrez l'objet Cost
            cost = form.save(commit=False)
            cost.name_cost = name_cost
            cost.save()
            return redirect('lst_cost')  # Redirection après ajout
    else:
        form = CostForm()

    return render(request, 'app/backend/create_cost.html', {'form': form, 'name_costs': name_costs})