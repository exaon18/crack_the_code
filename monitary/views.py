from django.conf import settings
from django.shortcuts import render, redirect
from django.http import Http404, JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from django.urls import reverse
from autapp.models import MyUser, Ballance
from .models import WithdrawalRequest
import random
from django.contrib.auth import authenticate, login
invalidOtp = False
# ✅ Generate a proper 6-digit OTP
def generate_unique_number():
    return str(random.randint(100000, 999999))  # Always generates a 6-digit OTP

# ✅ Send email properly
def send_welcome_email(user, email, token, subjectE):
    subject = subjectE
    from_email = settings.DEFAULT_FROM_EMAIL
    to_email = email
    print(f"📧 Sending email to: {to_email}")
    html_content = render_to_string('withdrawOTP.html', {'user': user, 'token': token})
    
    email_message = EmailMessage(subject, html_content, from_email, [to_email])
    email_message.content_subtype = 'html'
    
    try:
        email_message.send()
        print(f"✅ Email sent successfully to {email}")
    except Exception as e:
        print(f"❌ Email sending failed: {e}")

@login_required
def withdraw(request, invalidOtp=invalidOtp):
    
    user = request.user
    user_balance = Ballance.objects.get(user=user).ballance

    if request.method == 'POST':
        try:
            amount = float(request.POST["amount"])
        except ValueError:
            messages.error(request, "Please enter a valid number for the amount.")
            print("Redirecting to 'withdraw' after invalid amount input.")
            return redirect("withdraw")
        
        token = request.POST["token"].strip()
        phone_number = request.POST["phone_number"].strip()

        if user.pendingWithdrwal:
            print("⏳ User already has a pending withdrawal. Rendering 'withdraw.html'.")
            messages.error(request, "You already have a pending withdrawal. Please wait for it to be completed.")
            return render(request, "dashboard")
        
        # Compare after converting token from the form to int
        if user.withdrawalToken == int(token) and user_balance >= amount:
            if amount < 25:
                print("❌ Withdrawal amount too low. Rendering 'withdraw.html'.")
                invalidOtp = True
                messages.error(request, "Withdrawal amount must be at least 25 birr.")
                return JsonResponse(request,{"success":False,"message":"Withdrawal amount must be at least 25 birr."})
            
            WithdrawalRequest.objects.create(
                user=user,
                amount=amount,
                phone_number=phone_number,
                status="Pending"
            )
            user.pendingWithdrwal = True
            user.withdrawalToken = None  # Reset OTP after use
            user.save()

            print(f"✅ Withdrawal request submitted: {amount} ETB. Redirecting to 'withdraw'.")
            messages.success(request, f"Your withdrawal request for {amount} ETB has been submitted successfully.")
            return JsonResponse({"success":True,"message":f"Your withdrawal request for {amount} ETB has been submitted successfully."})
        else:
            invalidOtp = True
            print("❌ Invalid OTP or insufficient balance. Redirecting to 'withdraw'.")
            messages.error(request, "Invalid OTP or insufficient balance.")
            return JsonResponse({"success":False, "message":"Invalid OTP or Insufficinet balance"})
    else:
        if user.pendingWithdrwal==True:
            print(f"🔹 Pending Withdrawal: {user.pendingWithdrwal} and wihdrawaal token {user.withdrawalToken}")
            return redirect("dashboard")
        if user.pendingWithdrwal==False and user.withdrawalToken != None and invalidOtp==False:
            print("1st")
            generated_token=generate_unique_number()
            user.pendingWithdrwal = False   
            user.withdrawalToken = generated_token
            user.save()
            print(f"🔹 Generated OTP: {generated_token}")
            print(f"🔹 Pending Withdrawal: {user.pendingWithdrwal} and wihdrawaal token {user.withdrawalToken}")
            send_welcome_email(user=user, email=user.email, token=generated_token, subjectE="Your Withdrawal OTP")
            print("⏳ User didnt requested a withdrwal. Rendering 'withdraw.html'.")
            messages.error(request, "You already have a pending withdrawal. Please wait for it to be completed.")
            return render(request,"withdraw.html")
        elif  user.withdrawalToken==None and user.pendingWithdrwal == False:
            generated_token = generate_unique_number()
            user.withdrawalToken = generated_token
            user.save()
            print(f"🔹 Pending Withdrawal: {user.pendingWithdrwal} and wihdrawaal token {user.withdrawalToken}")
            print(f"🔹 Generated OTP: {generated_token}")
            send_welcome_email(user=user, email=user.email, token=generated_token, subjectE="Your Withdrawal OTP")
        print("Rendering 'withdraw.html'.")
        print(f"with token {user.withdrawalToken} , pending {user.pendingWithdrwal}")

        return render(request, "withdraw.html")

