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
from django.views.decorators.http import require_POST
import re
from django.middleware.csrf import get_token
from django.views.decorators.csrf import csrf_exempt

def get_csrf_token(request):
    """
    View to provide a fresh CSRF token via AJAX.
    This is useful for SPA applications or when cookies might be blocked.
    """
    csrf_token = get_token(request)
    return JsonResponse({'csrf_token': csrf_token})

def send_welcome_email(user, email,token,why):
    subject = 'Welcome to Chiwe'
    from_email = settings.DEFAULT_FROM_EMAIL
    to_email = email
    # Render the HTML template with context
    if why=="signup":
        html_content = render_to_string('otp.html', {'user': user,'token':token})
    else:
        html_content = render_to_string('forgot.html', {'user': user,'token':token})
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
        
        email = request.POST['email']
        password = request.POST['password1']
        password2 = request.POST['password2']
        if "@" not in email:
            return JsonResponse({"success": False, "message":"Invalid email."})
        
        if password != password2:
            return JsonResponse({"success": False, "message":"Passwords do not match."})
            
        if len(password) < 6:
            return JsonResponse({"success": False, "message":"Password must be at least 6 characters."})
        
        # Check for active user conflicts
        if " " in username:
            return JsonResponse({"success": False, "message":"Username must not contain spaces."})
        if MyUser.objects.filter(username=username, is_active=True).exists():
            return JsonResponse({"success": False, "message":"Username already exists, try another one."})
        if MyUser.objects.filter(email=email, is_active=True).exists():
            return JsonResponse({"success": False, "message":"Email already exists, try another one."})
        
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
            email=email,
            password=password,
            token=token
        )
        Ballance.objects.create(user=user, ballance=0.00)
        user.is_active = False  # User needs to verify via email
        user.save()
        print("finished")
        try:
            send_welcome_email(user, email, token,why="signup")
            return JsonResponse({"success": True, "message":"OTP has been sent to your email, please check your inbox.",
                                 "username":username})
        except Exception as e:
            print(e)
            messages.error(request, f'Error sending email: please sign up again')
            user.delete()
            return JsonResponse({"success": False, "message":"system is busy , please sign up again."})
    return render(request, 'signup.html')



def verify(request, username):
   
    user = get_object_or_404(MyUser, username=username)
    if user.is_active: 
        raise Http404
    if request.method == 'POST':
        print(request.POST)
        if request.POST.get('type')=="fp":
           
            if str(username)==str(request.POST.get('username')):
               
               return resend_otp_signup(request, user)
            else:
                return JsonResponse({"success":False,"message":"Something went wrong , please refresh the page"})
        if not request.POST.get('token'):
            return JsonResponse({"success": False, "message":"OTP is required."})
        
            
        token = request.POST['token']
        print(user.token)
        if user.token == token:
            user.is_active = True
            user.save()
            GameHistory.objects.get_or_create(user=user,TotalPlayed=0,TotalWin=0,Totaloss=0,TotalEarning=0.00,)
            user.save()
            login(request, user)
            messages.success(request, 'Account activated successfully.')
            return JsonResponse({"success": True, "message":"Account Verified successfully, redirecting you to the login page "})  # Redirect to the home page or any other page
        else:
            messages.error(request, 'Invalid token')
            return JsonResponse({"success": False, "message":"Invalid token"})
    
    return render(request, 'activate.html', {'user': user})

