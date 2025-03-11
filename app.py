from flask import Flask, render_template, request, redirect, url_for, session, flash
import os
from dotenv import load_dotenv
import uuid
from supabase import create_client, Client
import json
from datetime import datetime

# Cargar variables de entorno
load_dotenv()

# Configurar cliente de Supabase
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(supabase_url, supabase_key)

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "clave_secreta_temporal")

# Generar un ID de usuario temporal si no existe
def get_user_id():
    if 'user_id' not in session:
        session['user_id'] = str(uuid.uuid4())
    return session['user_id']

# Función para formatear precios
def format_price(price):
    return f"{price:,.0f}".replace(",", ".")

# Productos estáticos para la demostración
PRODUCTOS_ESTATICOS = [
    {
        "id": 1,
        "name": "Pantalón Cargo Multi-Pocket",
        "price": 320000,
        "image_url": "https://trueshop.co/cdn/shop/files/Cargo_Multi_Pocket_Pants_Washed_Black_1_720x720.jpg?v=1738204246",
        "description": "Pantalón cargo con múltiples bolsillos, perfecto para un look casual y funcional.",
        "stock": 15,
        "category": "ropa"
    },
    {
        "id": 2,
        "name": "Camiseta Oversized Lavado",
        "price": 170000,
        "image_url": "https://trueshop.co/cdn/shop/files/Dreams-Boxy-Tee-Black-01_344a24c9-e6a3-4fdc-8a1f-1b5a9107e741_800x.jpg?v=1740433357",
        "description": "Camiseta de corte holgado con efecto lavado, ideal para un estilo urbano y relajado.",
        "stock": 25,
        "category": "ropa"
    },
    {
        "id": 3,
        "name": "Zapatilla Nike Casual Dama Air Force 1 07 Blanco",
        "price": 640000,
        "image_url": "https://azzurry.com/wp-content/uploads/2024/03/0095_DD8959-100.jpg",
        "description": "Zapatillas clásicas de Nike, versátiles y cómodas para uso diario.",
        "stock": 10,
        "category": "calzado"
    },
    {
        "id": 4,
        "name": "Chaqueta Negra Prospect Mte-1 Puffer Jacket Hombre Vans",
        "price": 489300,
        "image_url": "https://vansco.vteximg.com.br/arquivos/ids/326451-1000-1000/VN0A7S8HBLK-1.jpg?v=638367830544230000",
        "description": "Chaqueta acolchada resistente al agua, perfecta para climas fríos.",
        "stock": 8,
        "category": "ropa"
    },
    {
        "id": 5,
        "name": "Gorro de Punto Negro para Hombre - 100% Algodón",
        "price": 59990,
        "image_url": "https://www.gef.co/cdn/shop/files/tom-gorro-negro-799-729439_000799-1.jpg?v=1738327019",
        "description": "Gorro de punto suave y cómodo, perfecto para completar tu look invernal.",
        "stock": 30,
        "category": "accesorios"
    },
    {
        "id": 6,
        "name": "Cadena de 60 cm cubana color oro acero inoxidable 12 mm hombre",
        "price": 39900,
        "image_url": "https://imagedelivery.net/4fYuQyy-r8_rpBpcY7lH_A/falabellaCO/122993611_01/w=1500,h=1500,fit=pad",
        "description": "Cadena de estilo cubano en acero inoxidable dorado, resistente y duradera.",
        "stock": 20,
        "category": "accesorios"
    }
]

@app.route('/')
def inicio():
    return render_template('home.html')

@app.route('/productos')
def ver_catalogo():
    return render_template('products.html')

