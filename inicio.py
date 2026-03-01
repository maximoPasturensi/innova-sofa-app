import streamlit as st
from supabase import create_client
import pandas as pd
from fpdf import FPDF

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
    opcion = st.sidebar.selectbox("Menú", ["Registrar Pedido", "Ver Pedidos Pendientes", "Reforzar Seña", "Pedidos Terminados"])

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
            whatsapp = st.text_input("📱 Número del cliente", placeholder="Ej: 1150361256")
            st.caption("💡 Tip: Poné el 11 adelante para que el botón directo funcione perfecto.")
            
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

    # --- OPCIÓN 2: VER TABLERO (CON BUSCADOR) ---
    elif opcion == "Ver Pedidos Pendientes":
        st.header("📋 Tablero de Producción")
        
        # 1. Traemos los datos de la nube
        res = supabase.table("pedidos").select("*").eq("estado", "Pendiente").order('id', desc=True).execute()
        
        if res.data:
            # --- NUEVO: BARRA DE BÚSQUEDA ---
            busqueda = st.text_input("🔍 Buscar por nombre de cliente o detalle:", "").lower()

            # Procesamos los datos para poder filtrar
            pedidos_mostrados = []
            for p in res.data:
                cli = supabase.table("clientes").select("nombre_apellido").eq("id", p['cliente_id']).execute()
                nombre_cli = cli.data[0]['nombre_apellido'] if cli.data else "Cliente"
                
                # Si el buscador está vacío o coincide con el nombre/nota/color, lo agregamos
                if busqueda in nombre_cli.lower() or busqueda in p['nota'].lower() or busqueda in p['color'].lower():
                    pedidos_mostrados.append((p, nombre_cli))

            # 2. CÁLCULO DEL TOTAL (Solo de lo que se ve en pantalla)
            total_visible = sum((float(item[0]['total_operacion'] or 0) - float(item[0]['anticipo_monto'] or 0)) for item in pedidos_mostrados)
            
            col_met, col_info = st.columns([2, 1])
            with col_met:
                st.metric(label="💰 SALDO PENDIENTE (FILTRADO)", value=f"${total_visible:,.2f}")
            with col_info:
                st.write(f"Mostrando **{len(pedidos_mostrados)}** pedidos")
            
            st.divider()
            saldo = float(p.get('total_operacion') or 0) - float(p.get('anticipo_monto') or 0)
            with st.expander(f"🆔 {p['id']} | 🪑 {nombre_cli} | SALDO: ${saldo:,.2f}"):
                col1, col2 = st.columns(2)
            with col1:
                st.markdown("### 💰 Pago")
                st.write(f"**Total:** ${float(p['total_operacion']):,.2f}")
                st.write(f"**Anticipo:** ${float(p['anticipo_monto']):,.2f}")
            with col2:
                st.markdown("### 🛋️ Producto")
                st.write(f"**Color:** {p['color']}")
                st.write(f"**Notas:** {p['nota']}")
            
            st.divider()

            # --- BOTÓN DE WHATSAPP ---
            # (Aquí también debe haber 8 espacios de margen)
            tel_sucio = p.get('cliente_telefono', '')
            tel_limpio = "".join(filter(str.isdigit, str(tel_sucio)))
            
            if tel_limpio:
                link_wa = f"https://wa.me/{tel_limpio}"
                st.link_button("🟢 Ir al WhatsApp del Cliente", link_wa, type="primary")

             # --- GENERADOR DE PDF ---
            if st.button(f"📄 Generar Remito #{p['id']}", key=f"pdf_{p['id']}"):
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", "B", 16)
                pdf.cell(0, 10, "INNOVA SOFÁ - REMITO", ln=True, align="C")
                pdf.set_font("Arial", "", 12)
                pdf.ln(10)
                pdf.cell(0, 10, f"Cliente: {nombre_cli}", ln=True)
                pdf.cell(0, 10, f"Detalle: {p['nota']}", ln=True)
                pdf.cell(0, 10, f"Color: {p['color']}", ln=True)
                pdf.ln(5)
                pdf.cell(0, 10, f"SALDO A COBRAR: ${saldo:,.2f}", ln=True)
                                
                nombre_pdf = f"Remito_{p['id']}.pdf"
                pdf.output(nombre_pdf)
                                
            with open(nombre_pdf, "rb") as f:
                    st.download_button("⬇️ Descargar PDF", f, file_name=nombre_pdf)

                    # --- BOTÓN TERMINAR ---
                    if st.button("Marcar Terminado", key=f"fin_{p['id']}"):
                        supabase.table("pedidos").update({"estado": "Terminado"}).eq("id", p['id']).execute()
                        st.success("¡Pedido finalizado!")
                        st.rerun()
                    else:
                        st.info("No hay pedidos pendientes.")

        # --- OPCIÓN 4: PEDIDOS TERMINADOS (EL HISTORIAL) ---
    elif opcion == "Pedidos Terminados":
        st.header("✅ Historial de Pedidos Finalizados")
        
        # Traemos solo los que tienen estado "Terminado"
        res = supabase.table("pedidos").select("*, clientes(nombre_apellido)").eq("estado", "Terminado").order('id', desc=True).execute()
        
        if res.data:
            # Buscador para el historial
            busqueda_historial = st.text_input("🔍 Buscar en el historial:", "").lower()
            
            for p in res.data:
                nombre_cli = p['clientes']['nombre_apellido'] if p.get('clientes') else "Cliente"
                
                # Filtro de búsqueda
                if busqueda_historial in nombre_cli.lower() or busqueda_historial in p['nota'].lower():
                    # Usamos un color gris para que se note que ya pasó
                    with st.expander(f"📦 ID: {p['id']} | {nombre_cli}"):
                        st.write(f"**Color:** {p['color']}")
                        st.write(f"**Notas:** {p['nota']}")
                        st.write(f"**Total que se cobró:** ${float(p['total_operacion']):,.2f}")
                        
                        # Por si te equivocaste y querés volverlo a pendientes
                        if st.button("Reabrir Pedido", key=f"reabrir_{p['id']}"):
                            supabase.table("pedidos").update({"estado": "Pendiente"}).eq("id", p['id']).execute()
                            st.success("El pedido volvió a pendientes")
                            st.rerun()
        else:
            st.info("Aún no tienes pedidos marcados como terminados.")