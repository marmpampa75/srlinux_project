from django.contrib import admin
from .models import Device

@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ("name", "ip_address")  # Display name and IP in admin list view
    readonly_fields = ("ip_address",)  # Prevent manual changes to IP field

    def save_model(self, request, obj, form, change):
        """Ensure the IP is fetched before saving."""
        obj.ip_address = obj.get_container_ip() or obj.ip_address
        super().save_model(request, obj, form, change)
