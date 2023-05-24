from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.db import transaction
from django.forms.utils import ValidationError

from .models import User,Customer


class VendorSignUpForm(UserCreationForm):
    email = forms.EmailField(help_text="A valid email address.")
    class Meta(UserCreationForm.Meta):
        model = User

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_vendor = True
        user.email = self.cleaned_data.get('email')
        if commit:
            user.save()
        return user

class CustomerSignUpForm(UserCreationForm):
    name = forms.CharField(initial="Your name")
    email = forms.EmailField(help_text="A valid email address.")

    class Meta(UserCreationForm.Meta):
        model = User

    @transaction.atomic
    def save(self):
        user = super().save(commit=False)
        user.is_customer = True
        user.save()
        customer = Customer.objects.create(user=user)
        customer.name = self.cleaned_data.get('name')
        customer.email = self.cleaned_data.get('email')
        customer.save()
        return user




