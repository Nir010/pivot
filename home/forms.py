from django import forms

class ContactForm(forms.Form):
    name = forms.CharField(max_length=100)
    email = forms.EmailField(max_length=254)
    organization = forms.CharField(max_length=150, required=False)
    message = forms.CharField(required=True, max_length=5000)
    # Honeypot: hidden from people, tempting to bots. Humans leave it empty.
    website = forms.CharField(required=False)

    def clean_website(self):
        if self.cleaned_data.get("website"):
            raise forms.ValidationError("Spam detected.")
        return ""