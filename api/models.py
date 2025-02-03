from django.db import models
from django.db import transaction


class User(models.Model):
    USER_TYPE_CHOICES = [
        ('passenger', 'Passenger'),
        ('driver', 'Driver'),
        ('shipper', 'Shipper')
    ]
    
    telegram_id = models.BigIntegerField(unique=True)
    telegram_username = models.CharField(max_length=100, null=True, blank=True)
    telegram_fullname = models.CharField(max_length=100, null=True, blank=True)
    phone_number = models.CharField(max_length=20, null=True, blank=True)
    last_activity = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_registered = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)

    active_role = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, default="passenger")

    def change_role(self, new_role):
        """Foydalanuvchi aktiv rolini o‘zgartirib, mos modelga saqlaydi."""
        if new_role not in dict(self.USER_TYPE_CHOICES):
            raise ValueError("Invalid role")

        with transaction.atomic():  # Atomic transaction bilan xavfsiz saqlash
            # Avval eski roli bo‘yicha tegishli modelni o‘chirib tashlaymiz
            if self.active_role == 'driver':
                Driver.objects.filter(user=self).delete()
            elif self.active_role == 'passenger':
                Passenger.objects.filter(user=self).delete()
            elif self.active_role == 'shipper':
                Shipper.objects.filter(user=self).delete()

            # Yangi roli bo‘yicha yangi model yaratamiz
            if new_role == 'driver':
                Driver.objects.create(user=self, car_name="Unknown", car_number="Unknown")
            elif new_role == 'passenger':
                Passenger.objects.create(user=self)
            elif new_role == 'shipper':
                Shipper.objects.create(user=self, origin_location="Unknown", destination="Unknown")

            # Foydalanuvchi rolini yangilab saqlaymiz
            self.active_role = new_role
            self.save()

    @property
    def user_role(self):
        """User modelidagi aktiv rolni qaytaradi"""
        return self.active_role

    def __str__(self):
        return f"{self.telegram_fullname} - {self.active_role}"

    def save(self, *args, **kwargs):
        """Foydalanuvchi yaratishda ro'lni tekshirib to'g'ri saqlash"""
        if self.active_role not in dict(self.USER_TYPE_CHOICES):
            raise ValueError("Invalid role")
        super().save(*args, **kwargs)


class Passenger(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='passenger_data')
    passenger_count = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"Passenger: {self.user.telegram_fullname}"

class Driver(models.Model):
    STATUS_CHOICES = [
        ('not_busy', 'Not Busy'),
        ('busy', 'Busy')
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='driver_data')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='not_busy')
    car_name = models.CharField(max_length=255)
    car_number = models.CharField(max_length=50)
    seats_available = models.PositiveIntegerField(default=4)
    current_direction = models.CharField(max_length=255, null=True, blank=True)
    current_region = models.CharField(max_length=255, null=True, blank=True)
    dropoff_location = models.CharField(max_length=255, null=True, blank=True)
    rating = models.FloatField(default=5.0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Driver: {self.user.telegram_fullname} ({self.car_name})"

class Shipper(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='shipper_data')
    message_text = models.TextField(null=True, blank=True)
    origin_location = models.CharField(max_length=255)
    destination = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"Shipper: {self.user.telegram_fullname}"
    
ORDER_TYPE = [
        ('shipper', 'Yuk yuboruvchi'),
        ('passenger', 'Yo\'lovchi')
    ]


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ]

    order_type = models.CharField(max_length=10, choices=ORDER_TYPE, default='passenger')
    passenger = models.ForeignKey(User, on_delete=models.CASCADE, related_name='passenger_orders', blank=True, null=True)
    shipper = models.ForeignKey(User, on_delete=models.CASCADE, related_name='shipper_orders', blank=True, null=True)
    driver = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='driver_orders')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    direction = models.CharField(max_length=255)
    pickup_location = models.CharField(max_length=255)
    dropoff_location = models.CharField(max_length=255)
    departure_time = models.CharField(max_length=255, null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    passenger_count = models.PositiveIntegerField(default=1)
    rejected_users = models.TextField(null=True, blank=True)

def __str__(self):
    try:
        return f"Order {self.id}: {self.passenger.user.telegram_fullname} -> {self.dropoff_location}"
    except AttributeError:
        return f"Order {self.id}: No Passenger -> {self.dropoff_location}"


class Direction(models.Model):
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return self.name
    

class Region(models.Model):
    direction = models.ForeignKey(Direction, on_delete=models.CASCADE, related_name='regions')
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
    
class District(models.Model):
    region = models.ForeignKey(Region, on_delete=models.CASCADE, related_name='districts')
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name