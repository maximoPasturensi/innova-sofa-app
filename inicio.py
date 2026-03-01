import streamlit as st
from supabase import create_client
import pandas as pd

# 1. Configuración de conexión
# En lugar de pegar el texto de la clave, le decimos que la busque en secrets
URL_PROYECTO = st.secrets["URL_PROYECTO"]
KEY_PROYECTO = st.secrets["KEY_PROYECTO"]

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
        
        res = supabase.table("pedidos").select("*").order('id', desc=True).execute()
        
        if res.data:
            datos_tabla = []
            for p in res.data:
                cli = supabase.table("clientes").select("nombre_apellido").eq("id", p['cliente_id']).execute()
                nombre = cli.data[0]['nombre_apellido'] if cli.data else "S/N"
                
                # Datos financieros
                total = float(p['total_operacion'] or 0)
                anticipo = float(p['anticipo_monto'] or 0)
                metodo = p.get('anticipo_metodo', 'N/A') # Traemos la procedencia (ej: TRF JAVI)
                saldo = total - anticipo
                
                datos_tabla.append({
                    "Cliente": nombre,
                    "Total $": f"${total:,.2f}",
                    "Anticipo $": f"${anticipo:,.2f}",
                    "Procedencia": metodo,
                    "Saldo a Cobrar $": f"${saldo:,.2f}",
                    "Estado": p['estado']
                })
            
            # Mostramos la tabla completa
            st.table(datos_tabla)
            st.divider()
            
            # Detalles extra (Color y Notas)
            st.subheader("🔍 Detalles del Pedido")
            for p in res.data:
                cli = supabase.table("clientes").select("nombre_apellido").eq("id", p['cliente_id']).execute()
                nombre_cli = cli.data[0]['nombre_apellido'] if cli.data else "Cliente"
                
                with st.expander(f"🪑 {nombre_cli} - Ver Tela y Notas"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Color/Tela:** {p['color']}")
                    with col2:
                        st.write(f"**Notas:** {p['nota']}")
                    
                    if st.button("Marcar como Terminado", key=f"btn_{p['id']}"):
                        supabase.table("pedidos").update({"estado": "Terminado"}).eq("id", p['id']).execute()
                        st.rerun()
        else:
            st.info("No hay pedidos pendientes.")