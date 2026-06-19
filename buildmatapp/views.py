from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q, F, Sum
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.utils import timezone
from PIL import Image
from io import BytesIO
from .models import Product, ProductMaterial, CustomUser, Category, Manufacturer, Supplier, Order, OrderItem


def is_admin(user):
    """Проверка, что пользователь — администратор."""
    return user.is_authenticated and user.role == 'admin'


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


def register_view(request):
    """Регистрация нового пользователя."""
    if request.user.is_authenticated:
        return redirect('product_list')

    if request.method == 'POST':
        username = request.POST.get('username', '')
        password1 = request.POST.get('password1', '')
        password2 = request.POST.get('password2', '')
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')

        if username and password1 and password2 and first_name and last_name:
            if password1 == password2:
                if not CustomUser.objects.filter(username=username).exists():
                    CustomUser.objects.create_user(
                        username=username,
                        password=password1,
                        first_name=first_name,
                        last_name=last_name,
                    )
                    return redirect('login')
                else:
                    error = 'Пользователь с таким логином уже существует'
            else:
                error = 'Пароли не совпадают'
        else:
            error = 'Заполните все поля'
    else:
        error = None

    return render(request, 'buildmatapp/register.html', {'error': error})


@login_required
def logout_view(request):
    """Выход из системы."""
    logout(request)
    return redirect('login')


def product_list_view(request):
    """Список товаров с фильтрацией, сортировкой и поиском."""
    products = Product.objects.all()
    is_admin_user = request.user.is_authenticated and request.user.role == 'admin'
    is_manager_user = request.user.is_authenticated and request.user.role == 'manager'

    # Получаем параметры из GET запроса для AJAX
    search = request.GET.get('search', '')
    manufacturer_id = request.GET.get('manufacturer', '')
    sort_by = request.GET.get('sort', '-created_at')

    # Фильтрация по производителю (только для авторизованных пользователей с правами)
    if manufacturer_id:
        products = products.filter(manufacturer_id=manufacturer_id)

    # Поиск по текстовым полям
    if search:
        products = products.filter(
            Q(name__icontains=search) |
            Q(description__icontains=search) |
            Q(category__name__icontains=search) |
            Q(manufacturer__name__icontains=search) |
            Q(supplier__name__icontains=search)
        )

    # Сортировка
    valid_sort_fields = ['name', '-name', 'price', '-price', 'stock_quantity', '-stock_quantity', 'discount', '-discount', 'created_at', '-created_at']
    if sort_by in valid_sort_fields:
        products = products.order_by(sort_by)

    # Получаем данные для фильтров
    manufacturers = Manufacturer.objects.all()
    categories = Category.objects.all()

    context = {
        'products': products,
        'is_admin': is_admin_user,
        'is_manager': is_manager_user,
        'manufacturers': manufacturers,
        'categories': categories,
        'current_search': search,
        'current_manufacturer': manufacturer_id,
        'current_sort': sort_by,
        'is_authenticated': request.user.is_authenticated,
        'user': request.user if request.user.is_authenticated else None,
    }

    # Если это AJAX запрос (для фильтрации/поиска в реальном времени)
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render(request, 'buildmatapp/product_list.html', context)

    return render(request, 'buildmatapp/product_list.html', context)


def product_detail_view(request, product_id):
    """Просмотр деталей товара."""
    product = get_object_or_404(Product, id=product_id)
    return render(request, 'buildmatapp/product_detail.html', {'product': product})


