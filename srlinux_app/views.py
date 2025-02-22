from django.shortcuts import render
from django.shortcuts import redirect
from .models import Device
from .forms import DeviceForm
from .netmiko_handler import get_device_interfaces
from django.contrib.auth import authenticate, login
from django.contrib.auth import logout
import os
import subprocess

def run_containerlab():
    try:
        print(f"cd clab-quickstart/")  # Debugging
        os.chdir('/root/clab-quickstart')  # Change directory
        print(f"sudo containerlab deploy")  # Debugging
        subprocess.run(['sudo', 'containerlab', 'deploy'], check=True)
    except Exception as e:
        print(f"Error running containerlab: {e}")

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
    print(f"Connecting to: {device.ip_address}")  # Debugging

    interfaces = get_device_interfaces(device.ip_address, device.username, device.password)
    return render(request, 'device_interfaces.html', {'interfaces': interfaces, 'device': device})

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            # Run containerlab after successful login
            run_containerlab()
            return redirect('device_list')  # Redirect to the device list after login
        else:
            return render(request, 'login.html', {'error': 'Invalid credentials'})

    return render(request, 'login.html')

def logout_confirmation(request):
    return render(request, 'logout_confirmation.html')

def logout_confirmed(request):
    try:
        print(f"cd clab-quickstart/")  # Debugging
        os.chdir('/root/clab-quickstart')  # Change directory
        print(f"sudo containerlab destroy")  # Debugging
        subprocess.run(["sudo", "containerlab", "destroy"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error destroying container lab: {e}")

    # Log out the user
    logout(request)
    return redirect('login')  # Redirect the user to the login page after logging out

