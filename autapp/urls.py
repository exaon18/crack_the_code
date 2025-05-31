from django.urls import path
from . import views
from django.contrib.sitemaps.views import sitemap
from autapp.sitemaps import StaticViewSitemap
sitemaps = {
    'static': StaticViewSitemap,
}
urlpatterns = [
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='sitemap'),
    path('', views.index, name='index'),
    path('signup', views.signup, name='signup'),
    path('login', views.login_view, name='login'),
    path('dashboard', views.dashboard, name='dashboard'),
    path('verify/<str:username>', views.verify, name='verify'),
    path('profile/', views.profile, name='profile'),
    path('logout/',views.logout_view,name='logout'),
    path("recovery/", views.forgot_password, name="recovery"),
    path("recovery/validate_recovery/", views.validate_recovery, name="validate_recovery"),
    path('get-csrf-token/', views.get_csrf_token, name='get_csrf_token'),
    path('resend-otp-signup/<str:username>', views.resend_otp_signup, name='resend_otp'),
    path('recovery/resend-otp-fp/', views.resend_otp_token_fp, name='resend_otp_fp'),
    
]
from django.conf.urls import handler404
from django.shortcuts import render

def custom_404(request, exception):
    return render(request, '404.html', status=404)

handler404 = 'autapp.urls.custom_404'
