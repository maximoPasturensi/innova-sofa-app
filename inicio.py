import streamlit as st
from supabase import create_client
import pandas as pd

# 1. Configuración de conexión
URL_PROYECTO = "https://dpbvabeqgokpjixbsbxr.supabase.co"
KEY_PROYECTO = "sb_publishable_wJkOANIAJDUv7PxrjFz-VA_2lITki7K"
supabase = create_client(URL_PROYECTO, KEY_PROYECTO)

# 2. Función de Login
def check_password():
    def password_entered():
        if st.session_state["username"] == "admin" and st.session_state["password"] == "innova2024":
            st.session_state["password_correct"] = True
            del st.session_state["password"]
            del st.session_state["username"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.text_input("Usuario", key="username")
        st.text_input("Contraseña", type="password", key="password")
        st.button("Ingresar", on_click=password_entered)
        return False
    elif not st.session_state["password_correct"]:
        st.text_input("Usuario", key="username")
        st.text_input("Contraseña", type="password", key="password")
        st.button("Ingresar", on_click=password_entered)
        st.error("😕 Usuario o contraseña incorrectos")
        return False
    else:
        return True

# 3. CONTROL DE ACCESO (Si el login es correcto, muestra el resto)
if check_password():
    # --- TODO LO QUE SIGUE TIENE 4 ESPACIOS DE SANGRÍA ---
    st.set_page_config(page_title="Innova Sofá - Gestión", layout="wide")
    st.sidebar.success("Sesión iniciada")
    st.title("🛋️ Sistema de Gestión Innova Sofá")

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
            descripcion = st.text_area("Descripción del Artículo")
            total = st.number_input("Total Operación $", min_value=0.0)
            anticipo = st.number_input("Anticipo $", min_value=0.0)
            metodo = st.text_input("Método de Anticipo (Ej: TRF JAVI)")

        if st.button("Guardar Pedido en la Nube"):
            res_cliente = supabase.table("clientes").insert({"nombre_apellido": nombre, "direccion": direccion, "localidad": localidad}).execute()
            cliente_id = res_cliente.data[0]['id']
            supabase.table("pedidos").insert({
                "cliente_id": cliente_id,
                "color": color,
                "total_operacion": total,
                "anticipo_monto": anticipo,
                "anticipo_metodo": metodo,
                "nota": descripcion
            }).execute()
            st.success(f"✅ ¡Pedido de {nombre} guardado!")

    elif opcion == "Ver Pedidos Pendientes":
        st.header("📋 Tablero de Producción - Fábrica")
        res = supabase.table("pedidos").select("*, clientes(nombre_apellido)").order('id', desc=True).execute()
        
        if res.data:
            for p in res.data:
                total = float(p['total_operacion'])
                anticipo = float(p['anticipo_monto'])
                saldo = total - anticipo
                with st.expander(f"🪑 {p['clientes']['nombre_apellido']} - {p['estado']}"):
                    st.write(f"**Color:** {p['color']} | **Nota:** {p['nota']}")
                    st.error(f"**SALDO A COBRAR:** ${saldo:,.2f}")
                    if st.button("Marcar como Terminado", key=p['id']):
                        supabase.table("pedidos").update({"estado": "Terminado"}).eq("id", p['id']).execute()
                        st.rerun()