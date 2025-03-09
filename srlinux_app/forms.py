from django import forms
from .models import Device

class DeviceForm(forms.ModelForm):
    class Meta:
        model = Device
        fields = ['name', 'ip_address', 'username', 'password']

    ip_address = forms.CharField(initial='172.20.20.100', widget=forms.HiddenInput())  # Default value set here