from django.db import models
from django.urls import reverse
from django.contrib.auth.models import AbstractUser
from django.utils.html import escape, mark_safe
import datetime

class User(AbstractUser):
    is_customer = models.BooleanField(default=False)
    is_vendor = models.BooleanField(default=False)
    email = models.EmailField()


class Category(models.Model):
    name= models.CharField(max_length=50)

    @staticmethod
    def get_all_categories():
        return Category.objects.all()

    def __str__(self):
        return self.name

class Products(models.Model):
    Name=models.CharField(max_length=100)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    Description = models.CharField(max_length=250, default='', blank=True, null=True)
    Quantity = models.IntegerField(default=1)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, default=1)
    Image = models.ImageField(blank=True,null=True)
    Price = models.IntegerField(default=0)
    slug = models.SlugField(unique=True)
    active = models.BooleanField(default=True)
    Sum = models.IntegerField(default=0)

    def __str__(self):
        return self.Name

    def get_absolute_url(self):
        return reverse('post-detail',kwargs={'pk':self.pk})

    @staticmethod
    def get_products_by_id(ids):
        return Products.objects.filter(id__in=ids)

    @staticmethod
    def get_all_products():
        return Products.objects.all()

    @staticmethod
    def get_all_products_by_categoryid(category_id):
        if category_id:
            return Products.objects.filter(category=category_id)
        else:
            return Products.get_all_products();

    @property
    def imageURL(self):
        try:
            url = self.image.url
        except:
            url = ''
        return url

class Customer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    name = models.CharField(max_length=50)
    email=models.EmailField()
    balance = models.IntegerField(default=0)

    #to save the data
    def register(self):
        self.save()


    @staticmethod
    def get_customer_by_email(email):
        try:
            return Customer.objects.get(email= email)
        except:
            return False


    def isExists(self):
        if Customer.objects.filter(email = self.email):
            return True

        return False

    def __str__(self):
        return self.user.name

class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    created_at = models.DateTimeField(auto_now_add=True, auto_now=False)
    updated_at = models.DateTimeField(auto_now_add=False, auto_now=True)
    active = models.BooleanField(default=True)

    def __unicode__(self):
        return 'Cart #' + unicode(self.id)


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, null=True, blank=True,on_delete=models.CASCADE)
    product = models.ForeignKey(Products,on_delete=models.CASCADE)
    quantity = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True, auto_now=False)
    updated_at = models.DateTimeField(auto_now_add=False, auto_now=True)
    active = models.BooleanField(default=True)

    def __unicode__(self):
        return 'Order #' + unicode(self.id) + ' of ' + self.product.Name

ORDER_STATUS = (
    ('started', 'Started'),
    ('abandoned', 'Abandoned'),
    ('finished', 'Finished'),
)

class Order(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    product = models.ForeignKey(Products,
                                on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    price = models.IntegerField()
    address = models.CharField (max_length=50, default='', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=255, choices=ORDER_STATUS, default='started')
    email = models.EmailField()

    def placeOrder(self):
        self.save()

    @staticmethod
    def get_orders_by_customer(customer_id):
        return Order.objects.filter(customer=customer_id).order_by('-date')

    def __unicode__(self):
        return '<Order:' + self.order_id + '> ' + self.status + ' | ' + unicode(self.created_at)

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Products, related_name='items', on_delete=models.CASCADE)
    price = models.IntegerField()
    quantity = models.IntegerField(default=1)







