from django.db import models
from django.contrib.auth.models import AbstractUser


class Role(models.TextChoices):
    """Роли пользователей."""
    CLIENT = 'client', 'Клиент'
    MANAGER = 'manager', 'Менеджер'
    ADMIN = 'admin', 'Администратор'


class CustomUser(AbstractUser):
    """Пользователь системы."""

    role = models.CharField('Роль', max_length=10, choices=Role.choices, default=Role.CLIENT)

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return f'{self.first_name or ""} {self.last_name or ""} ({self.get_role_display()})'


class Category(models.Model):
    """Категория товара."""

    name = models.CharField('Название', max_length=200, unique=True)
    description = models.TextField('Описание', blank=True)

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'
        ordering = ['name']

    def __str__(self):
        return self.name


class Manufacturer(models.Model):
    """Производитель."""

    name = models.CharField('Название', max_length=200, unique=True)
    country = models.CharField('Страна', max_length=100, blank=True)

    class Meta:
        verbose_name = 'Производитель'
        verbose_name_plural = 'Производители'
        ordering = ['name']

    def __str__(self):
        return self.name


class Supplier(models.Model):
    """Поставщик."""

    name = models.CharField('Название', max_length=200, unique=True)
    contact = models.CharField('Контакт', max_length=200, blank=True)

    class Meta:
        verbose_name = 'Поставщик'
        verbose_name_plural = 'Поставщики'
        ordering = ['name']

    def __str__(self):
        return self.name


class Product(models.Model):
    """Товар — строительный материал."""

    name = models.CharField('Название', max_length=300)
    description = models.TextField('Описание', blank=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='products', verbose_name='Категория')
    manufacturer = models.ForeignKey(Manufacturer, on_delete=models.SET_NULL, null=True, related_name='products', verbose_name='Производитель')
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, related_name='products', verbose_name='Поставщик')
    price = models.DecimalField('Цена', max_digits=10, decimal_places=2)
    discount = models.DecimalField('Скидка %', max_digits=5, decimal_places=2, default=0)
    unit = models.CharField('Единица измерения', max_length=50, default='шт')
    stock_quantity = models.PositiveIntegerField('Количество на складе', default=0)
    image = models.ImageField('Изображение', upload_to='products/', blank=True, null=True)
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True)

    class Meta:
        verbose_name = 'Товар'
        verbose_name_plural = 'Товары'
        ordering = ['name']

    def __str__(self):
        return self.name

    @property
    def final_price(self):
        """Итоговая цена со скидкой."""
        if self.discount:
            return self.price * (1 - self.discount / 100)
        return self.price

    @property
    def is_out_of_stock(self):
        return self.stock_quantity == 0

    @property
    def is_high_discount(self):
        return self.discount > 12


class Material(models.Model):
    """Материал, из которого состоит продукт."""

    name = models.CharField('Название', max_length=200, unique=True)
    unit = models.CharField('Единица измерения', max_length=50, default='шт')

    class Meta:
        verbose_name = 'Материал'
        verbose_name_plural = 'Материалы'
        ordering = ['name']

    def __str__(self):
        return f'{self.name} ({self.unit})'


class ProductMaterial(models.Model):
    """Состав продукта — какие материалы и в каком количестве нужны."""

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='materials', verbose_name='Продукт')
    material = models.ForeignKey(Material, on_delete=models.PROTECT, related_name='in_products', verbose_name='Материал')
    quantity_per_unit = models.DecimalField('Количество на единицу', max_digits=10, decimal_places=2, db_column='quantity_per_unit')

    class Meta:
        verbose_name = 'Расход материала'
        verbose_name_plural = 'Расходы материалов'
        unique_together = ('product', 'material')

    def __str__(self):
        return f'{self.product.name} — {self.material.name}: {self.quantity_per_unit}'


class Order(models.Model):
    """Заказ."""

    class Status(models.TextChoices):
        PENDING = 'pending', 'Ожидает обработки'
        PROCESSING = 'processing', 'В обработке'
        COMPLETED = 'completed', 'Выполнен'
        CANCELLED = 'cancelled', 'Отменён'

    article = models.CharField('Артикул', max_length=50, unique=True)
    status = models.CharField('Статус', max_length=20, choices=Status.choices, default=Status.PENDING)
    pickup_address = models.CharField('Адрес пункта выдачи', max_length=300)
    order_date = models.DateTimeField('Дата заказа')
    pickup_date = models.DateTimeField('Дата выдачи', blank=True, null=True)
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True)

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'
        ordering = ['-order_date']

    def __str__(self):
        return f'Заказ #{self.article}'


class OrderItem(models.Model):
    """Позиция заказа."""

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items', verbose_name='Заказ')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, verbose_name='Товар')
    quantity = models.PositiveIntegerField('Количество', default=1)
    price = models.DecimalField('Цена за единицу', max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = 'Позиция заказа'
        verbose_name_plural = 'Позиции заказа'

    def __str__(self):
        return f'{self.product.name} x {self.quantity}'
