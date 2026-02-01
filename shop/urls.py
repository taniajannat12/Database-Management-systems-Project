# shop/urls.py - COMPLETE CORRECT VERSION
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    path('', views.home, name='dashboard'),
    
   
    path('skin/', views.skin, name='skin'),
    path('hair/', views.hair, name='hair'), 
    path('makeup/', views.makeup, name='makeup'),
    path('cart/', views.view_cart, name='cart'),
    path('add-to-cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('remove-cart-item/<int:item_id>/', views.remove_from_cart, name='remove_cart_item'),
    path('checkout/', views.checkout, name='checkout'),
    path('orders/', views.order_history, name='orders'),
    path('login/', views.login, name='login'),
    path('signup/', views.signup, name='signup'),
    path('logout/', views.logout, name='logout'),
    path('contact/', views.contact, name='contact'),

    # Admin URLs
    path('manage/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('manage/products/', views.admin_products, name='admin_products'),
    path('manage/products/add/', views.admin_add_product, name='admin_add_product'),
    path('manage/products/edit/<int:product_id>/', views.admin_edit_product, name='admin_edit_product'),
    path('manage/products/delete/<int:product_id>/', views.admin_delete_product, name='admin_delete_product'),
    path('manage/products/stock/<int:product_id>/', views.admin_update_stock, name='admin_update_stock'),
    path('manage/orders/', views.admin_orders, name='admin_orders'),
    path('manage/orders/status/<int:order_id>/', views.admin_update_order_status, name='admin_update_order_status'),
    path('manage/user-activities/', views.admin_user_activities, name='admin_user_activities'),
]

# ✅ FIXED: Media files serving for development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)