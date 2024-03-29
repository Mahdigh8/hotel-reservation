from django import forms
from django.contrib.auth.models import User

class LoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)

class UserRegistrationForm(forms.ModelForm):

    #phone Number:
    phone = forms.CharField(label='Phone number')

    #national ID:
    national_id = forms.CharField(label="National id")
    
    # password 
    password = forms.CharField(label='Password',widget=forms.PasswordInput)

    # confrim password
    password2 = forms.CharField(label='Repeat password',widget=forms.PasswordInput)

    def __init__(self, *args, **kwargs):
        super(UserRegistrationForm, self).__init__(*args, **kwargs)
        self.fields['email'].required = True

    class Meta:
        model = User

        fields = ('first_name','last_name','email','username')

    def clean_password2(self):
        cd = self.cleaned_data

        if (cd['password'] != cd['password2']):
            raise forms.ValidationError('Passwords don\'t match !')
            
        return cd['password2']