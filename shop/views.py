from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import connection, transaction
from django.http import HttpResponse
import os
from django.conf import settings

# Helper function: SQL query execute
def execute_sql_query(query, params=None):
    with connection.cursor() as cursor:
        cursor.execute(query, params or [])    # run sql query
        if query.strip().upper().startswith('SELECT'):
            columns = [col[0] for col in cursor.description]
            results = []
            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))
            return results
        return cursor.rowcount

# Helper function: Single row fetch
def execute_sql_single(query, params=None):
    with connection.cursor() as cursor:
        cursor.execute(query, params or [])
        row = cursor.fetchone()
        if row:
            columns = [col[0] for col in cursor.description]
            return dict(zip(columns, row))
        return None

# Custom Admin Check Function
def is_admin_user(user_id):
    """SQL দিয়ে check করে user admin কি না"""
    query = "SELECT is_staff, is_superuser FROM auth_user WHERE id = %s"
    result = execute_sql_single(query, [user_id])
    return result and (result['is_staff'] or result['is_superuser'])

# ========================
# PRODUCT PAGES - SQL দিয়ে
# ========================

def home(request):
    """Home Page - Featured Products"""
    query = """
        SELECT id, name, price, description, stock, image_url
        FROM shop_product 
        WHERE available = 1 
        ORDER BY id DESC 
        LIMIT 12
    """
    products = execute_sql_query(query)
    
    categories_query = "SELECT id, name FROM shop_category"
    categories = execute_sql_query(categories_query)
    
    return render(request, 'shop/dashboard.html', {
        'products': products, 
        'categories': categories
    })

def skin_care(request):
    """Skin Care Products Page"""
    query = """
        SELECT id, name, price, description, stock, image_url
        FROM shop_product 
        WHERE category_id = 1 AND available = 1 
        ORDER BY id DESC
    """
    products = execute_sql_query(query)
    return render(request, 'shop/skin.html', {'products': products})

def makeup(request):
    """Makeup Products Page"""
    query = """
        SELECT id, name, price, description, stock, image_url 
        FROM shop_product 
        WHERE category_id = 2 AND available = 1 
        ORDER BY id DESC
    """
    products = execute_sql_query(query)
    return render(request, 'shop/makeup.html', {'products': products})

def hair_care(request):
    """Hair Care Products Page"""
    query = """
        SELECT id, name, price, description, stock, image_url
        FROM shop_product 
        WHERE category_id = 3 AND available = 1 
        ORDER BY id DESC
    """
    products = execute_sql_query(query)
    return render(request, 'shop/hair.html', {'products': products})

# ========================
# CART SYSTEM - SQL 
# ========================

@login_required
def add_to_cart(request, product_id):
    """Add product to cart using SQL"""
    try:
        # Check if product exists
        product_query = "SELECT id, name, price FROM shop_product WHERE id = %s AND available = 1"
        product = execute_sql_single(product_query, [product_id])
        
        if not product:
            messages.error(request, "Product not found!")
            return redirect('dashboard')
        
        # Get or create user's cart
        cart_query = "SELECT id FROM shop_cart WHERE user_id = %s"
        cart = execute_sql_single(cart_query, [request.user.id])
        
        if not cart:
            create_cart_query = "INSERT INTO shop_cart (user_id) VALUES (%s)"
            execute_sql_query(create_cart_query, [request.user.id])
            cart = execute_sql_single(cart_query, [request.user.id])
        
        # Check if product already in cart
        cart_item_query = "SELECT id, quantity FROM shop_cartitem WHERE cart_id = %s AND product_id = %s"
        cart_item = execute_sql_single(cart_item_query, [cart['id'], product_id])
        
        if cart_item:
            # Update quantity
            update_query = "UPDATE shop_cartitem SET quantity = quantity + 1 WHERE id = %s"
            execute_sql_query(update_query, [cart_item['id']])
            messages.success(request, f"{product['name']} quantity updated in cart!")
        else:
            # Add new item
            insert_query = "INSERT INTO shop_cartitem (cart_id, product_id, quantity) VALUES (%s, %s, 1)"
            execute_sql_query(insert_query, [cart['id'], product_id])
            messages.success(request, f"{product['name']} added to cart!")
        
        return redirect('cart')
        
    except Exception as e:
        messages.error(request, "Error adding product to cart!")
        return redirect('dashboard')

