# db_operations.py
from supabase_config import supabase

# Funciones para productos
def get_all_products():
    response = supabase.table('products').select('*').execute()
    return response.data

def get_product_by_id(product_id):
    response = supabase.table('products').select('*').eq('id', product_id).execute()
    if response.data:
        return response.data[0]
    return None

def get_products_by_category(category):
    response = supabase.table('products').select('*').eq('category', category).execute()
    return response.data

# Funciones para el carrito
def get_cart(user_id):
    # Primero, buscar si el usuario ya tiene un carrito
    response = supabase.table('carts').select('*').eq('user_id', user_id).execute()
    
    # Si no tiene carrito, crear uno nuevo
    if not response.data:
        cart_response = supabase.table('carts').insert({'user_id': user_id}).execute()
        return cart_response.data[0]
    
    return response.data[0]

def get_cart_items(cart_id):
    response = supabase.table('cart_items')\
        .select('*, products(*)').eq('cart_id', cart_id).execute()
    return response.data

def add_to_cart(cart_id, product_id, quantity=1):
    # Verificar si el producto ya está en el carrito
    response = supabase.table('cart_items')\
        .select('*').eq('cart_id', cart_id).eq('product_id', product_id).execute()
    
    if response.data:
        # Si ya existe, actualizar la cantidad
        item_id = response.data[0]['id']
        new_quantity = response.data[0]['quantity'] + quantity
        update_response = supabase.table('cart_items')\
            .update({'quantity': new_quantity}).eq('id', item_id).execute()
        return update_response.data[0]
    else:
        # Si no existe, crear un nuevo item
        insert_response = supabase.table('cart_items')\
            .insert({'cart_id': cart_id, 'product_id': product_id, 'quantity': quantity}).execute()
        return insert_response.data[0]

def remove_from_cart(cart_id, product_id):
    response = supabase.table('cart_items')\
        .delete().eq('cart_id', cart_id).eq('product_id', product_id).execute()
    return response.data

def update_cart_item_quantity(cart_id, product_id, quantity):
    if quantity <= 0:
        return remove_from_cart(cart_id, product_id)
    
    response = supabase.table('cart_items')\
        .update({'quantity': quantity}).eq('cart_id', cart_id).eq('product_id', product_id).execute()
    return response.data