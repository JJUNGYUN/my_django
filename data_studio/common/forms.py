
from django.contrib.auth.forms import UserCreationForm
from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

class UserForm(UserCreationForm):
    class Meta:
        model = User
        fields = ("first_name","last_name", "username", "password1", "password2")

class ProfileForm(forms.ModelForm):
    first_name = forms.CharField(
        label="한글 이름",
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    last_name = forms.CharField(
        label="영문 이름",
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    password1 = forms.CharField(
        label="새 비밀번호",
        widget=forms.PasswordInput(
            attrs={'class': 'form-control', 'autocomplete': 'new-password'}
        ),
        required=False,
        help_text="변경하려면 새 비밀번호를 입력하세요."
    )
    password2 = forms.CharField(
        label="비밀번호 확인",
        widget=forms.PasswordInput(
            attrs={'class': 'form-control', 'autocomplete': 'new-password'}
        ),
        required=False
    )

    class Meta:
        model = User
        # username 은 수정 불가이므로 제외, first_name 과 last_name 만 편집
        fields = ('first_name', 'last_name')

    def clean(self):
        cleaned = super().clean()
        pw1 = cleaned.get('password1')
        pw2 = cleaned.get('password2')
        if pw1 or pw2:
            # 하나라도 입력되었다면 둘 다 같아야 함
            if pw1 != pw2:
                raise ValidationError("비밀번호가 서로 일치하지 않습니다.")
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        pw = self.cleaned_data.get('password1')
        if pw:
            user.set_password(pw)
        if commit:
            user.save()
        return user