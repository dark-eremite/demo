from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect


def login_view(request):
    """Страница авторизации."""
    if request.user.is_authenticated:
        return redirect('product_list')

    if request.method == 'POST':
        username = request.POST.get('username', '')
        password = request.POST.get('password', '')

        if username and password:
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                next_url = request.GET.get('next', 'product_list')
                return redirect(next_url)
            else:
                error = 'Неверный логин или пароль'
        else:
            error = 'Заполните все поля'
    else:
        error = None

    return render(request, 'buildmatapp/login.html', {'error': error})
