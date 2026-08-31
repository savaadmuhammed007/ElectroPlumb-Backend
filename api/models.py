from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    ROLE_CHOICES = (
        ('electrician', 'Electrician'),
        ('plumber', 'Plumber'),
        ('general', 'General Worker'),
        ('admin', 'Admin'),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='electrician')
    phone = models.CharField(max_length=20, blank=True, null=True)
    whatsapp = models.CharField(max_length=20, blank=True, null=True)
    business_name = models.CharField(max_length=150, blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=100, blank=True, null=True)
    pin_code = models.CharField(max_length=20, blank=True, null=True)
    profile_photo = models.TextField(blank=True, null=True) # Base64 or URL
    about = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} Profile ({self.role})"


class Item(models.Model):
    ITEM_TYPE_CHOICES = (
        ('electrical', 'Electrical'),
        ('plumbing', 'Plumbing'),
    )

    STATUS_CHOICES = (
        ('active', 'Active'),
        ('disabled', 'Disabled'),
    )

    name = models.CharField(max_length=200)
    item_code = models.CharField(max_length=50, unique=True)
    item_type = models.CharField(max_length=20, choices=ITEM_TYPE_CHOICES)
    category = models.CharField(max_length=100)
    unit = models.CharField(max_length=50, default='Piece') # Meter, Piece, Box, etc.
    description = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['category', 'name']

    def __str__(self):
        return f"[{self.item_type.upper()}] {self.name} ({self.item_code})"


class MaterialList(models.Model):
    LIST_TYPE_CHOICES = (
        ('electrical', 'Electrical'),
        ('plumbing', 'Plumbing'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='material_lists')
    list_type = models.CharField(max_length=20, choices=LIST_TYPE_CHOICES)
    client_name = models.CharField(max_length=150)
    client_phone = models.CharField(max_length=30, blank=True, null=True)
    project_name = models.CharField(max_length=150, blank=True, null=True)
    location = models.CharField(max_length=200, blank=True, null=True)
    date = models.CharField(max_length=50, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"List #{self.id} - {self.client_name} ({self.list_type})"


class ListItem(models.Model):
    material_list = models.ForeignKey(MaterialList, on_delete=models.CASCADE, related_name='items')
    item = models.ForeignKey(Item, on_delete=models.SET_NULL, null=True, blank=True)
    item_name = models.CharField(max_length=200)
    category = models.CharField(max_length=100, blank=True, null=True)
    unit = models.CharField(max_length=50, default='Piece')
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.item_name} x {self.quantity} {self.unit}"
