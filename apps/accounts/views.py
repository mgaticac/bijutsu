from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.db import transaction
from .forms import RegistrationForm, ProfileForm
from .models import CustomerProfile

def register(request):
    if request.user.is_authenticated:
        return redirect('quotes:list')
    form = RegistrationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        with transaction.atomic():
            user = form.save()
            CustomerProfile.objects.create(user=user)
        login(request, user)
        return redirect('quotes:list')
    return render(request, 'registration/register.html', {'form': form})

@login_required
def profile(request):
    profile, _ = CustomerProfile.objects.get_or_create(user=request.user)
    form = ProfileForm(request.POST or None, instance=request.user, initial={'phone': profile.phone})
    if request.method == 'POST' and form.is_valid():
        form.save()
        profile.phone = form.cleaned_data['phone']
        profile.save()
        messages.success(request, 'Perfil actualizado.')
        return redirect('profile')
    return render(request, 'accounts/profile.html', {'form': form})
