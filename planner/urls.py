from django.urls import path
from . import views
urlpatterns=[
 path('',views.home_view,name='home'),path('predict/',views.predict_view,name='predict'),
 path('result/',views.result_view,name='result'),path('plans/<int:pk>/',views.plan_detail,name='plan_detail'),
 path('blocks/<int:pk>/toggle/',views.toggle_block,name='toggle_block'),
 path('tasks/',views.tasks_view,name='tasks'),path('tasks/<int:pk>/edit/',views.edit_task,name='edit_task'),path('tasks/<int:pk>/toggle/',views.toggle_task,name='toggle_task'),
 path('history/',views.history_view,name='history'),path('download/',views.download_csv,name='download_csv'),
 path('plans/<int:pk>/download/',views.download_csv,name='download_plan'),path('plans/<int:pk>/reschedule/',views.reschedule_plan,name='reschedule_plan'),
 path('login/',views.login_view,name='login'),path('register/',views.register_view,name='register'),
 path('logout/',views.logout_view,name='logout'),path('api/chart/',views.chart_data_api,name='chart_data')]
