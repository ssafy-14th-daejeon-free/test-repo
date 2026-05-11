from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


class SignUpForm(UserCreationForm):
    email = forms.EmailField(label="Email")
    display_name = forms.CharField(label="Display name", max_length=40, required=False)
    bio = forms.CharField(
        label="Bio",
        required=False,
        widget=forms.Textarea(attrs={"rows": 3}),
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email", "display_name", "bio")

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("This email is already in use.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user
