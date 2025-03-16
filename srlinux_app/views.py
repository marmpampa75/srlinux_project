from django.shortcuts import render
from django.shortcuts import redirect
from django.shortcuts import get_object_or_404
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
import time


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


def get_container_ip(device_name):
    """Fetch the IP address of the container using docker inspect."""
    try:
        # Ensure the device name includes the prefix
        if not device_name.startswith("clab-srlceos01-"):
            device_name = "clab-srlceos01-" + device_name

        result = subprocess.run(
            ["docker", "inspect", device_name], capture_output=True, text=True
        )
        
        if result.returncode == 0:
            # Print the raw docker inspect output for debugging
            print(f"docker inspect output for {device_name}:\n{result.stdout}")

            # Parse the JSON output
            container_info = json.loads(result.stdout)
            ip_address = container_info[0]["NetworkSettings"]["Networks"]["clab"].get("IPAddress", None)
            
            if ip_address:
                return ip_address
            else:
                print(f"No IP address found for {device_name}")
        else:
            print(f"Error with docker inspect for {device_name}: {result.stderr}")
    except Exception as e:
        print(f"Error fetching IP for {device_name}: {e}")
    return None


def device_list(request):
    devices = Device.objects.all()

    # Update IP addresses before rendering
    for device in devices:
        ip = get_container_ip(device.name)
        if ip:
            device.ip_address = ip  # Update the object
            device.save()  # Save updated IP in the database

    return render(request, 'device_list.html', {'devices': devices})

#def device_list(request):
    #devices = Device.objects.all()
    # Run "docker ps -a" command
    #try:
    #    print(f"cd clab-quickstart/")  # Debugging
    #    os.chdir('/root/clab-quickstart')  # Change directory
    #    print(f"docker ps -a")  # Debugging
    #    docker_output = subprocess.check_output(["docker", "ps", "-a"], text=True)
    #except subprocess.CalledProcessError as e:
    #    docker_output = f"Error executing command: {e}"
    #return render(request, 'device_list.html', {'devices': devices})

def modify_clab_file(delete, node_name, kind, image):
    """
    Adds or deletes a node and its links dynamically to the Containerlab YAML file.

    :param node_name: Name of the new node (e.g., "srl3")
    :param kind: Node type (e.g., "nokia_srlinux")
    :param image: Docker image for the node
    :param delete: Boolean flag to indicate if the node should be deleted
    """
    try:
        clab_file_path = "/root/clab-quickstart/srlceos01.clab.yml"

        # Load existing YAML data
        with open(clab_file_path, "r") as file:
            data = yaml.safe_load(file) or {}

        # Ensure 'topology' and its subkeys exist
        data.setdefault("topology", {})
        data["topology"].setdefault("nodes", {})
        data["topology"].setdefault("links", [])

        if delete:
            if node_name in data["topology"]["nodes"]:
                del data["topology"]["nodes"][node_name]
                print(f"Deleted node: {node_name}")

                # Remove any links referencing the deleted node
                new_links = []
                for link in data["topology"]["links"]:
                    if not any(node_name in endpoint for endpoint in link["endpoints"]):
                        new_links.append(link)

                data["topology"]["links"] = new_links  # Update links list
                print(f"Removed links associated with {node_name}")

            else:
                print(f"Node '{node_name}' not found. No changes made.")
        else:
            # Add the new node if not already present
            if node_name not in data["topology"]["nodes"]:
                data["topology"]["nodes"][node_name] = {
                    "kind": kind,
                    "image": image
                }
                print(f"Added node: {node_name}")

        # Save the modified YAML file
        with open(clab_file_path, "w") as file:
            yaml.dump(data, file, default_flow_style=False)

        print(f"Updated '{clab_file_path}' successfully!")

    except Exception as e:
        print(f"Error modifying the YAML file: {e}")

    # Display the modified YAML file contents
    print("\nUpdated YAML File Content:\n" + "-" * 50)
    with open(clab_file_path, "r") as file:
        print(file.read())  # Print the YAML file content

def add_device(request):
    if request.method == "POST":
        form = DeviceForm(request.POST)
        if form.is_valid():
            form.save()  # Save the device to the database of admin page
            device_name = form.cleaned_data["name"]  # Get the name from the form
            stop_containerlab()
            modify_clab_file(
                delete=False,
                node_name=device_name,  # Use the user-provided name
                kind="nokia_srlinux",
                image="ghcr.io/nokia/srlinux:24.3.3"
            )
            run_containerlab()
            time.sleep(5)
            return redirect('device_list')  # Redirect to device_list 
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
            # Ensure the device name includes the prefix
            if not device.name.startswith("clab-srlceos01-"):
                device_name = "clab-srlceos01-" + device.name
            else:
                device_name = device.name

            # Run 'docker inspect' to get uptime for the container
            output = subprocess.check_output(
                ["docker", "inspect", "-f", "{{.State.StartedAt}}", device_name],
                text=True
            ).strip()

            # Convert timestamp to seconds 
            # Example: "2024-02-17T12:34:56.123456789Z" (take the first 19 characters)
            started_at = datetime.strptime(output[:19], "%Y-%m-%dT%H:%M:%S")
            #[current UTC time]-[start time] 
            uptime_seconds = (datetime.utcnow() - started_at).total_seconds()

            # Store in dictionary
            uptime_data[device.name] = int(uptime_seconds)
        
        except subprocess.CalledProcessError:
            uptime_data[device.name] = 0  # If the device is not running, uptime is 0

    return JsonResponse(uptime_data)  # Return uptime data as a JSON response

def confirm_delete(request, device_id):
    # Check if the request method is POST (to confirm deletion)
    if request.method == 'POST':
        # Get the device to delete using the device_id passed in the URL
        device = get_object_or_404(Device, id=device_id)
        device_name = device.name

        # Delete the device
        device.delete()
        stop_containerlab()
        modify_clab_file(
            delete=True,
            node_name=device_name,
            kind="nokia_srlinux",
            image="ghcr.io/nokia/srlinux:24.3.3"
        )
        run_containerlab()
        time.sleep(5)

        # Redirect to the device list page after deletion
        return redirect('device_list')  # or whichever URL you want

    # If the request is not POST (e.g., GET), redirect to the device list page or show an error
    return redirect('device_list')

# Show the delete device page with the list of devices
def delete_device(request):
    devices = Device.objects.all()
    return render(request, 'delete_device.html', {'devices': devices})