@login_required
def view_cart(request):
    """View cart items using SQL"""
    try:
        cart_items_query = """
            SELECT 
                ci.id,
                ci.quantity,
                p.id as product_id,
                p.name as product_name,
                p.price,
                p.stock,
                p.image_url, 
                (ci.quantity * p.price) as item_total
            FROM shop_cartitem ci
            JOIN shop_product p ON ci.product_id = p.id
            JOIN shop_cart c ON ci.cart_id = c.id
            WHERE c.user_id = %s
        """
        cart_items = execute_sql_query(cart_items_query, [request.user.id])
        
        total_query = """
            SELECT SUM(ci.quantity * p.price) as total
            FROM shop_cartitem ci
            JOIN shop_product p ON ci.product_id = p.id
            JOIN shop_cart c ON ci.cart_id = c.id
            WHERE c.user_id = %s
        """
        total_result = execute_sql_single(total_query, [request.user.id])
        total = total_result['total'] if total_result and total_result['total'] else 0
        
        return render(request, 'shop/cart.html', {
            'cart_items': cart_items,
            'total': total
        })
        
    except Exception as e:
        return render(request, 'shop/cart.html', {'cart_items': [], 'total': 0})

@login_required
def remove_from_cart(request, item_id):
    """Remove item from cart using SQL"""
    try:
        delete_query = "DELETE FROM shop_cartitem WHERE id = %s"
        execute_sql_query(delete_query, [item_id])
        messages.success(request, "Item removed from cart!")
    except Exception as e:
        messages.error(request, "Error removing item from cart!")
    
    return redirect('cart')

# ========================
# ORDER SYSTEM - SQL 
# ========================

@login_required
def checkout(request):
    """Checkout and create order using SQL"""
    try:
        # Get cart items
        cart_items_query = """
            SELECT 
                ci.id,
                ci.quantity,
                p.id as product_id,
                p.name,
                p.price,
                p.image_url, 
                (ci.quantity * p.price) as item_total
            FROM shop_cartitem ci
            JOIN shop_product p ON ci.product_id = p.id
            JOIN shop_cart c ON ci.cart_id = c.id
            WHERE c.user_id = %s
        """
        cart_items = execute_sql_query(cart_items_query, [request.user.id])
        
        if not cart_items:
            messages.error(request, "Your cart is empty!")
            return redirect('cart')
        
        if request.method == 'POST':
            address = request.POST.get('address', '').strip()
            phone = request.POST.get('phone', '').strip()
            
            if not address:
                messages.error(request, "Please enter delivery address!")
                return redirect('checkout')
            
            with transaction.atomic():
                # Calculate total
                total_query = """
                    SELECT SUM(ci.quantity * p.price) as total
                    FROM shop_cartitem ci
                    JOIN shop_product p ON ci.product_id = p.id
                    JOIN shop_cart c ON ci.cart_id = c.id
                    WHERE c.user_id = %s
                """
                total_result = execute_sql_single(total_query, [request.user.id])
                total_amount = total_result['total'] if total_result else 0
                
                # Create order
                order_query = """
                    INSERT INTO shop_order (user_id, total_amount, status, delivery_address, phone_number)
                    VALUES (%s, %s, 'pending', %s, %s)
                """
                execute_sql_query(order_query, [request.user.id, total_amount, address, phone])
                
                # Get order ID
                order_id_query = "SELECT LAST_INSERT_ID() as order_id"
                order_result = execute_sql_single(order_id_query)
                order_id = order_result['order_id']
                
                # Add order items
                order_items_query = """
                    INSERT INTO shop_orderitem (order_id, product_id, quantity, price)
                    SELECT %s, p.id, ci.quantity, p.price
                    FROM shop_cartitem ci
                    JOIN shop_product p ON ci.product_id = p.id
                    JOIN shop_cart c ON ci.cart_id = c.id
                    WHERE c.user_id = %s
                """
                execute_sql_query(order_items_query, [order_id, request.user.id])
                
                # Update stock
                update_stock_query = """
                    UPDATE shop_product p
                    JOIN shop_cartitem ci ON p.id = ci.product_id
                    JOIN shop_cart c ON ci.cart_id = c.id
                    SET p.stock = p.stock - ci.quantity
                    WHERE c.user_id = %s
                """
                execute_sql_query(update_stock_query, [request.user.id])
                
                # Clear cart
                clear_cart_query = """
                    DELETE ci FROM shop_cartitem ci
                    JOIN shop_cart c ON ci.cart_id = c.id
                    WHERE c.user_id = %s
                """
                execute_sql_query(clear_cart_query, [request.user.id])
            
            messages.success(request, f"Order #{order_id} placed successfully! Total: ${total_amount}")
            return redirect('orders')
        
        # Calculate total for display
        total_query = """
            SELECT SUM(ci.quantity * p.price) as total
            FROM shop_cartitem ci
            JOIN shop_product p ON ci.product_id = p.id
            JOIN shop_cart c ON ci.cart_id = c.id
            WHERE c.user_id = %s
        """
        total_result = execute_sql_single(total_query, [request.user.id])
        total = total_result['total'] if total_result else 0
        
        return render(request, 'shop/checkout.html', {
            'cart_items': cart_items,
            'total': total
        })
        
    except Exception as e:
        messages.error(request, "Checkout error occurred!")
        return redirect('cart')

