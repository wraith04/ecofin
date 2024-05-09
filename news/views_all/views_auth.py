from captcha.fields import CaptchaField
from django import forms
from django.shortcuts import render


class LoginForm(forms.Form):
    username = forms.CharField(label='用户名', max_length=100)
    password = forms.CharField(label='密码', widget=forms.PasswordInput)
    captcha = CaptchaField(label='验证码')


from django.http import HttpResponseRedirect


def user_login(request):
    next_url = request.GET.get('next', 'home')  # 尝试从GET请求中获取'next'参数，如果没有，则默认为'home'
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return HttpResponseRedirect(next_url)  # 使用重定向到'next_url'
            else:
                form.add_error(None, '用户名或密码不正确')
    else:
        form = LoginForm()
    return render(request, 'registration/login.html', {'form': form, 'next': next_url})


from django.contrib.auth import get_user_model, authenticate, login

User = get_user_model()


class RegisterForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}), label="密码")
    password2 = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}), label="确认密码")

    class Meta:
        model = User
        fields = ('username', 'email')  # 移除'user_type'
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }
        error_messages = {
            'username': {
                'required': "用户名是必填项。",
                'max_length': "用户名不能超过150个字符。",
                'invalid': "用户名只能包含字母、数字以及 @/./+/-/_ 符号。",
            },
            'email': {
                'required': "电子邮件是必填项。",
                'invalid': "请输入一个有效的电子邮件地址。",
            },
            # 如果有其他字段的自定义错误消息也可以在这里添加
        }

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("该用户名已被占用，请选择其他用户名。")
        return username
    def clean_password2(self):
        cd = self.cleaned_data
        if cd['password'] != cd['password2']:
            raise forms.ValidationError('密码不匹配。')
        return cd['password2']
def register(request):
    next_url = request.GET.get('next', 'home')  # 尝试从GET请求中获取'next'参数，如果没有，则默认为'home'
    if request.method == 'POST':
        user_form = RegisterForm(request.POST)
        if user_form.is_valid():
            # 创建但不保存新用户记录
            new_user = user_form.save(commit=False)
            # 设置密码
            new_user.set_password(user_form.cleaned_data['password'])
            # 设置用户类型为"RegisteredUser"
            new_user.user_type = 'RegisteredUser'
            # 保存用户
            new_user.save()
            return HttpResponseRedirect(next_url)  # 重定向到 'next_url'
    else:
        user_form = RegisterForm()
        print(user_form)
    return render(request, 'registration/register.html', {'user_form': user_form})


class UserUpdateForm(forms.ModelForm):
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ['username', 'email', 'avatar']

