from django.urls import path
from . import views

app_name = 'buildmatapp'

urlpatterns = [
    path('', views.login_view, name='login'),
]
