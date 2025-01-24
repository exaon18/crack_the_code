from django.shortcuts import render
from autapp.models import Game,MyUser
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import Http404

# Create your views here.
@login_required
def game(request,game_type):
    user=request.user
    if user.is_authenticated:
        username=user.username
        if Game.objects.filter(user=user,game_status=False).exists():
            messages.error(request, 'Game already started')
            return render(request, 'game.html',{'user':user,'game_type':game_type})
        else:
            user=MyUser.objects.get(username=username)
            game_to_be_played=Game.objects.create(game_type=game_type,user=user,game_status=False)
            game_to_be_played.save()
            messages.success(request, 'Game started successfully')
            return render(request, 'game.html',{'user':user,'game_type':game_type})
    else:
         raise Http404