def ChiweA(request, username):
    try:
        admin_user = MyUser.objects.get(username=username)
    except MyUser.DoesNotExist:
        print("❌ Admin not found. Raising 404.")
        raise Http404("Admin not found")
    
    if admin_user.is_staff:
        if request.method == "POST":
            password = request.POST["password"]
            user = authenticate(request, username=username, password=password)
            if user is not None:
                # Build URL using the URL pattern parameter 'admin'
                url = reverse("Monitering", kwargs={"admin": username})
                print(f"🔄 Redirecting to: {url}")
                return redirect(url)
            else:
                print("❌ Authentication failed! Redirecting to 'signup'.")
                return redirect("signup")
        else:
            print("Rendering 'loginA.html' for admin login.")
            return render(request, "loginA.html", {"admin": username})
    else:
        print("❌ User is not staff. Raising 404.")
        raise Http404

def Monitering(request, admin):
    try:
        admin_user = MyUser.objects.get(username=admin)
    except MyUser.DoesNotExist:
        print("❌ Admin not found in Monitering. Raising 404.")
        raise Http404("Admin not found")

    if admin_user.is_staff:
        Pdata = WithdrawalRequest.objects.filter(status="Pending")
        Adata = WithdrawalRequest.objects.filter(status="Approved")
        Rdata = WithdrawalRequest.objects.filter(status="Rejected")

        print(f"📊 Admin: {admin} - Pending: {Pdata.count()}, Approved: {Adata.count()}, Rejected: {Rdata.count()}")

        if request.method == "POST":
            
            amount = request.POST["amount"]
            user = request.POST["username"]
            phoneNumber= request.POST["phone_number"]
            AdminRES = request.POST["adminres"]
          
            try:
                Player = MyUser.objects.get(username=user)
                PlayerB = Ballance.objects.get(user=Player)
                WR = WithdrawalRequest.objects.filter(user=Player, status="Pending")

                if int(PlayerB.ballance) >= int(amount) and WR.exists() and AdminRES == "Approved":
                    PlayerB.ballance -= int(amount)
                    PlayerB.save()
                    Player.pendingWithdrwal = False
                    Player.withdrawalToken = None
                    Player.save()
                    WR.update(status="Approved")
                        
                    
                    messages.success(request, f"✅ approved {amount} ETB to {user}.")
                    print(f"✅ Approved transaction: {user} - {amount} ETB. Rendering 'admin.html'.")
                    return render(request, "admin.html", {"Adata": Adata, "Pdata": Pdata, "Rdata": Rdata, "admin": admin})
                elif AdminRES == "Rejected":
                    WR.update(status="Rejected")
                    Player.pendingWithdrwal = False
                    Player.withdrawalToken = None
                    Player.save()
                    messages.error(request, f"❌ rejected {amount} ETB to {user}.")
                    print(f"❌ Rejected transaction: {user} - {amount} ETB. Rendering 'admin.html'.")
                    return render(request, "admin.html", {"Adata": Adata, "Pdata": Pdata, "Rdata": Rdata, "admin": admin})
                 
                else:
                    print("❌ Invalid transaction attempt. Rendering 'admin.html'.")
            except MyUser.DoesNotExist:
                print("❌ User does not exist!")
            except Ballance.DoesNotExist:
                print("❌ User has no balance record!")

        print("Rendering 'admin.html' with current data.")
        
        return render(request, "admin.html", {"Adata": Adata, "Pdata": Pdata, "Rdata": Rdata, "admin": admin})
    else:
        print("❌ User is not staff in Monitering. Raising 404.")
        raise Http404

def deposit(request):
    pass 