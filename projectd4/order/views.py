from django.shortcuts import render,get_object_or_404, HttpResponseRedirect
from django.db.models import Sum
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from decimal import Decimal
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin,UserPassesTestMixin
from .models import Products,User,Category,Order,Customer,Cart, CartItem,OrderItem
from django.views.generic import ListView,DetailView,CreateView,UpdateView,DeleteView
from django.contrib.auth.decorators import login_required
from .forms import VendorSignUpForm,CustomerSignUpForm
from django.shortcuts import redirect, render
from django.views.generic import TemplateView
from django.utils.decorators import method_decorator
from .decorators import vendor_required,customer_required
from django.views import View
from django.urls import reverse
import datetime
from mailjet_rest import Client
from django.conf import settings
from django.contrib.auth import authenticate, login


class SignUpView(TemplateView):
    template_name = 'order/signup.html'


def home(request):

    if request.user.is_authenticated:
        if request.user.is_vendor:
            return redirect('order_vend')
        elif request.user.is_customer:
            return redirect('store')
    else:
        user = authenticate(request, backend='django.contrib.auth.backends.ModelBackend')
        if user is not None:
            login(request, user)
            if user.is_vendor:
                return redirect('order_vend')
            elif user.is_customer:
                return redirect('store')
        return render(request, 'order/home.html')


class VendorSignUpView(CreateView):
    model = User
    form_class = VendorSignUpForm
    template_name = 'order/signup_form.html'

    def get_context_data(self, **kwargs):
        kwargs['user_type'] = 'vendor'
        return super().get_context_data(**kwargs)

    def form_valid(self, form):
        user = form.save()
        authenticated_user = authenticate(self.request, username=user.username, password=form.cleaned_data['password1'])
        login(self.request, authenticated_user)
        return redirect('order_vend')

class CustomerSignUpView(CreateView):
    model = User
    form_class = CustomerSignUpForm
    template_name = 'order/signup_form.html'

    def get_context_data(self, **kwargs):
        kwargs['user_type'] = 'customer'
        return super().get_context_data(**kwargs)

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        return redirect('store')


@method_decorator([login_required, vendor_required], name='dispatch')
class PostListView(ListView):
    model=Products
    template_name = 'order/odr.html'    # <app>/<model>_<viewtype>.html
    context_object_name = 'orde'
    #ordering = ['-date_posted']

@method_decorator([login_required, vendor_required], name='dispatch')
class PostCreateView(LoginRequiredMixin, CreateView):
    model =Products
    fields=['Name', 'Price','Description','Quantity','Image','category','slug']

    def form_valid(self, form):
         form.instance.author=self.request.user
         return super().form_valid(form)

@method_decorator([login_required, vendor_required], name='dispatch')
class PostDetailView(DetailView):
        model = Products

@method_decorator([login_required, vendor_required], name='dispatch')
class PostDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Products
    success_url = '/'

    def test_func(self):
        post = self.get_object()
        if self.request.user == post.author:
            return True
        return False

@method_decorator([login_required, vendor_required], name='dispatch')
class PostUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Products
    fields = ['Name', 'Price','Description','Quantity','Image','category','slug']

    def form_valid(self, form):
         form.instance.author=self.request.user
         return super().form_valid(form)

    def test_func(self):
        post=self.get_object()
        if self.request.user==post.author:
            return True
        return False

@method_decorator([login_required, customer_required], name='dispatch')
class Index(View):
    def get(self , request):
        return HttpResponseRedirect(f'/store{request.get_full_path()[1:]}')

def store(request):
    cart = request.session.get('cart')
    if not cart:
        request.session['cart'] = {}
    products = None
    categories = Category.get_all_categories()
    categoryID = request.GET.get('category')
    if categoryID:
        products = Products.get_all_products_by_categoryid(categoryID)
    else:
        products = Products.get_all_products();

    data={}
    data['products'] = products
    data['categories'] = categories

    print('you are : ', request.session.get('email'))
    return render(request, 'order/index.html', data)



def get_user_cart(request):
    """Retrieves the shopping cart for the current user."""
    cart_id = None
    cart = None
    if request.user.is_authenticated and not request.user.is_anonymous:
        try:
            cart = Cart.objects.get(user=request.user)
        except ObjectDoesNotExist:
            cart = Cart(user=request.user)
            cart.save()
    else:
        cart_id = request.session.get('cart_id')
        if not cart_id:
            cart = Cart()
            cart.save()
            request.session['cart_id'] = cart.id
        else:
            cart = Cart.objects.get(id=cart_id)
    return cart


def get_cart_count(request):
    cart = get_user_cart(request)
    total_count = 0
    cart_items = CartItem.objects.filter(cart=cart)
    for item in cart_items:
        total_count += item.quantity
    return total_count


def update_cart_info(request):
    request.session['cart_count'] = get_cart_count(request)

def custom_update(request):
    customer=Customer.objects.get(user=request.user)
    request.session['customer'] = customer


def view_cart(request):
    cart = get_user_cart(request)
    custom_update(request)
    cart_items = CartItem.objects.filter(cart=cart)
    order_total = Decimal(0.0)
    customer=request.session['customer']
    for item in cart_items:
        order_total += (item.product.Price * item.quantity)
    context = {
        'cart_items': cart_items,
        'order_total':order_total,
        'customer':customer,
    }
    return render(request,'order/view_cart.html', context)


