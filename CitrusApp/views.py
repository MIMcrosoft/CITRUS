from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from .models import Coach
from .admin import CoachChangeForm

"""

"""


def accueil(request):
    if request.method == 'POST':
        pass

    return render(request, 'Acceuil.html', {})


"""

"""


def loginUser(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('')
        else:
            messages.error(request, 'Erreur')
            return redirect('login')
    else:

        return render(request, "components/components.html", {})


"""

"""


def coachSignIn(request, id):
    if request.method == 'POST':
        coach = get_object_or_404(Coach, id=id)
        form = CoachChangeForm(request.POST, instance=coach)
        if form.is_valid():
            form.save()
            return redirect('Accueil')
        else:
            # MSG ERREUR
            return redirect('Acceuil')

    return render(request, "coachSignIn.html", {id})


"""

"""


def equipes(request):
    if request.method == 'POST':
        pass

    return render(request, "base.html", {})


"""

"""


def calendrier(request):
    if request.method == 'POST':
        pass

    return render(request, "base.html", {})


"""

"""


def classements(request):
    if request.method == 'POST':
        pass

    return render(request, "base.html", {})


"""

"""


def tournois(request):
    if request.method == 'POST':
        pass

    return render(request, "base.html", {})


"""

"""


def archives(request):
    if request.method == 'POST':
        pass

    return render(request, "base.html", {})
