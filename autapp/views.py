from django.contrib import messages
from django.shortcuts import render,redirect
import hashlib
import time
from .models import MyUser,Ballance,GameHistory
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
        username = request.POST['username'].upper()
        firstname = request.POST['first_name']
        lastname = request.POST['last_name']
        email = request.POST['email']
        password = request.POST['password1']
        password2 = request.POST['password2']
        
        if password != password2:
            messages.error(request, 'Passwords do not match')
            return render(request, 'signup.html')
            
        if len(password) < 6:
            messages.error(request, 'Password must be at least 6 characters long')
            return render(request, 'signup.html')
        
        # Check for active user conflicts
        if MyUser.objects.filter(username=username, is_active=True).exists():
            messages.error(request, 'Username already exists, try another one!')
            return render(request, 'signup.html')
        if MyUser.objects.filter(email=email, is_active=True).exists():
            messages.error(request, 'Email already exists')
            return render(request, 'signup.html')
        
        # If inactive user exists, remove it
        inactive_user = MyUser.objects.filter(username=username, is_active=False).first()
        if inactive_user:
            inactive_user.delete()
        inactive_email = MyUser.objects.filter(email=email, is_active=False).first()
        if inactive_email:
            inactive_email.delete()
        
        # Now create the user once
        token = generate_unique_number(username)
        user = MyUser.objects.create_user(
            username=username,
            first_name=firstname,
            last_name=lastname,
            email=email,
            password=password,
            token=token
        )
        Ballance.objects.create(user=user, ballance=0.00)
        user.is_active = False  # User needs to verify via email
        user.save()
        
        try:
            send_welcome_email(user, email, token)
            messages.success(request, 'Account created successfully, check your email for verification')
            return redirect('verify', username=user.username)
        except Exception as e:
            messages.error(request, f'Error sending email: please sign up again')
            user.delete()
            return render(request, 'signup.html')
    return render(request, 'signup.html')



def verify(request, username):
    user = get_object_or_404(MyUser, username=username)
    if user.is_active: 
        raise Http404
    if request.method == 'POST':
        token = request.POST['token']
        print(user.token)
        if user.token == token:
            user.is_active = True
            user.save()
            GameHistory.objects.get_or_create(user=user,TotalPlayed=0,TotalWin=0,Totaloss=0,TotalEarning=0.00,)
            
            user.save()
            login(request, user)
            messages.success(request, 'Account activated successfully.')
            return JsonResponse({"Success": True, "message":"Account Verified successfully, redirecting you to the login page "})  # Redirect to the home page or any other page
        else:
            messages.error(request, 'Invalid token')
            return JsonResponse({"success": False, "message":"Invalid token"})
    
    return render(request, 'activate.html', {'user': user})

def login_view(request):
    if request.method == 'POST':
            username=request.POST['username'].upper()
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
    print(user.pendingWithdrwal)
    ballance=Ballance.objects.get(user=user).ballance
    return render(request,'dashboard.html',{'user':user,'ballance':ballance})
@login_required
def profile(request):
    if request.method == 'POST':
        user = request.user
        first_name=request.POST['first_name']
        last_name=request.POST['last_name']
        username=request.POST['username'].upper()
        if MyUser.objects.filter(username=username).exists():
            if request.user.username != username:
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
    Game_Stat, created = GameHistory.objects.get_or_create(
    user=user_file, 
    defaults={"TotalEarning": 0.00, "TotalPlayed": 0, "TotalWin": 0, "Totaloss": 0}
)

    ballance=Ballance.objects.get(user=user_file)
    print(f"total earning {Game_Stat.TotalEarning}") 
    print(f"total played {Game_Stat.TotalPlayed}")
    print(f"total won {Game_Stat.TotalWin}")
    print(f"total loss {Game_Stat.Totaloss}")

    return render(request, 'profile.html', {'user': request.user, 'stat': Game_Stat,'ballance':ballance})

@login_required
def logout_view(request):
    user=MyUser.objects.get(username=request.user.username)
    user.is_logged_in=False
    logout(request) 
    messages.success(request, 'you have been logged out!')
    return redirect('login')
