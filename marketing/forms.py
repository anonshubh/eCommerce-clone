from django import forms
from .models import MarketingPreference

class MarketingPreferenceForm(forms.ModelForm):
    subscribed = forms.BooleanField(label='Receive Email From Us?',required=False)
    class Meta():
        model = MarketingPreference
        fields = ['subscribed']