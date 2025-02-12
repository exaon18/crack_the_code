from django.contrib import messages
from django.shortcuts import render,redirect
import hashlib
import time

from .models import MyUser,game,Ballance
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.conf import settings
from django.contrib.auth import login, authenticate,logout
from django.http import Http404, JsonResponse
from django.contrib.auth import login
from django.contrib import messages
from django.shortcuts import render, get_object_or_404
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
def index(request):
    return render(request,'index.html')
def signup(request):
    if request.method == 'POST':
        username=request.POST['username']
        firstname=request.POST['first_name']
        lastname=request.POST['last_name']
        email=request.POST['email']
        password=request.POST['password1']
        password2=request.POST['password2']
        if password == password2:
            if len(password2)<6:
                messages.error(request,'Password must be at least 6 characters long')
                return render(request,'signup.html')
            else:
                if MyUser.objects.filter(username=username).exists():
                    messages.error(request,'Username already exists, try another one!')
                    return render(request,'signup.html')
                else:
                    if MyUser.objects.filter(email=email).exists():
                        messages.error(request,'Email already exists')
                        return render(request,'signup.html')
                    else:
                        token = generate_unique_number(username)
                        user = MyUser.objects.create_user(username=username,
                                                          first_name=firstname,
                                                          last_name=lastname,
                                                          email=email,
                                                          password=password,
                                                          token=token)
                        user.is_active=False
                        user.token=token
                        print(user.token)
                        user.save()
                        print('user saved')
                        
                        try:
                            send_welcome_email(user, email,token)
                            messages.success(request,'Account created successfully, check your email for verification')
                            print('email sent')
                            return redirect('verify',username=user.username)
                        except Exception as e:
                            print(e)
                            messages.error(request,f'Error sending email: please sign up again')
                            user.delete()
                            return render(request, 'signup.html')
                        
                        
                        
    return render(request,'signup.html')


def verify(request, username):
    user = get_object_or_404(MyUser, username=username)
    if user.is_active:
        raise Http404
    if request.method == 'POST':
        token = request.POST['token']
        print(user.token)
        if user.token == token:
            user.is_active = True
            ballance=   Ballance.objects.create(user=user,ballance=0.00)
            ballance.save()
            user.save()
            login(request, user)
            messages.success(request, 'Account activated successfully.')
            return redirect('dashboard')  # Redirect to the home page or any other page
        else:
            messages.error(request, 'Invalid token')
            return render(request, 'activate.html', {'user': user})
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
            messages.error(request,'Invalid credentials')
            return render(request, 'login.html', )
    else:
        return render(request, 'login.html')
@login_required
def dashboard(request):
    username=request.user.username
    user=MyUser.objects.get(username=username)
    ballance=Ballance.objects.get(user=user).ballance
    return render(request,'dashboard.html',{'user':user,'ballance':ballance})
@login_required
def profile(request):
    if request.method == 'POST':
        user = request.user
        first_name=request.POST['first_name']
        last_name=request.POST['last_name']
        username=request.POST['username']
        if MyUser.objects.filter(username=username).exists():
            messages.error(request,'Username already exists, try another one!')
        else:
            if len(first_name)>200 or len(last_name)>200:
                messages.error(request,"First name and last name must be less than 200 characters")
            else:
                user_obj=MyUser.objects.get(username=user.username)
                user_obj.first_name=first_name
                user_obj.last_name=last_name
                user_obj.username=username  
            
    
        try:
            user_obj.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('profile')
        except Exception as e:
            return render(request,'profile.html')
    user_file=MyUser.objects.get(username=request.user.username)
    user_status = game.objects.get(user=user_file)
    ballance=Ballance.objects.get(user=user_file).ballance
    return render(request, 'profile.html', {'user': request.user, 'stat': user_status,'ballance':ballance})


@login_required
def logout_view(request):
    logout(request)
    messages.success(request, 'you have been logged out!')
    return redirect('login')
