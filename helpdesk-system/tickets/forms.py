from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

from .models import Ticket

User = get_user_model()


class LoginForm(forms.Form):
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(required=False)
    last_name = forms.CharField(required=False)

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2')


class TicketForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ['department', 'category', 'priority', 'description', 'screenshot']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 5}),
        }


class TicketUpdateForm(forms.ModelForm):
    assigned_to = forms.ModelChoiceField(
        queryset=User.objects.filter(role=User.ROLE_TECHNICIAN),
        required=False,
        label='Assign Technician',
    )

    class Meta:
        model = Ticket
        fields = ['assigned_to', 'status', 'notes']
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 4}),
        }
