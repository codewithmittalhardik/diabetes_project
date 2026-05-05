from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('severity-guide/', views.severity_guide, name='severity_guide'),
    path('tech-stack/', views.tech_stack, name='tech_stack'),
    path('food-checker/', views.food_checker, name='food_checker'),
    path('predict', views.predict, name='predict'),
    path('check-food', views.check_food, name='check_food'),
]
