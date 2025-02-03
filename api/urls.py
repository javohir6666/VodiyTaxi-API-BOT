from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import update_order, get_driver_info, get_passenger_info, get_shipper_info,get_user_orders
from .views import (
    UserViewSet, PassengerViewSet, DriverViewSet, 
    ShipperViewSet, OrderViewSet, DirectionViewSet, 
    RegionViewSet, DistrictViewSet, UserDetailAPIView,
    PassengerOrdersView, UpdateUserView, UpdateUserRoleDataView, OrderDetailAPIView
)

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'passengers', PassengerViewSet)
router.register(r'drivers', DriverViewSet)
router.register(r'shippers', ShipperViewSet)
router.register(r'orders', OrderViewSet)
router.register(r'directions', DirectionViewSet)
router.register(r'regions', RegionViewSet)
router.register(r'districts', DistrictViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('user/<str:telegram_id>/', UserDetailAPIView.as_view(), name='user-detail'),
    path('user/<int:user_id>/orders/', get_user_orders, name='get_user_orders'),
    path('orders/passenger/<int:user_id>/', PassengerOrdersView.as_view(), name='passenger_orders'),
    path('order/<int:order_id>/', OrderDetailAPIView.as_view(), name="order_detail"),
    path('order/update/<int:order_id>/', update_order, name='update_order'),
    path("user/update/<int:telegram_id>/", UpdateUserView.as_view(), name="update_user"),
    path("user/update_role_data/<int:telegram_id>/", UpdateUserRoleDataView.as_view(), name="update_user_role_data"),
    path('driver/<int:user_id>/', get_driver_info, name="get_driver"),
    path('passenger/<int:user_id>/', get_passenger_info, name="get_passenger"),
    path('shipper/<int:user_id>/', get_shipper_info, name="get_shipper"),


]
