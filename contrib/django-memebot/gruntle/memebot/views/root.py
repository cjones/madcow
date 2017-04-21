"""View functions for root of site"""

import time

from django.shortcuts import render
from django.http import HttpResponse, Http404
from memebot.forms import AMPMTimeForm

def view_index(request):
    """Front page"""
    return render(request, 'index.html', {})


def view_robots(request):
    """View the site robots.txt file"""
    return render(request, 'robots.txt', mimetype='text/plain')


def friendly_404(request):
    """Raise 404 normally, uses 404.html template with site style"""
    raise Http404


def harsh_404(request):
    """Spartan 404 that reveaals notthing about the site, used when people are digging"""
    return HttpResponse('no.', 'text/plain', 404)


def view_calc(request):
    """MInecraft time calculator"""
    seconds = None
    if request.method == 'POST':
        form = AMPMTimeForm(request.POST)
        if form.is_valid():
            try:
                seconds = _convert_minecraft_time(form.cleaned_data['hour'],
                                                  form.cleaned_data['minute'],
                                                  form.cleaned_data['phase'])
            except:
                pass

    else:
        form = AMPMTimeForm()
    return render(request, 'calc.html', {'form': form, 'seconds': seconds})


def _convert_minecraft_time(h, m, p):
    ts = time.strptime('%02d:%02d %s' % (h, m, p), '%I:%M %p')
    h = ts.tm_hour - 6
    if h < 0:
        h += 24
    return h * 1000 + ts.tm_min * 1000 / 60
