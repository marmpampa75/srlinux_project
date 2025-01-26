from django.db import models

class Device(models.Model):
    name = models.CharField(max_length=255)
    ip_address = models.GenericIPAddressField()
    username = models.CharField(max_length=100)
    password = models.CharField(max_length=100)

    def __str__(self):
        return self.name
