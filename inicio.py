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

    # Definimos el menú con las 3 opciones
    opcion = st.sidebar.selectbox("Menú", ["Registrar Pedido", "Ver Pedidos Pendientes", "Reforzar Seña"])

    # --- OPCIÓN 1: REGISTRAR ---
    if opcion == "Registrar Pedido":
        st.header("📝 Cargar Nuevo Remito")
        with st.form("nuevo_pedido"):
            nombre = st.text_input("Nombre y Apellido del Cliente")
            color = st.text_input("Color (Ej: Kaki Scandal)")
            total = st.number_input("Total Operación $", min_value=0.0)
            anticipo = st.number_input("Anticipo $", min_value=0.0)
            metodo = st.text_input("Método de Anticipo (Ej: TRF JAVI)")
            notas = st.text_area("Descripción del Artículo")
            
            if st.form_submit_button("Guardar Pedido en la Nube"):
                # Primero guardamos el cliente
                res_cli = supabase.table("clientes").insert({"nombre_apellido": nombre}).execute()
                cli_id = res_cli.data[0]['id']
                
                # Después guardamos el pedido
                supabase.table("pedidos").insert({
                    "cliente_id": cli_id,
                    "color": color,
                    "total_operacion": total,
                    "anticipo_monto": anticipo,
                    "anticipo_metodo": metodo,
                    "nota": notas,
                    "estado": "Pendiente"
                }).execute()
                st.success(f"✅ ¡Pedido de {nombre} guardado!")

    # --- OPCIÓN 2: VER TABLERO ---
    elif opcion == "Ver Pedidos Pendientes":
        st.header("📋 Tablero de Producción")
        res = supabase.table("pedidos").select("*").eq("estado", "Pendiente").order('id', desc=True).execute()
        
        if res.data:
            # Cálculo del total de la calle
            total_a_cobrar = sum((float(p['total_operacion'] or 0) - float(p['anticipo_monto'] or 0)) for p in res.data)
            st.metric(label="💰 TOTAL EN LA CALLE", value=f"${total_a_cobrar:,.2f}")
            st.divider()

            for p in res.data:
                cli = supabase.table("clientes").select("nombre_apellido").eq("id", p['cliente_id']).execute()
                nombre_cli = cli.data[0]['nombre_apellido'] if cli.data else "Cliente"
                saldo = float(p['total_operacion'] or 0) - float(p['anticipo_monto'] or 0)

                with st.expander(f"🆔 {p['id']} | 🪑 {nombre_cli} | SALDO: ${saldo:,.2f}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"**Total:** ${float(p['total_operacion']):,.2f}")
                        st.write(f"**Anticipo:** ${float(p['anticipo_monto']):,.2f} ({p['anticipo_metodo']})")
                    with col2:
                        st.write(f"**Color:** {p['color']}")
                        st.write(f"**Notas:** {p['nota']}")
                    
                    if st.button("Marcar Terminado", key=f"fin_{p['id']}"):
                        supabase.table("pedidos").update({"estado": "Terminado"}).eq("id", p['id']).execute()
                        st.rerun()
        else:
            st.info("No hay pedidos pendientes.")

    # --- OPCIÓN 3: REFORZAR SEÑA ---
    elif opcion == "Reforzar Seña":
        st.header("💰 Registrar Refuerzo de Dinero")
        res = supabase.table("pedidos").select("*, clientes(nombre_apellido)").eq("estado", "Pendiente").execute()
        
        if res.data:
            opciones = {f"ID: {p['id']} - {p['clientes']['nombre_apellido']}": p for p in res.data}
            seleccion = st.selectbox("Seleccioná el pedido:", list(opciones.keys()))
            pedido = opciones[seleccion]
            
            refuerzo = st.number_input("Monto del refuerzo $:", min_value=0.0)
            if st.button("Confirmar Pago"):
                nuevo_monto = float(pedido['anticipo_monto']) + refuerzo
                supabase.table("pedidos").update({"anticipo_monto": nuevo_monto}).eq("id", pedido['id']).execute()
                st.success("¡Saldo actualizado!")
                st.balloons()