from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages


def signup_view(request):
    """회원가입 뷰"""
    if request.user.is_authenticated:
        return redirect('chatbot:chat')
    
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, '회원가입이 완료되었습니다!')
            return redirect('chatbot:chat')
    else:
        form = UserCreationForm()
    
    return render(request, 'users/signup.html', {'form': form})


def login_view(request):
    """로그인 뷰"""
    if request.user.is_authenticated:
        return redirect('chatbot:chat')
    
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'{username}님, 환영합니다!')
                return redirect('chatbot:chat')
    else:
        form = AuthenticationForm()
    
    return render(request, 'users/login.html', {'form': form})


def logout_view(request):
    """로그아웃 뷰"""
    logout(request)
    messages.info(request, '로그아웃되었습니다.')
    return redirect('home')
