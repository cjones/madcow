from django.views.generic.simple import direct_to_template
from django.contrib.auth.decorators import login_required
from django.conf import settings
from gruntle.memebot.models import UserProfile, Link
from gruntle.memebot.forms import ManageProfileForm

@login_required
def index(request):
    return direct_to_template(request, 'memebot/index.html', {})


@login_required
def scores(request):
    profiles = UserProfile.objects.get_by_score()
    return direct_to_template(request, 'memebot/scores.html', {'profiles': profiles})


@login_required
def profile(request):
    if request.method == 'POST':
        form = ManageProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            request.user.message_set.create(message='Your profile has been updated')
    else:
        form = ManageProfileForm(instance=request.user)
    return direct_to_template(request, 'memebot/profile.html', {'form': form})


@login_required
def browse(request):
    try:
        page = int(request.GET.get('page'))
    except StandardError:
        page = 1
    try:
        per_page = int(request.GET.get('per_page'))
    except StandardError:
        per_page = settings.BROWSE_LINKS_PER_PAGE

    start = (page - 1) * per_page
    end = start + per_page
    links = Link.objects.all().order_by('-created')[start:end]
    return direct_to_template(request, 'memebot/browse.html', {'links': links})
