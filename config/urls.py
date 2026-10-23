from django.urls import path
from maintenance import views
urlpatterns = [path('', views.dashboard, name='dashboard'), path('login/', views.sign_in, name='login'),
 path('logout/', views.sign_out, name='logout'), path('review/', views.review, name='review'),
 path('requests/new/', views.report, name='report'), path('requests/<int:pk>/', views.detail, name='detail'),
 path('requests/<int:pk>/<str:action>/', views.action, name='action')]
handler403 = 'maintenance.views.forbidden'
handler404 = 'maintenance.views.missing'
