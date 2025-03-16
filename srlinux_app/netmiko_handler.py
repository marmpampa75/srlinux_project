from netmiko import ConnectHandler

def get_device_interfaces(ip, username, password):
    device = {
        "device_type": "nokia_srl",
        "host": ip,
        "username": username,
        "password": password,
        "timeout": 60,  # connection timeout
    }

    try:
        # Connect to the device
        # Establish SSH connection
        connection = ConnectHandler(**device)
        # Increase the read_timeout after connection is established
        connection.read_timeout = 360  # Adjust as needed
        # Execute the command
        output = connection.send_command("show interface")
        # Close the connection
        connection.disconnect()
        return output

    except Exception as e:
        return f"Error connecting to device: {str(e)}"