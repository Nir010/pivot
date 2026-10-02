from django import forms

class ContactForm(forms.Form):
    name = forms.CharField(max_length=100)
    email = forms.EmailField(max_length=254)
    organization = forms.CharField(max_length=150, required=False)
    message = forms.CharField(required=True)