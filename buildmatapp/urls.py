from django.urls import path
from . import views

app_name = 'buildmatapp'

urlpatterns = [
    path('', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('products/', views.product_list_view, name='product_list'),
    path('products/<int:product_id>/', views.product_detail_view, name='product_detail'),
    path('products/create/', views.product_create_view, name='product_create'),
    path('products/<int:product_id>/edit/', views.product_edit_view, name='product_edit'),
    path('products/<int:product_id>/delete/', views.product_delete_view, name='product_delete'),
    path('orders/', views.order_list_view, name='order_list'),
    path('orders/create/', views.order_create_view, name='order_create'),
    path('orders/<int:order_id>/edit/', views.order_edit_view, name='order_edit'),
    path('orders/<int:order_id>/delete/', views.order_delete_view, name='order_delete'),
    path('calculate/', views.material_calculation_view, name='calculate'),
]