def add_to_cart(request, slug):
    if request.POST:
        cart = get_user_cart(request)
        product = Products.objects.get(slug=slug)
        quantity = int(request.POST.get('qty')) or 1
        cart_item = CartItem(product=product, cart=cart, quantity=0)
        if quantity <= product.Quantity:
            cart_item.quantity += quantity
            cart.user = request.user
            cart_item.save()
        elif product.Quantity==0:
            messages.error(request, "Sorry, the item is currently out of stock.")
        elif quantity>product.Quantity:
            cart_item.quantity = product.Quantity
            cart.user = request.user
            cart_item.save()
            messages.error(request, "Sorry, more items selected than in stock.")
        if request.session.get('cart_count'):
            request.session['cart_count'] += quantity
        else:
            request.session['cart_count'] = quantity
        update_cart_info(request)
        return redirect(reverse('view_cart'))


def remove_from_cart(request, id):
    if request.POST:
        cart_item = CartItem.objects.get(id=id)
        quantity = cart_item.quantity
        cart_item.delete()
        if request.session.get('cart_count'):
            request.session['cart_count'] -= quantity
        else:
            request.session['cart_count'] = 0
        update_cart_info(request)
        return redirect(reverse('view_cart'))

def all(request):
    all_products = Products.objects.all()
    context = {
        'all_products': all_products
    }
    return render(request,'order/all.html',context )

def home2(request):
    return render(request,'order/home.html')

def detail(request, slug):

    product = Products.objects.get(slug=slug)
    context={'product':product}
    return render(request,'order/detail.html',context)

def orders(request):
    order=Order.objects.get(user=request.user)
    orders = OrderItem.objects.filter(order=order)
    context = {'orders':orders}
    template = 'order/orders2.html'
    return render(request, template, context)


def cartData(request,no):
    if request.method == "POST":
            cart_item = CartItem.objects.get(id=no)
            Iden=cart_item.id
            quantity = cart_item.quantity
            product=cart_item.product
            request.session['cartdata'] = {'cartItem':cart_item, 'quantity':quantity, 'product':product,'Iden':Iden}
            return redirect("view_cart")
    else:
        return redirect("homepage")


def send_vendor_notification(vendor_email, customer_name):
    mailjet = Client(
        auth=(settings.MAILJET_API_KEY, settings.MAILJET_API_SECRET),
        version='v3.1'
    )

    data = {
        'Messages': [
            {
                'From': {
                    'Email': 'your-email@example.com',
                    'Name': 'Your Name'
                },
                'To': [
                    {
                        'Email': vendor_email,
                        'Name': 'Vendor Name'
                    }
                ],
                'Subject': 'New Purchase Notification',
                'TextPart': f'You have received a new purchase from {customer_name}.',
                'HTMLPart': f'<p>You have received a new purchase from {customer_name}.</p>'
            }
        ]
    }

    result = mailjet.send.create(data=data)
    if result.status_code == 200:
        print('Notification email sent successfully')
    else:
        print('Failed to send notification email')


def checkout4(request):
    data = request.session.get('cartdata')
    product =data['product']
    quantity = data['quantity']
    Iden=data['Iden']
    custom_update(request)
    Customer=request.session['customer']
    if request.method == "POST":
        if Customer.balance >= ((product.Price)*(quantity)):
            sum=0
            address = request.POST.get("address")
            email = request.POST.get("email")
            order = Order(user=request.user, product=product, price=(product.Price)*(quantity), address=address,
                              email=email, quantity=quantity,created_at=datetime.datetime.now())
            order.save()
            item = OrderItem.objects.create(order=order, product=product, price=(product.Price)*(quantity), quantity=quantity)
            no = Iden
            remove_from_cart(request, no)
            product.Quantity=product.Quantity-quantity
            product.Sum=product.Sum+item.price
            product.save()
            Customer.balance-=item.price
            Customer.save()
            vendor=product.author
            vendor_email=vendor.email
            customer_name=Customer.name
            send_vendor_notification(vendor_email, customer_name)
            return redirect("view_cart")
        else:
            messages.error(request, "Sorry, Balance left is less than required to place Order.")
            return redirect("view_cart")

    else:
        return render(request, 'order/checkout3.html')


@method_decorator([login_required, vendor_required], name='dispatch')
class OrderListView(ListView):
    model=OrderItem
    template_name = 'order/odr1.html'    # <app>/<model>_<viewtype>.html
    context_object_name = 'orde'

def Vendororders(request):
  products=Products.objects.filter(author=request.user).order_by('-Sum')
  context={'orde':products}
  return render(request,'order/odr2.html',context)

def Orders_List(request):
  products=Products.objects.all().order_by('-Sum')
  context={'orde':products}
  return render(request,'order/odr2.html',context)


def get_orders_by_product():
    orders = OrderItem.objects.values('product').annotate(total_quantity=Sum('quantity'))
    return orders

def my_view(request):
    orders = get_orders_by_product()
    context={'orde':orders}
    return render(request, 'order/odr3.html',context)

def OrderHierarchy(request):
    orders = OrderItem.objects.values('product').annotate(total_quantity=Sum('quantity'))
    products=Products.filter(author=request.user)
    for product in products:
        order=orders.filter(product=product)
        product.Sum=order.total_quantity
        product.save()

def add_money(request):
    if request.method == 'POST':
        amount = int(request.POST.get('amount'))
        customer = Customer.objects.get(user=request.user)
        customer.balance += amount
        customer.save()
        return redirect('homepage')  # Redirect to account details page after adding money
    else:
        return render(request, 'order/add_money.html')