@login_required
@user_passes_test(is_admin, login_url='product_list')
def product_create_view(request):
    """Добавление нового товара (только для администратора)."""
    if request.method == 'POST':
        name = request.POST.get('name', '')
        description = request.POST.get('description', '')
        category_id = request.POST.get('category')
        manufacturer_id = request.POST.get('manufacturer')
        supplier = request.POST.get('supplier', '')
        price = request.POST.get('price', '0')
        discount = request.POST.get('discount', '0')
        unit = request.POST.get('unit', 'шт')
        stock_quantity = request.POST.get('stock_quantity', '0')

        # Валидация данных
        errors = []
        try:
            price_val = float(price)
            if price_val < 0:
                errors.append('Цена не может быть отрицательной')
        except ValueError:
            errors.append('Некорректный формат цены')

        try:
            discount_val = float(discount)
            if discount_val < 0 or discount_val > 100:
                errors.append('Скидка должна быть от 0 до 100')
        except ValueError:
            errors.append('Некорректный формат скидки')

        try:
            stock_val = int(stock_quantity)
            if stock_val < 0:
                errors.append('Количество не может быть отрицательным')
        except ValueError:
            errors.append('Некорректный формат количества')

        # Обработка изображения
        image_file = request.FILES.get('image')
        if image_file:
            # Проверяем и масштабируем изображение
            try:
                img = Image.open(image_file)
                img = img.convert('RGB')  # Преобразуем в RGB
                img.thumbnail((300, 200))  # Масштабируем до 300x200

                # Сохраняем изображение
                from django.core.files.uploadedfile import InMemoryUploadedFile
                from PIL import Image
                import io

                output = io.BytesIO()
                img.save(output, format='JPEG', quality=85)
                output.seek(0)

                image_file = InMemoryUploadedFile(
                    output,
                    'ImageField',
                    f"{name}.jpg",
                    'image/jpeg',
                    output.tell(),
                    None
                )
            except Exception as e:
                errors.append('Ошибка обработки изображения')
                image_file = None

        if errors:
            return render(request, 'buildmatapp/product_form.html', {
                'product': None,
                'errors': errors,
                'categories': Category.objects.all(),
                'manufacturers': Manufacturer.objects.all(),
                'suppliers': Supplier.objects.all(),
                'is_admin': True,
                'is_manager': False,
                'manufacturers_list': Manufacturer.objects.all(),
                'categories_list': Category.objects.all(),
                'user': request.user,
                'is_authenticated': True,
            })

        # Создаём новый товар
        product = Product.objects.create(
            name=name,
            description=description,
            category_id=category_id if category_id else None,
            manufacturer_id=manufacturer_id if manufacturer_id else None,
            supplier=supplier,
            price=price_val,
            discount=discount_val,
            unit=unit,
            stock_quantity=stock_val,
        )

        # Сохраняем изображение, если оно есть
        if image_file:
            product.image.save(f"{product.name}.jpg", image_file, save=True)

        return redirect('product_list')

    return render(request, 'buildmatapp/product_form.html', {
        'product': None,
        'errors': [],
        'categories': Category.objects.all(),
        'manufacturers': Manufacturer.objects.all(),
        'suppliers': Supplier.objects.all(),
        'is_admin': True,
        'is_manager': False,
        'manufacturers_list': Manufacturer.objects.all(),
        'categories_list': Category.objects.all(),
        'user': request.user,
        'is_authenticated': True,
    })