@login_required
def order_history(request):
    """View order history using SQL"""
    try:
        orders_query = """
            SELECT 
                id, total_amount, status, delivery_address, phone_number, created_at
            FROM shop_order 
            WHERE user_id = %s
            ORDER BY created_at DESC
        """
        orders = execute_sql_query(orders_query, [request.user.id])
        
        orders_with_items = []
        for order in orders:
            order_items_query = """
                SELECT 
                    oi.quantity, oi.price, p.name as product_name,
                    (oi.quantity * oi.price) as item_total
                FROM shop_orderitem oi
                JOIN shop_product p ON oi.product_id = p.id
                WHERE oi.order_id = %s
            """
            items = execute_sql_query(order_items_query, [order['id']])
            orders_with_items.append({
                'order': order,
                'items': items
            })
        
        return render(request, 'shop/orders.html', {
            'orders_with_items': orders_with_items
        })
    except Exception as e:
        return render(request, 'shop/orders.html', {'orders_with_items': []})

# ========================
# AUTHENTICATION
# ========================

def signup(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')
        
        if not name or not email or not password:
            messages.error(request, 'All fields are required!')
            return render(request, 'shop/login.html', {'form_type': 'signup'})
        
        if password != confirm_password:
            messages.error(request, 'Passwords do not match!')
            return render(request, 'shop/login.html', {'form_type': 'signup'})
        
        if User.objects.filter(username=email).exists():
            messages.error(request, 'User with this email already exists!')
            return render(request, 'shop/login.html', {'form_type': 'signup'})
            
        try:
            user = User.objects.create_user(
                username=email,
                email=email,
                password=password,
                first_name=name
            )
            
            auth_login(request, user)
            messages.success(request, f'Welcome {name}! Your account has been created successfully.')
            return redirect('dashboard')
            
        except Exception as e:
            messages.error(request, "Error creating account. Please try again.")
            return render(request, 'shop/login.html', {'form_type': 'signup'})
        
    return render(request, 'shop/login.html', {'form_type': 'signup'})

def login(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        
        print(f"DEBUG: Login attempt - Email: {email}, Password: {password}")
        
        if not email or not password:
            messages.error(request, 'Please enter both email and password!')
            return render(request, 'shop/login.html', {'form_type': 'login'})
        
        # Try multiple authentication methods
        user = None
        
        # Method 1: Try with email as username
        user = authenticate(request, username=email, password=password)
        
        # Method 2: If that fails, try to find by actual email
        if user is None and '@' in email:
            try:
                user_obj = User.objects.get(email=email)
                user = authenticate(request, username=user_obj.username, password=password)
            except User.DoesNotExist:
                pass
        
        if user is not None:
            auth_login(request, user)
            messages.success(request, f'Welcome back, {user.first_name}!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid email or password!')
    
    return render(request, 'shop/login.html', {'form_type': 'login'})

def logout(request):
    auth_logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('login')

def contact(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        message_text = request.POST.get('message')

        if not name or not email or not message_text:
            messages.error(request, "All fields are required!")
            return redirect('contact')

        contact_query = """
            INSERT INTO shop_contactmessage (name, email, message, created_at)
            VALUES (%s, %s, %s, NOW())
        """
        execute_sql_query(contact_query, [name, email, message_text])
        
        messages.success(request, f"Thank you {name}, your message has been received!")
        return redirect('contact')

    return render(request, 'shop/contact.html')

# ========================
# ADMIN FUNCTIONS - SQL 
# ========================

@login_required
def admin_dashboard(request):
    """Admin Dashboard"""
    if not is_admin_user(request.user.id):
        messages.error(request, "Access denied! Admin permission required.")
        return redirect('dashboard')
    
    try:
        sales_query = "SELECT SUM(total_amount) as total_sales FROM shop_order"
        total_sales = execute_sql_single(sales_query)
        
        products_query = "SELECT COUNT(*) as total_products FROM shop_product"
        total_products = execute_sql_single(products_query)
        
        orders_query = "SELECT COUNT(*) as total_orders FROM shop_order"
        total_orders = execute_sql_single(orders_query)
        
        users_query = "SELECT COUNT(*) as total_users FROM auth_user"
        total_users = execute_sql_single(users_query)
        
        return render(request, 'shop/admin/dashboard.html', {
            'total_sales': total_sales['total_sales'] or 0,
            'total_products': total_products['total_products'],
            'total_orders': total_orders['total_orders'],
            'total_users': total_users['total_users'],
        })
        
    except Exception as e:
        return render(request, 'shop/admin/dashboard.html')
@login_required
def admin_products(request):
    """Admin product management"""
    if not is_admin_user(request.user.id):
        messages.error(request, "Access denied! Admin permission required.")
        return redirect('dashboard')
    
    try:
        # ✅ FIXED: Only show available products
        products_query = """
            SELECT p.*, c.name as category_name
            FROM shop_product p
            JOIN shop_category c ON p.category_id = c.id
            WHERE p.available = 1  # ✅ THIS LINE IS CRITICAL
            ORDER BY p.id DESC
        """
        products = execute_sql_query(products_query)
        
        categories_query = "SELECT id, name FROM shop_category"
        categories = execute_sql_query(categories_query)
        
        print(f"🔍 DEBUG: Loaded {len(products)} AVAILABLE products")
        
        return render(request, 'shop/admin/products.html', {
            'products': products,
            'categories': categories
        })
    except Exception as e:
        print(f"❌ ERROR in admin_products: {e}")
        return render(request, 'shop/admin/products.html', {'products': []})
@login_required
def admin_add_product(request):
    """Add new product with image - FIXED VERSION"""
    if not is_admin_user(request.user.id):
        messages.error(request, "Access denied! Admin permission required.")
        return redirect('dashboard')
    
    if request.method == 'POST':
        try:
            name = request.POST.get('name')
            price = request.POST.get('price')
            description = request.POST.get('description')
            category_id = request.POST.get('category_id')
            stock = request.POST.get('stock')
            
            if not name or not price:
                messages.error(request, 'Product name and price are required!')
                return redirect('admin_products')
            
            # ✅ FIXED: Image handling
            image_url = ""
            if 'image' in request.FILES:
                image_file = request.FILES['image']
                
                # Create media/products directory if not exists
                media_dir = os.path.join(settings.MEDIA_ROOT, 'products')
                os.makedirs(media_dir, exist_ok=True)
                
                # Generate unique filename
                file_extension = os.path.splitext(image_file.name)[1]
                unique_filename = f"{name.replace(' ', '_')}_{int(timezone.now().timestamp())}{file_extension}"
                
                # Save file
                file_path = os.path.join(media_dir, unique_filename)
                with open(file_path, 'wb+') as destination:
                    for chunk in image_file.chunks():
                        destination.write(chunk)
                
                # ✅ FIXED: Store only the relative path (without /media/)
                image_url = f"products/{unique_filename}"
                print(f"✅ DEBUG: Image saved at: {file_path}")
                print(f"✅ DEBUG: Image URL in DB: {image_url}")
            
            insert_query = """
                INSERT INTO shop_product 
                (name, price, description, category_id, stock, available, image_url) 
                VALUES (%s, %s, %s, %s, %s, 1, %s)
            """
            execute_sql_query(insert_query, [
                name, float(price), description, 
                int(category_id), int(stock), image_url
            ])
            
            messages.success(request, f'✅ Product "{name}" added successfully!')
            return redirect('admin_products')
            
        except Exception as e:
            messages.error(request, f'Error adding product: {str(e)}')
            print(f"❌ ERROR: {str(e)}")
            return redirect('admin_products')
    
    else:
        return redirect('admin_products')
from django.utils import timezone
from django.core.files.storage import FileSystemStorage
import os

# ... existing imports ...



# ... existing code ...

@login_required
def admin_edit_product(request, product_id):
    """Edit product - FIXED VERSION"""
    print(f"🔄 DEBUG: admin_edit_product called, product_id: {product_id}")
    
    if not is_admin_user(request.user.id):
        messages.error(request, "Access denied! Admin permission required.")
        return redirect('dashboard')
    
    if request.method == 'POST':
        print(f"🔄 DEBUG: POST data: {dict(request.POST)}")
        print(f"🔄 DEBUG: FILES: {dict(request.FILES)}")
        
        try:
            name = request.POST.get('name', '').strip()
            price = request.POST.get('price', '0').strip()
            description = request.POST.get('description', '').strip()
            category_id = request.POST.get('category_id', '0').strip()
            stock = request.POST.get('stock', '0').strip()
            
            # ✅ FIX: Proper checkbox handling
            available = 1 if request.POST.get('available') == 'on' else 0
            
            # ✅ FIX: Validate required fields
            if not name or not price or price == '0':
                messages.error(request, 'Product name and valid price are required!')
                return redirect('admin_products')
            
            # Get current product info
            current_product_query = "SELECT image_url FROM shop_product WHERE id = %s"
            current_product = execute_sql_single(current_product_query, [product_id])
            current_image_url = current_product['image_url'] if current_product else None
            
            image_url = current_image_url
            
            # Check if new image is uploaded
            if 'image' in request.FILES and request.FILES['image']:
                image_file = request.FILES['image']
                
                # Create media directory if not exists
                media_dir = os.path.join(settings.MEDIA_ROOT, 'products')
                os.makedirs(media_dir, exist_ok=True)
                
                # Generate unique filename
                file_extension = os.path.splitext(image_file.name)[1]
                unique_filename = f"{name.replace(' ', '_')}_{int(timezone.now().timestamp())}{file_extension}"
                
                # Save file
                file_path = os.path.join(media_dir, unique_filename)
                with open(file_path, 'wb+') as destination:
                    for chunk in image_file.chunks():
                        destination.write(chunk)
                
                image_url = f"products/{unique_filename}"
                print(f"✅ DEBUG: New image saved: {image_url}")
            
            # Update product
            update_query = """
                UPDATE shop_product 
                SET name = %s, price = %s, description = %s, 
                    category_id = %s, stock = %s, available = %s,
                    image_url = %s
                WHERE id = %s
            """
            execute_sql_query(update_query, [
                name, float(price), description, 
                int(category_id), int(stock), available,
                image_url, product_id
            ])
            
            messages.success(request, f'✅ Product "{name}" updated successfully!')
            print(f"✅ DEBUG: Product {product_id} updated successfully")
            return redirect('admin_products')
            
        except Exception as e:
            messages.error(request, f'❌ Error updating product: {str(e)}')
            print(f"❌ ERROR in admin_edit_product: {e}")
            import traceback
            traceback.print_exc()
            return redirect('admin_products')
    
    else:
        # GET request - show edit form
        try:
            product_query = """
                SELECT p.*, c.name as category_name 
                FROM shop_product p 
                LEFT JOIN shop_category c ON p.category_id = c.id 
                WHERE p.id = %s
            """
            product = execute_sql_single(product_query, [product_id])
            
            if not product:
                messages.error(request, "Product not found!")
                return redirect('admin_products')
            
            categories_query = "SELECT id, name FROM shop_category ORDER BY name"
            categories = execute_sql_query(categories_query)
            
            print(f"✅ DEBUG: Loading edit form for product: {product['name']}")
            
            return render(request, 'shop/admin/edit_product.html', {
                'product': product,
                'categories': categories
            })
            
        except Exception as e:
            messages.error(request, f"Error loading product: {str(e)}")
            return redirect('admin_products')


@login_required
def admin_update_stock(request, product_id):
    """Update product stock - FIXED VERSION"""
    print(f"🔄 DEBUG: admin_update_stock called, product_id: {product_id}")
    
    if not is_admin_user(request.user.id):
        messages.error(request, "Access denied! Admin permission required.")
        return redirect('dashboard')
    
    if request.method == 'POST':
        try:
            stock = request.POST.get('stock', '0').strip()
            
            if not stock.isdigit():
                messages.error(request, "Invalid stock value!")
                return redirect('admin_products')
            
            # Get product info for message
            product_query = "SELECT name FROM shop_product WHERE id = %s"
            product = execute_sql_single(product_query, [product_id])
            
            if product:
                update_query = "UPDATE shop_product SET stock = %s WHERE id = %s"
                result = execute_sql_query(update_query, [int(stock), product_id])
                
                print(f"✅ DEBUG: Stock updated - {result} rows affected")
                messages.success(request, f'✅ Stock updated for "{product["name"]}"! New stock: {stock}')
            else:
                messages.error(request, "Product not found!")
                
        except Exception as e:
            messages.error(request, f"❌ Error updating stock: {str(e)}")
            print(f"❌ ERROR in admin_update_stock: {e}")
    
    return redirect('admin_products')

# ❌ REMOVE the duplicate admin_update_stock function (keep only one)

# ... rest of your code ...

@login_required
def admin_delete_product(request, product_id):
    """Delete product - DEBUG VERSION"""
    if not is_admin_user(request.user.id):
        messages.error(request, "Access denied! Admin permission required.")
        return redirect('dashboard')
    
    try:
        print(f"🔄 DEBUG: Delete function called for product_id: {product_id}")
        
        # Check if product exists
        product_query = "SELECT id, name FROM shop_product WHERE id = %s"
        product = execute_sql_single(product_query, [product_id])
        
        if not product:
            print(f"❌ DEBUG: Product {product_id} not found")
            messages.error(request, "Product not found!")
            return redirect('admin_products')
        
        print(f"✅ DEBUG: Product found - ID: {product['id']}, Name: {product['name']}")
        
        # ✅ OPTION 1: Try SOFT DELETE first
        print("🔄 DEBUG: Attempting soft delete...")
        soft_delete_query = "UPDATE shop_product SET available = 0 WHERE id = %s"
        soft_result = execute_sql_query(soft_delete_query, [product_id])
        print(f"✅ DEBUG: Soft delete result - {soft_result} rows affected")
        
        if soft_result > 0:
            messages.success(request, f'✅ Product "{product["name"]}" deleted successfully!')
            print(f"✅ DEBUG: Soft delete successful for product: {product['name']}")
        else:
            # ✅ OPTION 2: If soft delete fails, try HARD DELETE
            print("🔄 DEBUG: Soft delete failed, attempting hard delete...")
            hard_delete_query = "DELETE FROM shop_product WHERE id = %s"
            hard_result = execute_sql_query(hard_delete_query, [product_id])
            print(f"✅ DEBUG: Hard delete result - {hard_result} rows affected")
            
            if hard_result > 0:
                messages.success(request, f'✅ Product "{product["name"]}" permanently deleted!')
                print(f"✅ DEBUG: Hard delete successful for product: {product['name']}")
            else:
                messages.error(request, "Failed to delete product!")
                print(f"❌ DEBUG: Both soft and hard delete failed for product: {product['name']}")
            
    except Exception as e:
        error_msg = str(e)
        print(f"❌ ERROR in admin_delete_product: {error_msg}")
        messages.error(request, f"Error deleting product: {error_msg}")
    
    return redirect('admin_products')
@login_required
def admin_update_stock(request, product_id):
    """Update product stock"""
    if not is_admin_user(request.user.id):
        messages.error(request, "Access denied! Admin permission required.")
        return redirect('dashboard')
    
    if request.method == 'POST':
        try:
            stock = request.POST.get('stock')
            
            product_query = "SELECT name FROM shop_product WHERE id = %s"
            product = execute_sql_single(product_query, [product_id])
            
            if product:
                update_query = "UPDATE shop_product SET stock = %s WHERE id = %s"
                execute_sql_query(update_query, [int(stock), product_id])
                
                messages.success(request, f'✅ Stock updated for "{product["name"]}"! New stock: {stock}')
            else:
                messages.error(request, "Product not found!")
                
        except Exception as e:
            messages.error(request, "Error updating stock!")
    
    return redirect('admin_products')

@login_required
def admin_orders(request):
    """Admin orders"""
    if not is_admin_user(request.user.id):
        messages.error(request, "Access denied! Admin permission required.")
        return redirect('dashboard')
    
    try:
        orders_query = """
            SELECT o.*, u.username, u.first_name
            FROM shop_order o
            JOIN auth_user u ON o.user_id = u.id
            ORDER BY o.created_at DESC
        """
        orders = execute_sql_query(orders_query)
        
        return render(request, 'shop/admin/orders.html', {
            'orders': orders
        })
        
    except Exception as e:
        return render(request, 'shop/admin/orders.html', {'orders': []})

@login_required
def admin_update_order_status(request, order_id):
    """Update order status"""
    if not is_admin_user(request.user.id):
        messages.error(request, "Access denied! Admin permission required.")
        return redirect('dashboard')
    
    if request.method == 'POST':
        try:
            status = request.POST.get('status')
            
            update_query = "UPDATE shop_order SET status = %s WHERE id = %s"
            execute_sql_query(update_query, [status, order_id])
            
            messages.success(request, f'✅ Order #{order_id} status updated to {status}')
            
        except Exception as e:
            messages.error(request, "Error updating order status!")
    
    return redirect('admin_orders')

# ========================
# URL COMPATIBILITY FUNCTIONS
# ========================

def skin(request):
    """Alias for skin_care"""
    return skin_care(request)

def hair(request):
    """Alias for hair_care"""
    return hair_care(request)

def cart_view(request):
    """Alias for view_cart"""
    return view_cart(request)

def remove_cart_item(request, item_id):
    """Alias for remove_from_cart"""
    return remove_from_cart(request, item_id)

def orders(request):
    """Alias for order_history"""
    return order_history(request)



from django.utils import timezone  # ✅ timezone import যোগ করুন

# ... আপনার existing code ...

@login_required
def admin_user_activities(request):
    """Admin-কে User Activities দেখাবে"""
    if not is_admin_user(request.user.id):
        messages.error(request, "Access denied! Admin permission required.")
        return redirect('dashboard')
    
    try:
        # Recent User Registrations
        recent_users_query = """
            SELECT username, email, first_name, date_joined, last_login
            FROM auth_user 
            ORDER BY date_joined DESC 
            LIMIT 20
        """
        recent_users = execute_sql_query(recent_users_query)
        
        # Contact Messages
        contact_messages_query = """
            SELECT name, email, message, created_at 
            FROM shop_contactmessage 
            ORDER BY created_at DESC
            LIMIT 20
        """
        contact_messages = execute_sql_query(contact_messages_query)
        
        # Recent Orders
        recent_orders_query = """
            SELECT o.*, u.username, u.first_name
            FROM shop_order o
            JOIN auth_user u ON o.user_id = u.id
            ORDER BY o.created_at DESC
            LIMIT 15
        """
        recent_orders = execute_sql_query(recent_orders_query)
        
        # Recent Cart Activities
        recent_cart_activities_query = """
            SELECT ci.*, p.name as product_name, u.username
            FROM shop_cartitem ci
            JOIN shop_product p ON ci.product_id = p.id
            JOIN shop_cart c ON ci.cart_id = c.id
            JOIN auth_user u ON c.user_id = u.id
            ORDER BY ci.created_at DESC
            LIMIT 20
        """
        recent_cart_activities = execute_sql_query(recent_cart_activities_query)
        
        return render(request, 'shop/admin/user_activities.html', {
            'recent_users': recent_users,
            'contact_messages': contact_messages,
            'recent_orders': recent_orders,
            'recent_cart_activities': recent_cart_activities
        })
        
    except Exception as e:
        return render(request, 'shop/admin/user_activities.html')

# ✅ আলাদা function (indentation ঠিক করুন)
def contact(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        message_text = request.POST.get('message', '').strip()

        print(f"🔍 DEBUG: Contact Form Data - Name: '{name}', Email: '{email}', Message: '{message_text}'")

        if not name or not email or not message_text:
            print("❌ DEBUG: Validation failed - empty fields")
            messages.error(request, "All fields are required!")
            return render(request, 'shop/contact.html')

        try:
            print("✅ DEBUG: Attempting to insert into database...")
            
            contact_query = """
                INSERT INTO shop_contactmessage (name, email, message, created_at)
                VALUES (%s, %s, %s, NOW())
            """
            
            # Execute query
            result = execute_sql_query(contact_query, [name, email, message_text])
            print(f"✅ DEBUG: Query executed successfully! Rows affected: {result}")
            
            messages.success(request, f"Thank you {name}! Your message has been received.")
            return redirect('contact')
            
        except Exception as e:
            print(f"❌ DEBUG: Database Error: {str(e)}")
            messages.error(request, "Error sending message. Please try again.")
    
    return render(request, 'shop/contact.html')