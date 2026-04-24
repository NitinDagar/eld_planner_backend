from django.urls import path
from . import views

urlpatterns = [
    path('trip/plan/', views.PlanTripView.as_view(), name='plan-trip'),
]
