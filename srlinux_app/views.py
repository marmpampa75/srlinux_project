from django.shortcuts import render
from django.shortcuts import redirect
from .models import Device
from .forms import DeviceForm
from .netmiko_handler import get_device_interfaces
from django.contrib.auth import authenticate, login
from django.contrib.auth import logout
import os
import subprocess
import json
from django.http import JsonResponse
from datetime import datetime
import yaml

def run_containerlab():
    try:
        print(f"cd clab-quickstart/")  # Debugging
        os.chdir('/root/clab-quickstart')  # Change directory
        print(f"sudo containerlab deploy")  # Debugging
        subprocess.run(['sudo', 'containerlab', 'deploy'], check=True)
    except Exception as e:
        print(f"Error running containerlab: {e}")

def stop_containerlab():
    try:
        print(f"cd clab-quickstart/")  # Debugging
        os.chdir('/root/clab-quickstart')  # Change directory
        print(f"sudo containerlab destroy")  # Debugging
        subprocess.run(["sudo", "containerlab", "destroy"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error destroying container lab: {e}")

def device_list(request):
    devices = Device.objects.all()
    # Run "docker ps -a" command
    #try:
    #    print(f"cd clab-quickstart/")  # Debugging
    #    os.chdir('/root/clab-quickstart')  # Change directory
    #    print(f"docker ps -a")  # Debugging
    #    docker_output = subprocess.check_output(["docker", "ps", "-a"], text=True)
    #except subprocess.CalledProcessError as e:
    #    docker_output = f"Error executing command: {e}"
    return render(request, 'device_list.html', {'devices': devices})

###___________________NOT COMPLETED_________________________
def modify_clab_file(node_name, kind, image, endpoint):
    try:
        # Change directory to where the clab file is located
        print(f"cd clab-quickstart/")
        os.chdir('/root/clab-quickstart')
        # Open and load the YAML file
        clab_file_path = "srlceos01.clab.yml"
        with open(clab_file_path, "r") as file:
            data = yaml.safe_load(file)  # Load the YAML data into a Python dictionary
        # Dynamically add the node to the nodes section
        if "nodes" not in data:
            data["nodes"] = {}
        # Add the dynamic node
        data["nodes"][node_name] = {
            "kind": kind,
            "image": image
        }
        # Dynamically modify the links section
        if "links" not in data:
            data["links"] = []
        # Add the new endpoint to all links
        for link in data["links"]:
            if "endpoints" in link:
                link["endpoints"].append(f"{node_name}:{endpoint}")
        # Save the modified YAML file
        with open(clab_file_path, "w") as file:
            yaml.dump(data, file)  # Write the modified data back to the file
        print(f"YML file '{clab_file_path}' modified successfully with node '{node_name}'.")
    except Exception as e:
        print(f"An error occurred: {e}")

def add_device(request):
    if request.method == "POST":
        form = DeviceForm(request.POST)
        if form.is_valid():
            device = form.save()
            stop_containerlab()
            modify_clab_file(device.name, "nokia_srlinux", "ghcr.io/nokia/srlinux:24.3.3", "e1-1")
            run_containerlab()
            return redirect('device_list')  # Redirect to the list page
    else:
        form = DeviceForm()
    
    return render(request, 'add_device.html', {'form': form})

def device_interfaces(request, device_id):
    device = Device.objects.get(id=device_id)   # Fetch the device object from the database using device_id
    print(f"Connecting to: {device.ip_address}")  # Debugging
    # (via netmiko_handler) connects to the device and stotes output in variable
    interfaces = get_device_interfaces(device.ip_address, device.username, device.password)
    return render(request, 'device_interfaces.html', {'interfaces': interfaces, 'device': device})

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        #login for users that are in database 
        if user is not None:
            login(request, user)
            # Run containerlab after successful login
            run_containerlab()
            return redirect('device_list')  # Redirect to the device list after login
        #if the credentials are wrong 'Invalid credentials' message displayed and containerlab does not run
        else:
            return render(request, 'login.html', {'error': 'Invalid credentials'})

    return render(request, 'login.html')

def logout_confirmation(request):
    return render(request, 'logout_confirmation.html') 

def logout_confirmed(request):
    #when logout stop containerlab
    stop_containerlab()
    # Log out the user
    logout(request)
    return redirect('login')  # Redirect the user to the login page 

def get_device_uptime(request):
    devices = Device.objects.all()  # Fetch all devices from the database
    uptime_data = {}

    for device in devices:
        try:
            # Run 'docker inspect' to get uptime for the container
            output = subprocess.check_output(
                ["docker", "inspect", "-f", "{{.State.StartedAt}}", device.name],
                text=True
            ).strip()

            # Convert timestamp to seconds 
            #Example: "2024-02-17T12:34:56.123456789Z" (take the first 19 characters)
            started_at = datetime.strptime(output[:19], "%Y-%m-%dT%H:%M:%S")
            #[current UTC time]-[start time] 
            uptime_seconds = (datetime.utcnow() - started_at).total_seconds()

            #Store in dictionary
            uptime_data[device.name] = int(uptime_seconds)
        
        except subprocess.CalledProcessError:
            uptime_data[device.name] = 0  # If the device is not running, uptime is 0

    return JsonResponse(uptime_data)    # Return uptime data as a JSON response