@login_required
@user_passes_test(is_admin, login_url='product_list')
def product_edit_view(request, product_id):
    """Редактирование товара (только для администратора)."""
    product = get_object_or_404(Product, id=product_id)

    if request.method == 'POST':
        name = request.POST.get('name', '')
        description = request.POST.get('description', '')
        category_id = request.POST.get('category')
        manufacturer_id = request.POST.get('manufacturer')
        supplier = request.POST.get('supplier', '')
        price = request.POST.get('price', '0')
        discount = request.POST.get('discount', '0')
        unit = request.POST.get('unit', 'шт')
        stock_quantity = request.POST.get('stock_quantity', '0')

        # Валидация данных
        errors = []
        try:
            price_val = float(price)
            if price_val < 0:
                errors.append('Цена не может быть отрицательной')
        except ValueError:
            errors.append('Некорректный формат цены')

        try:
            discount_val = float(discount)
            if discount_val < 0 or discount_val > 100:
                errors.append('Скидка должна быть от 0 до 100')
        except ValueError:
            errors.append('Некорректный формат скидки')

        try:
            stock_val = int(stock_quantity)
            if stock_val < 0:
                errors.append('Количество не может быть отрицательным')
        except ValueError:
            errors.append('Некорректный формат количества')

        # Обработка нового изображения
        image_file = request.FILES.get('image')
        if image_file:
            try:
                img = Image.open(image_file)
                img = img.convert('RGB')
                img.thumbnail((300, 200))

                from django.core.files.uploadedfile import InMemoryUploadedFile
                import io

                output = io.BytesIO()
                img.save(output, format='JPEG', quality=85)
                output.seek(0)

                image_file = InMemoryUploadedFile(
                    output,
                    'ImageField',
                    f"{name}.jpg",
                    'image/jpeg',
                    output.tell(),
                    None
                )

                # Удаляем старое изображение, если оно есть
                if product.image:
                    if default_storage.exists(product.image.name):
                        default_storage.delete(product.image.name)
            except Exception as e:
                errors.append('Ошибка обработки изображения')
                image_file = None

        if errors:
            return render(request, 'buildmatapp/product_form.html', {
                'product': product,
                'errors': errors,
                'categories': Category.objects.all(),
                'manufacturers': Manufacturer.objects.all(),
                'suppliers': Supplier.objects.all(),
                'is_admin': True,
                'is_manager': False,
                'manufacturers_list': Manufacturer.objects.all(),
                'categories_list': Category.objects.all(),
                'user': request.user,
                'is_authenticated': True,
            })

        # Обновляем товар
        product.name = name
        product.description = description
        product.category_id = category_id if category_id else None
        product.manufacturer_id = manufacturer_id if manufacturer_id else None
        product.supplier = supplier
        product.price = price_val
        product.discount = discount_val
        product.unit = unit
        product.stock_quantity = stock_val

        # Сохраняем новое изображение, если оно есть
        if image_file:
            product.image.save(f"{product.name}.jpg", image_file, save=False)

        product.save()
        return redirect('product_list')

    return render(request, 'buildmatapp/product_form.html', {
        'product': product,
        'errors': [],
        'categories': Category.objects.all(),
        'manufacturers': Manufacturer.objects.all(),
        'suppliers': Supplier.objects.all(),
        'is_admin': True,
        'is_manager': False,
        'manufacturers_list': Manufacturer.objects.all(),
        'categories_list': Category.objects.all(),
        'user': request.user,
        'is_authenticated': True,
    })


@login_required
@user_passes_test(is_admin, login_url='product_list')
def product_delete_view(request, product_id):
    """Удаление товара (только для администратора)."""
    product = get_object_or_404(Product, id=product_id)

    # Проверяем, есть ли товар в заказах
    if ProductMaterial.objects.filter(product=product).exists():
        return JsonResponse({
            'success': False,
            'error': 'Нельзя удалить товар, который присутствует в заказах'
        })

    # Удаляем изображение, если оно есть
    if product.image:
        if default_storage.exists(product.image.name):
            default_storage.delete(product.image.name)

    product.delete()
    return JsonResponse({'success': True})


def material_calculation_view(request):
    """Расчёт количества материалов для нужного продукта."""
    result = None
    products = Product.objects.all()

    if request.method == 'POST':
        product_id = request.POST.get('product')
        quantity = request.POST.get('quantity', 1)

        if product_id and quantity:
            try:
                product = Product.objects.get(id=product_id)
                quantity = int(quantity)

                materials = ProductMaterial.objects.filter(product=product).annotate(
                    total_quantity=F('quantity_per_unit') * quantity
                )

                result = {
                    'product': product,
                    'quantity': quantity,
                    'materials': materials,
                }
            except Product.DoesNotExist:
                result = {'error': 'Продукт не найден'}

    return render(request, 'buildmatapp/calculate.html', {
        'result': result,
        'products': products,
    })


