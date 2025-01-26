from netmiko import ConnectHandler

def get_device_interfaces(host, username, password):
    device = {
        'device_type': 'nokia_srl',
        'host': host,
        'username': username,
        'password': password,
    }
    try:
        connection = ConnectHandler(**device)
        output = connection.send_command('show interfaces')
        connection.disconnect()
        return output
    except Exception as e:
        return f"Error: {str(e)}"