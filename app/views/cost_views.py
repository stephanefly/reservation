from django.shortcuts import render, redirect, get_object_or_404
from ..forms import CostForm
from ..models import Cost

def lst_cost(request):
    all_cost = Cost.objects.all().order_by('-created_at')
    return render(request, 'app/backend/lst_cost.html', {'all_cost': all_cost})

def create_cost(request):
    if request.method == 'POST':
        form = CostForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('lst_cost')
    else:
        form = CostForm()
    return render(request, 'app/backend/create_cost.html', {'form': form})

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
