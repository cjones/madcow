"""View functions for root of site"""

import time

from django.views.generic.simple import direct_to_template
from django.http import HttpResponse, Http404
from gruntle.memebot.forms import AMPMTimeForm

def view_index(request):
    """Front page"""
    return direct_to_template(request, 'root/index.html', {})


def view_robots(request):
    """View the site robots.txt file"""
    return direct_to_template(request, 'root/robots.txt', mimetype='text/plain')


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
    return direct_to_template(request, 'root/calc.html', {'form': form, 'seconds': seconds})


def _convert_minecraft_time(h, m, p):
    ts = time.strptime('%02d:%02d %s' % (h, m, p), '%I:%M %p')
    h = ts.tm_hour - 6
    if h < 0:
        h += 24
    return h * 1000 + ts.tm_min * 1000 / 60
