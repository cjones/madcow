"""Memebot forms"""

from django import forms
from django.contrib.auth.models import User

class ManageProfileForm(forms.ModelForm):

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
        commit = kwargs.pop('commit', True)
        kwargs['commit'] = False
        user = super(ManageProfileForm, self).save(*args, **kwargs)
        if self.cleaned_data['password2']:
            user.set_password(self.cleaned_data['password2'])
        if commit:
            user.save()
        return user
