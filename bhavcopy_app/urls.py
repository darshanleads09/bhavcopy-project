from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),  # Add this line for the root URL
    path('data/', views.get_data, name='get_data'),
    path('reload/<str:date>/', views.reload_date, name='reload_date'),
    path('mcx/', views.mcx_page, name='mcx_page'),
    path('data/mcx/', views.get_data_mcx, name='get_data_mcx'),
    path('reload/mcx/<str:date>/', views.reload_date_mcx, name='reload_date_mcx'),
]