@app.route('/contacto')
def ver_contacto():
    return render_template('contact.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        try:
            # Iniciar sesión con Supabase
            response = supabase.auth.sign_in_with_password({"email": email, "password": password})
            session['user_id'] = response.user.id
            session['user_email'] = email
            
            # Obtener información adicional del usuario si existe
            try:
                user_profile = supabase.table('profiles').select('*').eq('id', response.user.id).execute()
                if user_profile.data:
                    # Si hay un nombre en el perfil, guardarlo
                    if 'full_name' in user_profile.data[0]:
                        session['user_name'] = user_profile.data[0]['full_name']
                    # Si no hay nombre, usar la parte del email antes de @
                    else:
                        session['user_name'] = email.split('@')[0]
                else:
                    session['user_name'] = email.split('@')[0]
            except Exception as profile_error:
                print(f"Error al obtener perfil: {str(profile_error)}")
                session['user_name'] = email.split('@')[0]
            
            flash('Has iniciado sesión correctamente', 'success')
            
            # Verificar si hay una URL de redirección después del login
            if 'redirect_after_login' in session:
                redirect_url = session.pop('redirect_after_login')
                if redirect_url == url_for('proceder_pago'):
                    # Si la redirección es a proceder_pago, mostrar una página intermedia
                    return render_template('redireccion_pago.html')
                return redirect(redirect_url)
                
            return redirect(url_for('inicio'))
        except Exception as e:
            flash(f'Error al iniciar sesión: {str(e)}', 'error')
    
    return render_template('login.html')

@app.route('/carrito')
def cart():
    user_id = get_user_id()
    
    # Obtener el carrito de la sesión
    if 'cart' not in session:
        session['cart'] = []
    
    cart_items = session['cart']
    
    # Calcular el total
    total = sum(item['price'] * item['quantity'] for item in cart_items)
    
    return render_template('cart.html', cart_items=cart_items, total=total, format_price=format_price)

@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    product_id = int(request.form.get('product_id'))
    quantity = int(request.form.get('quantity', 1))
    
    # Buscar el producto en la lista estática
    product = next((p for p in PRODUCTOS_ESTATICOS if p['id'] == product_id), None)
    
    if product:
        # Inicializar el carrito si no existe
        if 'cart' not in session:
            session['cart'] = []
        
        # Verificar si el producto ya está en el carrito
        cart = session['cart']
        existing_item = next((item for item in cart if item['id'] == product_id), None)
        
        if existing_item:
            # Actualizar cantidad
            existing_item['quantity'] += quantity
        else:
            # Agregar nuevo item
            cart_item = {
                'id': product['id'],
                'name': product['name'],
                'price': product['price'],
                'image_url': product['image_url'],
                'quantity': quantity
            }
            cart.append(cart_item)
        
        # Guardar el carrito actualizado en la sesión
        session['cart'] = cart
        flash(f'Se agregó {product["name"]} al carrito', 'success')
    else:
        flash('Producto no encontrado', 'error')
    
    return redirect(url_for('cart'))

@app.route('/remove_from_cart', methods=['POST'])
def remove_from_cart():
    product_id = int(request.form.get('product_id'))
    
    if 'cart' in session:
        # Filtrar el carrito para eliminar el producto
        session['cart'] = [item for item in session['cart'] if item['id'] != product_id]
        flash('Producto eliminado del carrito', 'success')
    
    return redirect(url_for('cart'))

@app.route('/update_quantity', methods=['POST'])
def update_quantity():
    product_id = int(request.form.get('product_id'))
    quantity = int(request.form.get('quantity'))
    
    if 'cart' in session:
        cart = session['cart']
        for item in cart:
            if item['id'] == product_id:
                if quantity <= 0:
                    # Eliminar el producto si la cantidad es 0 o menos
                    cart.remove(item)
                else:
                    # Actualizar la cantidad
                    item['quantity'] = quantity
                break
        
        session['cart'] = cart
        flash('Carrito actualizado', 'success')
    
    return redirect(url_for('cart'))

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        try:
            # Registrar usuario con Supabase
            response = supabase.auth.sign_up({
                "email": email,
                "password": password
            })
            
            # Verificar si el registro fue exitoso
            if response.user:
                # Crear un perfil de usuario en la tabla 'profiles'
                try:
                    supabase.table('profiles').insert({
                        'id': response.user.id,
                        'email': email,
                        'created_at': 'now()'
                    }).execute()
                except Exception as profile_error:
                    print(f"Error al crear perfil: {str(profile_error)}")
                
                # Mostrar mensaje de éxito y redirigir
                flash('¡Registro exitoso! Por favor verifica tu correo electrónico para activar tu cuenta.', 'success')
                return redirect(url_for('login'))
            else:
                flash('Error en el registro. Por favor, inténtalo de nuevo.', 'error')
        except Exception as e:
            error_message = str(e) if str(e) else "Error desconocido en el registro"
            flash(f'Error al registrar: {error_message}', 'error')
    
    return render_template('register.html')

@app.route('/nosotros')
def ver_nosotros():
    return render_template('nosotros.html')

# Nuevas rutas para el proceso de pago
@app.route('/proceder_pago', methods=['POST'])
def proceder_pago():
    # Verificar si el usuario está autenticado
    if 'user_email' not in session:
        flash('Por favor inicia sesión para completar tu compra', 'info')
        # Guardar la URL de retorno para redirigir después del login
        session['redirect_after_login'] = url_for('proceder_pago')
        return redirect(url_for('login'))
    
    # Si el usuario está autenticado, procesar el pago
    if 'cart' in session and session['cart']:
        # Aquí iría la lógica de procesamiento de pago real
        # Por ahora, simplemente guardamos la información del pedido y limpiamos el carrito
        
        # Guardar información del pedido para mostrarla en la confirmación
        pedido = {
            'items': session['cart'],
            'total': sum(item['price'] * item['quantity'] for item in session['cart']),
            'fecha': datetime.now().strftime('%d/%m/%Y %H:%M'),
            'usuario': session.get('user_email', 'Usuario anónimo')
        }
        
        # Guardar el pedido en la sesión para mostrarlo en la confirmación
        session['ultimo_pedido'] = pedido
        
        # Aquí podrías guardar el pedido en Supabase si lo deseas
        try:
            # Crear el pedido en la base de datos
            order_data = {
                'user_id': session.get('user_id'),
                'total': pedido['total'],
                'status': 'completado',
                'items': json.dumps([{
                    'product_id': item['id'],
                    'name': item['name'],
                    'price': item['price'],
                    'quantity': item['quantity']
                } for item in session['cart']])
            }
            
            # Insertar en Supabase (descomenta si tienes una tabla 'orders')
            # supabase.table('orders').insert(order_data).execute()
            
        except Exception as e:
            print(f"Error al guardar el pedido: {str(e)}")
        
        # Limpiar el carrito
        session['cart'] = []
        
        flash('¡Pago procesado con éxito!', 'success')
        return redirect(url_for('confirmacion_compra'))
    else:
        flash('Tu carrito está vacío', 'error')
        return redirect(url_for('cart'))

@app.route('/confirmacion_compra')
def confirmacion_compra():
    # Verificar si hay información de pedido
    if 'ultimo_pedido' not in session:
        return redirect(url_for('ver_catalogo'))
    
    pedido = session['ultimo_pedido']
    return render_template('confirmacion_compra.html', pedido=pedido, format_price=format_price)

@app.context_processor
def inject_user():
    """Inyecta la información del usuario en todas las plantillas."""
    user_data = None
    if 'user_email' in session:
        user_data = {
            'email': session['user_email'],
            'name': session.get('user_name', session['user_email'].split('@')[0])  # Usar parte del email como nombre si no hay nombre
        }
    return {'user': user_data}

@app.route('/logout')
def logout():
    # Limpiar datos de sesión relacionados con el usuario
    session.pop('user_id', None)
    session.pop('user_email', None)
    session.pop('user_name', None)
    flash('Has cerrado sesión correctamente', 'success')
    return redirect(url_for('inicio'))

if __name__ == '__main__':
    app.run(debug=True)
    
