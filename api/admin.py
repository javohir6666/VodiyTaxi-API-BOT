from django.contrib import admin
from .models import User, Driver, Passenger, Shipper, Direction, District, Order, Region

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('telegram_id', 'telegram_username', 'telegram_fullname', 'phone_number', 'last_activity', 'created_at', 'is_registered', 'is_admin', 'user_role')
    search_fields = ('telegram_id', 'telegram_username', 'telegram_fullname', 'phone_number')
    list_filter = ('is_registered', 'is_admin', 'active_role')

@admin.register(Passenger)
class PassengerAdmin(admin.ModelAdmin):
    list_display = ('user', 'passenger_count')
    search_fields = ('user__telegram_fullname', 'user__telegram_id')
    list_filter = ('passenger_count',)

@admin.register(Driver)
class DriverAdmin(admin.ModelAdmin):
    list_display = ('user', 'status', 'car_name', 'car_number', 'seats_available', 'current_direction', 'current_region', 'dropoff_location', 'rating')
    search_fields = ('user__telegram_fullname', 'user__telegram_id', 'car_name', 'car_number')
    list_filter = ('status', 'seats_available', 'rating')

@admin.register(Shipper)
class ShipperAdmin(admin.ModelAdmin):
    list_display = ('user', 'origin_location', 'destination')
    search_fields = ('user__telegram_fullname', 'user__telegram_id', 'origin_location', 'destination')

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'order_type','driver', 'created_at', 'status', 'direction', 'pickup_location', 'dropoff_location', 'price')
    search_fields = ('passenger__telegram_fullname', 'driver__telegram_fullname', 'direction', 'pickup_location', 'dropoff_location')
    list_filter = ('status', 'order_type', 'created_at',  'price')

@admin.register(Direction)
class DirectionAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
    search_fields = ('name',)
    list_filter = ('created_at',)

@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ('name', 'direction', 'created_at')
    search_fields = ('name', 'direction__name')
    list_filter = ('created_at', 'direction')

@admin.register(District)
class DistrictAdmin(admin.ModelAdmin):
    list_display = ('name', 'region', 'created_at')
    search_fields = ('name', 'region__name')
    list_filter = ('created_at', 'region')