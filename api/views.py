from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.generics import UpdateAPIView
from rest_framework import status
from rest_framework.decorators import api_view

from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.views import View
from django.db.models import Q
from .models import User, Passenger, Driver, Shipper, Order, Direction, Region, District
from .serializers import (
    UserSerializer, PassengerSerializer, DriverSerializer, 
    ShipperSerializer, OrderSerializer, DirectionSerializer, 
    RegionSerializer, DistrictSerializer
)

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    lookup_field = 'telegram_id'

    @action(detail=True, methods=['post'])
    def change_role(self, request, telegram_id=None):
        user = self.get_object()
        serializer = ChangeRoleSerializer(data=request.data)

        if serializer.is_valid():
            new_role = serializer.validated_data['role']
            user.change_role(new_role)

            return Response({"message": f"Role changed to {new_role} successfully!"}, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserDetailAPIView(APIView):
    def get(self, request, telegram_id, format=None):
        try:
            user = User.objects.get(telegram_id=telegram_id)
            serializer = UserSerializer(user)
            return Response(serializer.data)
        except User.DoesNotExist:
            return Response({"detail": "No User matches the given query."}, status=status.HTTP_404_NOT_FOUND)

class PassengerOrdersView(View):
    # GET request uchun view
    def get(self, request, user_id):
        try:
            # Passengerga tegishli buyurtmalarni olish
            orders = Order.objects.filter(passenger=user_id)

            # Buyurtmalarni kerakli formatda qaytarish (masalan, JSON formatida)
            orders_data = [{
                "id": order.id,
                "direction": order.direction,
                "pickup_location": order.pickup_location,
                "dropoff_location": order.dropoff_location,
                "departure_time": order.departure_time,
                "status": order.status
            } for order in orders]

            return JsonResponse({"orders": orders_data}, status=200)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)
        
# 1️⃣ API orqali foydalanuvchini yangilash (PUT yoki PATCH)
class UpdateUserView(UpdateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    lookup_field = "telegram_id"  # Foydalanuvchini telegram_id orqali topamiz

    def update(self, request, *args, **kwargs):
        user = get_object_or_404(User, telegram_id=kwargs["telegram_id"])
        serializer = self.get_serializer(user, data=request.data, partial=True)  # PATCH uchun partial=True

        if serializer.is_valid():
            serializer.save()
            return Response({"message": "✅ Foydalanuvchi ma'lumotlari yangilandi!", "user": serializer.data}, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UpdateUserRoleDataView(APIView):
    """
    Foydalanuvchining user_role ga qarab tegishli modeldagi ma'lumotlarini yangilash
    """

    def patch(self, request, telegram_id):
        user = get_object_or_404(User, telegram_id=telegram_id)  # Foydalanuvchini topamiz
        user_role = user.active_role  # User roli

        # Foydalanuvchi ma'lumotlarini yangilash
        user_serializer = UserSerializer(user, data=request.data, partial=True)
        if user_serializer.is_valid():
            user_serializer.save()
        else:
            return Response(user_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # **USER_ROLE ga qarab ma'lumotlarni yangilash**
        if user_role == "driver":
            driver = get_object_or_404(Driver, user=user)
            serializer = DriverSerializer(driver, data=request.data, partial=True)

        elif user_role == "passenger":
            passenger = get_object_or_404(Passenger, user=user)
            serializer = PassengerSerializer(passenger, data=request.data, partial=True)

        elif user_role == "shipper":
            shipper = get_object_or_404(Shipper, user=user)
            serializer = ShipperSerializer(shipper, data=request.data, partial=True)

        else:
            return Response({"error": "Noto‘g‘ri user_role!"}, status=status.HTTP_400_BAD_REQUEST)

        # **Agar serializer valid bo‘lsa, saqlaymiz**
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "✅ Ma'lumotlar yangilandi!", "data": serializer.data}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)






class PassengerViewSet(viewsets.ModelViewSet):
    queryset = Passenger.objects.all()
    serializer_class = PassengerSerializer

@api_view(["GET"])
def get_passenger_info(request, user_id):
    """ Passenger ma'lumotlarini olish """
    passenger = get_object_or_404(Passenger, user=user_id)
    
    serializer = PassengerSerializer(passenger)
    return Response(serializer.data)



class DriverViewSet(viewsets.ModelViewSet):
    queryset = Driver.objects.all()
    serializer_class = DriverSerializer

@api_view(["GET"])
def get_driver_info(request, user_id):
    """ Driver ma'lumotlarini olish """
    driver = get_object_or_404(Driver, user=user_id)

    serializer = DriverSerializer(driver)
    return Response(serializer.data)


class ShipperViewSet(viewsets.ModelViewSet):
    queryset = Shipper.objects.all()
    serializer_class = ShipperSerializer

@api_view(["GET"])
def get_shipper_info(request, user_id):
    """ shipper ma'lumotlarini olish """
    shipper = get_object_or_404(Shipper, user=user_id)
    
    serializer = ShipperSerializer(shipper)
    return Response(serializer.data)

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer

@api_view(['PATCH'])
def update_order(request, order_id):
    """ Buyurtma ma'lumotlarini yangilash """
    order = get_object_or_404(Order, id=order_id)

    serializer = OrderSerializer(order, data=request.data, partial=True)

    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(["GET"])
def get_user_orders(request, user_id):
    """ Foydalanuvchiga tegishli barcha buyurtmalarni olish """
    user = get_object_or_404(User, id=user_id)
    orders = Order.objects.filter(Q(passenger=user) | Q(shipper=user) | Q(driver=user))
    serializer = OrderSerializer(orders, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)


class OrderDetailAPIView(APIView):
    def get(self, request, order_id, format=None):
        try:
            # Buyurtma id orqali buyurtmani olish
            order = Order.objects.get(id=order_id)
            serializer = OrderSerializer(order)
            return Response(serializer.data)
        except Order.DoesNotExist:
            return Response({"detail": "No Order matches the given query."}, status=status.HTTP_404_NOT_FOUND)

class DirectionViewSet(viewsets.ModelViewSet):
    queryset = Direction.objects.all()
    serializer_class = DirectionSerializer

class RegionViewSet(viewsets.ModelViewSet):
    queryset = Region.objects.all()
    serializer_class = RegionSerializer

class DistrictViewSet(viewsets.ModelViewSet):
    queryset = District.objects.all()
    serializer_class = DistrictSerializer
