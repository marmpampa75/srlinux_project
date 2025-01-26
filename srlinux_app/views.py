from django.shortcuts import render

from django.shortcuts import render, redirect
from .models import Device
from .forms import DeviceForm
from .netmiko_handler import get_device_interfaces

def device_list(request):
    devices = Device.objects.all()
    return render(request, 'device_list.html', {'devices': devices})

def add_device(request):
    if request.method == 'POST':
        form = DeviceForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('device_list')
    else:
        form = DeviceForm()
    return render(request, 'add_device.html', {'form': form})

def device_interfaces(request, device_id):
    device = Device.objects.get(id=device_id)
    interfaces = get_device_interfaces(device.ip_address, device.username, device.password)
    return render(request, 'device_interfaces.html', {'interfaces': interfaces, 'device': device})
