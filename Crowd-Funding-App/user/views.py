from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth.models import User
from fundProject.models import Project,Donation,Images
from django.contrib.auth import authenticate
from .models import Profile

# Create your views here.

from .forms import UserRegisterForm, UserUpdateForm, ProfileUpdateForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.conf import settings
from django.core.mail import send_mail, BadHeaderError
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth import login
from django.contrib.auth.views import PasswordResetConfirmView
from base64 import urlsafe_b64decode
from django.utils import timezone

def register(request):
    if request.method == 'POST':
        u_form = UserRegisterForm(request.POST)
        p_form = ProfileUpdateForm(request.POST)

        if u_form.is_valid():
            user = u_form.save(commit=False)
            user.is_active = False
            user.save()

            send_activation_email(user)

            messages.success(request, f'An activation email has been sent to {user.email}. Please verify your email to complete registration.')
            return redirect('login')
    else:
        u_form = UserRegisterForm()
        p_form = ProfileUpdateForm()
    return render(request, 'users/register.html', {'u_form': u_form, 'p_form': p_form})
def send_activation_email(user):
    # Generate the token and encode the user's primary key
    token = default_token_generator.make_token(user)
    uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
    
    # Construct the activation link
    activation_link = f"http://localhost:8000/verify/{uidb64}/{token}/"

    subject = 'Activate your account'
    message = f'Hi {user.username},\n\nPlease click the link below to activate your account:\n{activation_link}\n\nThank you!'
    
    try:
        # Send the email
        send_mail(subject, message, settings.EMAIL_HOST_USER, [user.email])
        user.save()
    except Exception as e:
        # Handle any errors that occur during email sending
        return f'An error occurred while sending the activation email: {e}'
    
@login_required
def profile(request):
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)
        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, 'Your account has been updated!')
            return redirect('profile')
    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=request.user.profile)
    context = {'u_form': u_form, 'p_form': p_form}
    return render(request, 'users/profile.html', context)

@login_required
def myProjects(request):
    projects = Project.objects.filter(user=request.user)
    for project in projects:
        setattr(project, 'img', Images.objects.filter(project_id=project))
    
    donations = Donation.objects.filter(user=request.user)
    for donation in donations:
        setattr(donation, 'img', Images.objects.filter(project_id=donation.project_id))
    
    
    context = {'projects':projects, 'donations':donations}
    return render(request, 'users/myProjects.html', context)


@login_required
def DeleteAccount(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        user.delete()
        return redirect('login')  
    else:
        return redirect('profile')


def updateUser(request):
    return render(request, 'updateUser.html')

def insertuser(request):
    return render(request, 'insertspecificUser.html')

def addUser(request):
    return render(request, 'addUser.html')

def allUser(request):
    users = User.objects.all()
    for user in users:
        setattr(user, 'data', Profile.objects.filter(user=user))
    context = {'users':users}
    return render(request, 'allUser.html',context)


def verify_email(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    
    if user is not None and default_token_generator.check_token(user, token):
        # Check if the token has expired
        if timezone.now() - user.date_joined > timezone.timedelta(days=1):
            # Token has expired, you can handle it here (e.g., send a new activation email)
            send_activation_email(user)
            messages.error(request, 'The verification link has expired. We have sent you a new activation email.')
            return redirect('login')
        
        user.is_active = True
        user.save()
        messages.success(request, 'Your account has been successfully activated. You can now log in.')
        return redirect('login')  # Redirect to the login page or any other appropriate page after successful activation
    else:
        messages.error(request, 'Sorry, the verification link is invalid. Please try again or contact support.')
        return render(request, 'registration/verification_failed.html')
    


