"""
urls.py — URL Routing for Planner App
=======================================
Maps URL patterns to view functions.

URL STRUCTURE:
  /           → home_view      (main form)
  /predict/   → predict_view   (process form)
  /result/    → result_view    (show result)
  /history/   → history_view   (past plans)
  /download/  → download_csv   (export CSV)
  /login/     → login_view     (login)
  /register/  → register_view  (register)
  /logout/    → logout_view    (logout)
  /api/chart/ → chart_data_api (chart JSON)
"""

from django.urls import path
from . import views

urlpatterns = [
    # Main pages
    path('', views.home_view, name='home'),
    path('predict/', views.predict_view, name='predict'),
    path('result/', views.result_view, name='result'),
    path('history/', views.history_view, name='history'),
    
    # Download
    path('download/', views.download_csv, name='download_csv'),
    
    # Auth pages
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    
    # API
    path('api/chart/', views.chart_data_api, name='chart_data'),
]
