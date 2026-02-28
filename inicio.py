import streamlit as st
from supabase import create_client
import pandas as pd

# --- SISTEMA DE LOGIN SIMPLE ---
def check_password():
    """Retorna True si el usuario ingresó la contraseña correcta."""
    def password_entered():
        """Chequea si la contraseña coincide."""
        if st.session_state["username"] == "admin" and st.session_state["password"] == "innova2026":
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # No guardamos la contraseña
            del st.session_state["username"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # Pantalla de Login
        st.text_input("Usuario", on_change=None, key="username")
        st.text_input("Contraseña", type="password", on_change=password_entered, key="password")
        return False
    elif not st.session_state["password_correct"]:
        # Falló el login
        st.text_input("Usuario", on_change=None, key="username")
        st.text_input("Contraseña", type="password", on_change=password_entered, key="password")
        st.error("😕 Usuario o contraseña incorrectos")
        return False
    else:
        # Contraseña correcta
        return True

# --- CONTROL DE ACCESO ---
if check_password():
    # AQUÍ VA TODO EL RESTO DE TU CÓDIGO ACTUAL
    # (El st.title, el menú, el registro de pedidos, etc.)
    st.sidebar.success("Sesión iniciada")

# 1. Configuración de conexión (Copiá tus datos de Supabase aquí)
URL_PROYECTO = "https://dpbvabeqgokpjixbsbxr.supabase.co"
KEY_PROYECTO = "sb_publishable_wJkOANlAJDuV7PxrjFz-VA_2lITki7K"
supabase = create_client(URL_PROYECTO, KEY_PROYECTO)

st.set_page_config(page_title="Innova Sofá - Gestión", layout="wide")

st.title("🛋️ Sistema de Gestión Innova Sofá")

# Menú lateral
opcion = st.sidebar.selectbox("Menú", ["Registrar Pedido", "Ver Pedidos Pendientes"])

if opcion == "Registrar Pedido":
    st.header("📝 Cargar Nuevo Remito")
    
    col1, col2 = st.columns(2)
    
    with col1:
        nombre = st.text_input("Nombre y Apellido del Cliente")
        direccion = st.text_input("Dirección")
        localidad = st.text_input("Localidad")
        color = st.text_input("Color (Ej: Kaki Scandal)")
        
    with col2:
        descripcion = st.text_area("Descripción del Artículo (Ej: Sillón Monaco 1.80)")
        total = st.number_input("Total Operación $", min_value=0.0)
        anticipo = st.number_input("Anticipo $", min_value=0.0)
        metodo = st.text_input("Método de Anticipo (Ej: TRF JAVI)")

    if st.button("Guardar Pedido en la Nube"):
        # Lógica para guardar en Supabase
        # Primero guardamos al cliente
        res_cliente = supabase.table("clientes").insert({"nombre_apellido": nombre, "direccion": direccion, "localidad": localidad}).execute()
        cliente_id = res_cliente.data[0]['id']
        
        # Luego guardamos el pedido
        res_pedido = supabase.table("pedidos").insert({
            "cliente_id": cliente_id,
            "color": color,
            "total_operacion": total,
            "anticipo_monto": anticipo,
            "anticipo_metodo": metodo,
            "nota": descripcion
        }).execute()
        
        st.success(f"✅ ¡Pedido de {nombre} guardado! Ya lo pueden ver en la fábrica.")

elif opcion == "Ver Pedidos Pendientes":
    st.header("📋 Tablero de Producción - Fábrica")
    
    # Traemos los datos de la nube con un "Join" para traer el nombre del cliente
    # Usamos .order('id', desc=True) para ver lo último que se cargó primero
    res = supabase.table("pedidos").select("*, clientes(nombre_apellido)").order('id', desc=True).execute()
    
    if res.data:
        for p in res.data:
            # Calculamos el saldo restante
            total = float(p['total_operacion'])
            anticipo = float(p['anticipo_monto'])
            saldo = total - anticipo
            
            # Creamos una "tarjeta" visual para cada pedido
            with st.expander(f"🪑 {p['clientes']['nombre_apellido']} - {p['estado']}"):
                c1, c2, c3 = st.columns(3)
                with c1:
                    st.write(f"**Color:** {p['color']}")
                    st.write(f"**Lado:** {p['lado'] if p['lado'] else 'No especifica'}")
                with c2:
                    st.write(f"**Descripción:** {p['nota']}")
                with c3:
                    st.write(f"**Total:** ${total:,.2f}")
                    st.write(f"**Anticipo:** ${anticipo:,.2f}")
                    st.error(f"**SALDO A COBRAR:** ${saldo:,.2f}")
                
                # Botón para cambiar estado (Esto le va a encantar a tu viejo)
                if st.button("Marcar como Terminado", key=p['id']):
                    supabase.table("pedidos").update({"estado": "Terminado"}).eq("id", p['id']).execute()
                    st.rerun()
    else:
        st.info("No hay pedidos en fabricación en este momento.")