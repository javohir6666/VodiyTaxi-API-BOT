from rest_framework import serializers
from .models import User, Passenger, Driver, Shipper, Order, Direction, Region, District

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'


    def create(self, validated_data):
        active_role = validated_data.get('active_role', 'passenger')  # default role is 'passenger'

        # Yangi foydalanuvchi yaratish
        user = User.objects.create(**validated_data)

        # Foydalanuvchi ro'lini faqat tanlangan rolga asoslab o'zgartirish
        user.change_role(active_role)

        return user
    
    
class ChangeRoleSerializer(serializers.Serializer):
    role = serializers.ChoiceField(choices=['passenger', 'driver', 'shipper'])


class PassengerSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Passenger
        fields = '__all__'

class DriverSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Driver
        fields = '__all__'

class ShipperSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Shipper
        fields = '__all__'

class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = '__all__'

class DirectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Direction
        fields = '__all__'

class RegionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Region
        fields = '__all__'

class DistrictSerializer(serializers.ModelSerializer):
    class Meta:
        model = District
        fields = '__all__'
