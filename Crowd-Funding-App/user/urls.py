# urls.py
from django.urls import path,include
from .views import * 
from django.contrib.auth import views as auth_views
from django.contrib.auth.views import LogoutView



urlpatterns = [
    path('auth/',include('django.contrib.auth.urls')),
    path('', allUser, name='allUser'),
    path('addUser/', addUser, name='addUser'),
    path('updateUser/<int:id>', updateUser, name='updateUser'),
    path('register/', register, name='register'),
    path('profile/', profile, name='profile'),
    path('login/', auth_views.LoginView.as_view(template_name='users/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(template_name='users/logout.html'), name='logout'),
    path('Delete/<int:user_id>/',DeleteAccount,name='DeleteAccount'),
    path('verify/<str:uidb64>/<str:token>/', verify_email, name='verify_email'),
    path('myProjects/', myProjects, name='myProjects')

]
 