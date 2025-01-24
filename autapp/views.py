from django.contrib import messages
from django.shortcuts import render,redirect
import hashlib
import time 
from .models import MyUser,Game
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.conf import settings
from django.contrib.auth import login, authenticate
from django.http import Http404
def send_welcome_email(user, email,token):
    subject = 'Welcome to Chiwe'
    from_email = settings.DEFAULT_FROM_EMAIL
    to_email = email
    # Render the HTML template with context
    html_content = render_to_string('otp.html', {'user': user,'token':token})
    # Create the email message
    email = EmailMessage(subject, html_content, from_email, [to_email])
    email.content_subtype = 'html'  # Set the content type to HTML
    # Send the email
    email.send()

def generate_unique_number(username):
    # Get the current timestamp
    timestamp = str(time.time())

    # Combine the username and timestamp
    seed = username + timestamp

    # Create a hash of the seed
    hash_object = hashlib.sha256(seed.encode())

    # Convert the hash to an integer and get the last 6 digits
    unique_number = int(hash_object.hexdigest(), 16) % 1000000

    # Ensure the number is 6 digits by padding with zeros if necessary
    return str(unique_number).zfill(6)


# Create your views here.
def index(request):
    return render(request, 'index.html')
def signup(request):
    if request.method == 'POST':
        print('hey')
        username=request.POST['username']
        firstname=request.POST['first_name']
        lastname=request.POST['last_name']
        email=request.POST['email']
        password=request.POST['password1']
        password2=request.POST['password2']
        if password == password2:
            if MyUser.objects.filter(username=username).exists():
                messages.error(request, 'Username already exists')
                return redirect('signup')
            elif MyUser.objects.filter(email=email).exists():
                messages.error(request, 'Email already exists')
                return redirect('signup')
            else:
                token=generate_unique_number(username)
                user = MyUser.objects.create_user(username=username, 
                                                  first_name=firstname, 
                                                  last_name=lastname, 
                                                  email=email,
                                                    password=password, 
                                                    token=token)
                user.is_active=False
                send_welcome_email(user, email,token)
                user.save()
                return redirect('activate', user=user)

        else:
            return render(request, 'index.html', {'error': 'Password and Confirm Password does not match'})
    else:
        return render(request, 'signup.html')
            
def activate(request,user):
    user_to_be_activated=MyUser.objects.get(username=user)      
    if request.method == 'POST':
        token=request.POST['token']
        print(token)
        print(user_to_be_activated.token)
        
        if user_to_be_activated.token==token:
            user_to_be_activated.is_active=True
            user_to_be_activated.token=''
            user_to_be_activated.save()
            
            return redirect('login')
        else:
            return render(request, 'index.html', {'error': 'Invalid token'})
    else:
        if user_to_be_activated.is_active:
            raise Http404
            
        return render(request, 'activate.html', {'user': user})
def login_view(request):
    if request.method == 'POST':
        username=request.POST['username']
        password=request.POST['password']
        user=authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard')
            
        else:
            return render(request, 'index.html', {'error': 'Invalid credentials'})
    else:
        return render(request, 'login.html')
@login_required
def dashboard(request):
    user=request.user
    if user.is_authenticated:
        username=user.username
    
        user=MyUser.objects.get(username=username)
    return render(request, 'dashboard.html',{'user':user})
@login_required
def join_game(request):
    user = request.user
    if user.is_authenticated:
        username = user.username
        palayer=MyUser.objects.get(username=username)
        games=Game.objects.create(user=palayer,game_id='1',game_status=False,channel_name='mkmskdnknad12')
        games.save()

        return render(request, 'join_game.html',{"game":games})
