from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth import authenticate,login
from .forms import LoginForm,UserRegistrationForm

# Create your views here.


def user_login(request):
    if (request.method == 'POST'):
        form = LoginForm(request.POST)

        if (form.is_valid()):
            cd = form.cleaned_data

            user = authenticate(username = cd['username'],password = cd['password'])

            if (user is not None):
                if user.is_active:
                    login(request,user)

                    return HttpResponse('Authenticated successfully !')
                
                else:
                    return HttpResponse('Disabled account !')
            else:
                return HttpResponse('Invalid login !')
    else:
        form = LoginForm()
        
    return render(request,'AccountApp/login.html',{'form':form})

def register(request):

    if (request.method == 'POST'):
        user_form = UserRegistrationForm(request.POST)

        if user_form.is_valid():
            # create a new user
            new_user = user_form.save(commit=False)
            # set password:
            new_user.set_password(user_form.cleaned_data['password'])

            #save user:
            new_user.save()
            return render(request,'AccountApp/register_done.html',{'new_user':new_user})
    
    else:
        user_form = UserRegistrationForm()
    
    return render(request,'AccountApp/register.html',{'user_form':user_form})