from django.urls import path,re_path
from django.urls import path, include,re_path
from .views import OrderListView,PostListView,PostCreateView,PostDetailView,PostDeleteView,PostUpdateView,SignUpView,VendorSignUpView,CustomerSignUpView,Index,store,home,Cart,add_to_cart
from . import views
from django.views.generic import TemplateView

urlpatterns = [
    path('', home, name='home'),
    path('v/', PostListView.as_view(), name='order_pg'),
    path('v/post/<int:pk>/', PostDetailView.as_view(), name='post-detail'),
    path('v/post/new/', PostCreateView.as_view(), name='post-create'),path('v/post/<int:pk>/delete/', PostDeleteView.as_view(), name='post-delete'),
    path('v/post/<int:pk>/update/', PostUpdateView.as_view(), name='post-update'),
    path('', Index.as_view(), name='homepage'),
    path('store', store, name='store'),
    path('cus/', views.home2, name='home2'),
    path('products/(<slug>', views.add_to_cart, name='add_to_cart'),
    path('products/<id>', views.remove_from_cart,
        name='remove_from_cart'),
    path('products/', views.all, name='all'),
    path('product/<slug>', views.detail, name='detail'),
    path('cart/', views.view_cart, name='view_cart'),
    path('checkout3/', views.checkout4, name="checkout3"),
    path('Checkout/<no>', views.cartData, name='Checkout'),
    path('Vendr/', OrderListView.as_view(), name='order_vend'),
    re_path(r'^orders/', views.orders, name='orders'),
    path('add-money/', views.add_money, name='add_money'),
    re_path(r'^Vendororders/', views.Vendororders, name='Vendororders'),
    path('orderslist/', views.Orders_List, name='OrderL'),
    path('', TemplateView.as_view(template_name="order/Index2.html")),
    path('accounts/', include('allauth.urls')),
    path('accounts/', include('django.contrib.auth.urls')),
    path('accounts2/signup/', SignUpView.as_view(), name='signup'),
    path('accounts2/signup/vendor/', VendorSignUpView.as_view(), name='vendor_signup'),
    path('accounts2/signup/customer/', CustomerSignUpView.as_view(), name='customer_signup'),
    ]
