"""Memebot forms"""

from django import forms
from django.contrib.auth.models import User
from django.db.models import Q
from gruntle.memebot.models import Link

class EditProfileForm(forms.ModelForm):

    """Form for updating your user profile"""

    password_opts = {'min_length': 3, 'max_length': 128, 'widget': forms.PasswordInput, 'required': False}

    password1 = forms.CharField(label='New Password', **password_opts)
    password2 = forms.CharField(label='Confirm Password', **password_opts)

    class Meta:

        model = User
        fields = 'email', 'first_name', 'last_name'

    def clean_password2(self):
        """Verify password matches"""
        if self.cleaned_data['password1'] != self.cleaned_data['password2']:
            raise forms.ValidationError("Doesn't match password")
        return self.cleaned_data['password2']

    def save(self, *args, **kwargs):
        """Save user instance, updated with cleaned_data"""
        commit = kwargs.pop('commit', True)
        kwargs['commit'] = False
        user = super(EditProfileForm, self).save(*args, **kwargs)
        if self.cleaned_data['password2']:
            user.set_password(self.cleaned_data['password2'])
        if commit:
            user.save()
        return user


class CheckLinkForm(forms.Form):

    url = forms.URLField(label='URL', min_length=11, max_length=128, required=True,
                         widget=forms.TextInput(attrs={'size': 128}))

    def clean_url(self):
        errors = []
        url = self.cleaned_data.get('url', None)
        self.cleaned_data['link'] = None
        if url is None:
            errors.append('You must enter the URL to check')
        else:
            normalized = Link.objects.normalize_url(url)
            links = Link.objects.filter(state='published')
            links = links.filter(Q(url=url) | Q(resolved_url=url) | Q(normalized=normalized)).distinct()
            links = links.order_by('published')
            if links.count():
                self.cleaned_data['link'] = links[0]
            else:
                errors.append('No results found for that URL')
        if errors:
            raise forms.ValidationError(errors)
        return self.cleaned_data['url']