from django.contrib import messages

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip().upper()
        password = request.POST.get('password', '')

        if not username or not password:
           
            return JsonResponse({"success": False, "message":"Username and password are required."})

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return JsonResponse({"success": True, "message":"Login successful."})
        else:
            
            return JsonResponse({"success": False, "message": "Invalid username or password"})
            
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
        
        username=request.POST['username'].upper()
        if " " in username:
            return JsonResponse({"success": False, "message":"Username must not contain spaces."})
        
        if MyUser.objects.filter(username=username).exists():
            if request.user.username != username:
                return JsonResponse({"success": False, "message":"Username already exists, try another one."})
            else:
                if len(first_name)>200 :
                    return JsonResponse({"success": False, "message":"First name and last name must be less than 200 characters"})
                else:
                    user_obj=MyUser.objects.get(username=user.username)
                    user_obj.first_name=first_name
                    user_obj.last_name=last_name
                    user_obj.username=username  
                    
            try:
                user_obj.save()
                return JsonResponse({"success": True, "message":"Profile updated successfully."})
            except Exception as e:
                return render(request,'profile.html')
        else:
            if len(first_name)>200  :
                return JsonResponse({"success":False,"messaege":"First name and last name must be less than 200 characters"})
            else:
                user_obj=MyUser.objects.get(username=user.username)
                user_obj.first_name=first_name
                user_obj.username=username  
                try:
                    user_obj.save()
                    return JsonResponse({"success": True, "message":"Profile updated successfully."})
                except Exception as e:
                    return JsonResponse({"success": False, "message":"Erorr updating profile try again"})
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
def forgot_password(request):
    if request.method == "POST":
        print(request.POST)
        email = request.POST["email"]
        try:
            user = MyUser.objects.get(email=email)
            if not user.is_active:
                return JsonResponse({"Success": False, "message":"User is not active."})
            otp = generate_unique_number(user.username)
            user.forgetPasswordToken = otp
            user.save()
            send_welcome_email(user=user, email=email, token=otp, why="forgot")
            return JsonResponse({"Success": True, "message":"OTP has been sent to your email, please check your inbox."})  # Redirect to the home page or any other page
        except MyUser.DoesNotExist:
            return JsonResponse({"Success": False, "message":"User not found."}) # Redirect to the home page or any other page
    else:
        return render(request, "forgot_password.html")
@require_POST 
def validate_recovery(request):
    if request.method == "POST":
        print(request.POST)
        email = request.POST["email"]
        token = request.POST["otp"]
        pass1=request.POST["new_password"]
        pass2=request.POST["confirm_password"]
        try:
            user = MyUser.objects.get(email=email)
            if not user.is_active:
                return JsonResponse({"Success": False, "message":"User is not active."})
            print(type(str(user.forgetPasswordToken)))
            print(type(token))
            if str(user.forgetPasswordToken) == token:
                if pass1==pass2:
                    if len(pass1)>6:
                        user.set_password(pass1)
                        user.save()
                        return JsonResponse({"Success": True, "message":"Password changed successfully."})  # Redirect to the home page or any other page
                    else:
                        return JsonResponse({"Success": False, "message":"Password must be at least 6 characters."})  # Redirect to the home page or any other page
                else:
                    return JsonResponse({"Success": False,"message":"Passwords do not match."})  # Redirect to the home page or any other page

            else:
                return JsonResponse({"Success": False, "message":"OTP is invalid."})  # Redirect to the home page or any other page
        except MyUser.DoesNotExist:
            return JsonResponse({"Success": False, "message":"User not found."}) # Redirect to the home page or any other page
from django.utils import timezone
from datetime import timedelta

@require_POST
def resend_otp_signup(request, userobj):
    print("i got in ")
    try:
        user = userobj
    
        if user.is_active:
            return JsonResponse({"success": False, "message": "User is already active."})
        cooldown_period = timedelta(seconds=60)
        now = timezone.now()
        last_otp=user.last_otp_sent
        if last_otp and now - last_otp < cooldown_period:
            remaining = cooldown_period - (now - last_otp)
            return JsonResponse({
                "success": False,
                "message": f"Please wait {int(remaining.total_seconds())} seconds before resending OTP."
                })
        otp = generate_unique_number(user.username)
        user.token = otp
        user.last_otp_sent = now
        user.save()
        send_welcome_email(user=user, email=user.email, token=otp, why="signup")
        return JsonResponse({"success": True, "message": "OTP has been sent to your email. Please check your inbox or SPAM folder."})
    except MyUser.DoesNotExist:
        return JsonResponse({"success": False, "message": "User not found."})
@csrf_exempt
@require_POST
def resend_otp_token_fp(request, username):
    try:
        user = MyUser.objects.get(username=username)
        
        if not user.is_active:
            return JsonResponse({"Success": False, "message": "User is not actived, please signup again."})
        cooldown_period = timedelta(seconds=60)
        now = timezone.now()
        last_otp=user.last_otp_fp
        if last_otp and now - last_otp < cooldown_period:
            remaining = cooldown_period - (now - last_otp)
            return JsonResponse({
                "Success": False,
                "message": f"Please wait {int(remaining.total_seconds())} seconds before resending OTP."
                })
        otp = generate_unique_number(user.username)
        user.forgetPasswordToken = otp
        user.last_otp_fp = now
        user.save()
        send_welcome_email(user=user, email=user.email, token=otp, why="forgot")
        return JsonResponse({"Success": True, "message": "OTP has been sent to your email. Please check your inbox or SPAM folder."})
    except MyUser.DoesNotExist:
        return JsonResponse({"Success": False, "message": "User not found."})

    