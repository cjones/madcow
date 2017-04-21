"""Accounts management views"""

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import Http404
from memebot.forms import EditProfileForm

@login_required
def edit_profile(request):
    """Update user profile"""
    if request.method == 'POST':
        form = EditProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            request.user.message_set.create(message='Your profile has been updated')
    else:
        form = EditProfileForm(instance=request.user)
    return render(request, 'memebot/profile.html', {'form': form})


@login_required
def view_profile(request):
    raise Http404
