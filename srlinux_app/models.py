import subprocess
from django.db import models

class Device(models.Model):
    name = models.CharField(max_length=100, unique=True)  # Device name
    ip_address = models.GenericIPAddressField(blank=True, null=True)  # IP address
    username = models.CharField(max_length=100)
    password = models.CharField(max_length=100)

    def get_container_ip(self):
        """Fetch the IP address of the container using docker inspect."""
        try:
            result = subprocess.run(
                ["docker", "inspect", self.name], capture_output=True, text=True
            )
            if result.returncode == 0:
                for line in result.stdout.splitlines():
                    if "IPAddress" in line:
                        return line.split(":")[-1].strip().strip('"', ',')
        except Exception as e:
            print(f"Error fetching IP for {self.name}: {e}")
        return None

    def save(self, *args, **kwargs):
        """Override save method to get the container's IP before saving."""
        self.ip_address = self.get_container_ip() or self.ip_address  # Keep existing IP if not found
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.ip_address})"