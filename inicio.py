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
            # --- ACÁ EMPIEZAN LOS EXPANDERS DIRECTAMENTE ---
            # Sumamos todos los saldos de la lista
            total_a_cobrar = sum((float(p['total_operacion'] or 0) - float(p['anticipo_monto'] or 0)) for p in res.data)

    elif opcion == "Reforzar Seña":
        st.header("💰 Registrar Refuerzo de Dinero")
        
        # 1. Buscamos pedidos que NO estén terminados
        res = supabase.table("pedidos").select("*, clientes(nombre_apellido)").eq("estado", "Pendiente").execute()
        
        if res.data:
            # Creamos una lista para que tu viejo elija el pedido fácilmente
            opciones_pedidos = {f"ID: {p['id']} - {p['clientes']['nombre_apellido']}": p for p in res.data}
            seleccion = st.selectbox("Seleccioná el pedido a reforzar:", list(opciones_pedidos.keys()))
            
            pedido_elegido = opciones_pedidos[seleccion]
            
            st.info(f"Saldo actual a cobrar: **${float(pedido_elegido['total_operacion']) - float(pedido_elegido['anticipo_monto']):,.2f}**")
            
            # 2. Formulario para el nuevo dinero
            nuevo_monto = st.number_input("Monto del refuerzo:", min_value=0.0, step=1000.0)
            nuevo_metodo = st.selectbox("Método de pago:", ["Efectivo", "Transferencia", "Tarjeta"])
            
            if st.button("Confirmar Refuerzo"):
                # Calculamos el nuevo total de anticipo
                nuevo_total_anticipo = float(pedido_elegido['anticipo_monto']) + nuevo_monto
                # Actualizamos la nota para que quede registro (opcional pero muy útil)
                nueva_nota = f"{pedido_elegido['nota']} | REFUERZO: ${nuevo_monto} por {nuevo_metodo}"
                
                supabase.table("pedidos").update({
                    "anticipo_monto": nuevo_total_anticipo,
                    "nota": nueva_nota
                }).eq("id", pedido_elegido['id']).execute()
                
                st.success(f"¡Pago registrado! El nuevo saldo es: ${float(pedido_elegido['total_operacion']) - nuevo_total_anticipo:,.2f}")
                st.balloons()
        else:
            st.warning("No hay pedidos pendientes para reforzar.")

# Lo mostramos en un cartel grande y verde
            total_a_cobrar = sum((float(p['total_operacion'] or 0) - float(p['anticipo_monto'] or 0)) for p in res.data)
            st.metric(label="💰 TOTAL PENDIENTE DE COBRO", value=f"${total_a_cobrar:,.2f}")
            st.divider()

            for p in res.data:
                # Buscamos el nombre del cliente
                cli = supabase.table("clientes").select("nombre_apellido").eq("id", p['cliente_id']).execute()
                nombre_cli = cli.data[0]['nombre_apellido'] if cli.data else "Cliente"
                
                # Cálculos (esto lo necesitás para el título del expander)
                total = float(p['total_operacion'] or 0)
                anticipo = float(p['anticipo_monto'] or 0)
                saldo = total - anticipo
                metodo = p.get('anticipo_metodo', 'N/A')

                # Título con el SALDO bien a la vista
                with st.expander(f"🪑 {nombre_cli} | SALDO: ${saldo:,.2f} | {p['estado']}"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown("### 💰 Pago")
                        st.write(f"**Total:** ${total:,.2f}")
                        st.write(f"**Anticipo:** ${anticipo:,.2f} ({metodo})")
                        st.error(f"**SALDO:** ${saldo:,.2f}")
                    with col2:
                        st.markdown("### 🛋️ Producto")
                        st.write(f"**Color:** {p['color']}")
                        st.write(f"**Notas:** {p['nota']}")
                    
                    if st.button("Marcar Terminado", key=f"btn_{p['id']}"):
                        supabase.table("pedidos").update({"estado": "Terminado"}).eq("id", p['id']).execute()
                        st.rerun()