def order_list_view(request):
    """Список заказов с фильтрацией и поиском."""
    is_admin_user = request.user.is_authenticated and request.user.role == 'admin'
    is_manager_user = request.user.is_authenticated and request.user.role == 'manager'

    # Менеджер и администратор могут видеть все заказы
    orders = Order.objects.all()

    # Получаем параметры из GET запроса для AJAX
    search = request.GET.get('search', '')
    status = request.GET.get('status', '')
    sort_by = request.GET.get('sort', '-order_date')

    # Фильтрация по статусу
    if status:
        orders = orders.filter(status=status)

    # Поиск по артикулу и адресу
    if search:
        orders = orders.filter(
            Q(article__icontains=search) |
            Q(pickup_address__icontains=search)
        )

    # Сортировка
    valid_sort_fields = ['article', '-article', 'order_date', '-order_date', 'pickup_date', '-pickup_date', 'status', '-status']
    if sort_by in valid_sort_fields:
        orders = orders.order_by(sort_by)

    context = {
        'orders': orders,
        'is_admin': is_admin_user,
        'is_manager': is_manager_user,
        'current_search': search,
        'current_status': status,
        'current_sort': sort_by,
        'is_authenticated': request.user.is_authenticated,
        'user': request.user if request.user.is_authenticated else None,
    }

    # Если это AJAX запрос (для фильтрации/поиска в реальном времени)
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return render(request, 'buildmatapp/order_list.html', context)

    return render(request, 'buildmatapp/order_list.html', context)


@login_required
@user_passes_test(is_admin, login_url='order_list')
def order_create_view(request):
    """Добавление нового заказа (только для администратора)."""
    if request.method == 'POST':
        article = request.POST.get('article', '')
        status = request.POST.get('status', 'pending')
        pickup_address = request.POST.get('pickup_address', '')
        order_date = request.POST.get('order_date', '')
        pickup_date = request.POST.get('pickup_date', '')

        # Валидация данных
        errors = []
        if not article:
            errors.append('Артикул обязателен')
        if not pickup_address:
            errors.append('Адрес пункта выдачи обязателен')
        if not order_date:
            errors.append('Дата заказа обязательна')

        # Проверяем уникальность артикула
        if article and Order.objects.filter(article=article).exists():
            errors.append('Заказ с таким артикулом уже существует')

        if errors:
            return render(request, 'buildmatapp/order_form.html', {
                'order': None,
                'errors': errors,
                'is_admin': True,
                'is_manager': False,
                'user': request.user,
                'is_authenticated': True,
            })

        # Создаём новый заказ
        order = Order.objects.create(
            article=article,
            status=status,
            pickup_address=pickup_address,
            order_date=order_date,
            pickup_date=pickup_date if pickup_date else None,
        )

        return redirect('order_list')

    return render(request, 'buildmatapp/order_form.html', {
        'order': None,
        'errors': [],
        'is_admin': True,
        'is_manager': False,
        'user': request.user,
        'is_authenticated': True,
    })


@login_required
@user_passes_test(is_admin, login_url='order_list')
def order_edit_view(request, order_id):
    """Редактирование заказа (только для администратора)."""
    order = get_object_or_404(Order, id=order_id)

    if request.method == 'POST':
        article = request.POST.get('article', '')
        status = request.POST.get('status', 'pending')
        pickup_address = request.POST.get('pickup_address', '')
        order_date = request.POST.get('order_date', '')
        pickup_date = request.POST.get('pickup_date', '')

        # Валидация данных
        errors = []
        if not article:
            errors.append('Артикул обязателен')
        if not pickup_address:
            errors.append('Адрес пункта выдачи обязателен')
        if not order_date:
            errors.append('Дата заказа обязательна')

        # Проверяем уникальность артикула (исключая текущий заказ)
        if article and Order.objects.filter(article=article).exclude(id=order_id).exists():
            errors.append('Заказ с таким артикулом уже существует')

        if errors:
            return render(request, 'buildmatapp/order_form.html', {
                'order': order,
                'errors': errors,
                'is_admin': True,
                'is_manager': False,
                'user': request.user,
                'is_authenticated': True,
            })

        # Обновляем заказ
        order.article = article
        order.status = status
        order.pickup_address = pickup_address
        order.order_date = order_date
        order.pickup_date = pickup_date if pickup_date else None
        order.save()

        return redirect('order_list')

    return render(request, 'buildmatapp/order_form.html', {
        'order': order,
        'errors': [],
        'is_admin': True,
        'is_manager': False,
        'user': request.user,
        'is_authenticated': True,
    })


@login_required
@user_passes_test(is_admin, login_url='order_list')
def order_delete_view(request, order_id):
    """Удаление заказа (только для администратора)."""
    order = get_object_or_404(Order, id=order_id)
    order.delete()
    return JsonResponse({'success': True})
