import streamlit as st
from supabase import create_client
import pandas as pd
from fpdf import FPDF
import urllib.parse

# 1. Configuración de conexión
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

# 3. CONTROL DE ACCESO
if check_password():
    st.set_page_config(page_title="Innova Sofá - Gestión", layout="wide")
    st.sidebar.success("Sesión iniciada")
    st.title("🛋️ Sistema de Gestión Innova Sofá")

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
            # Cambiamos el nombre de la variable para que coincida con la base de datos si es necesario
            telefono = st.text_input("📱 WhatsApp (Sin espacios ni guiones)", placeholder="54911...")
            
            if st.form_submit_button("Guardar Pedido en la Nube"):
                res_cli = supabase.table("clientes").insert({"nombre_apellido": nombre}).execute()
                cli_id = res_cli.data[0]['id']
                
                supabase.table("pedidos").insert({
                    "cliente_id": cli_id,
                    "color": color,
                    "total_operacion": total,
                    "anticipo_monto": anticipo,
                    "anticipo_metodo": metodo,
                    "nota": notas,
                    "cliente_telefono": telefono, # Guardamos el tel aquí
                    "estado": "Pendiente"
                }).execute()
                st.success(f"✅ ¡Pedido de {nombre} guardado!")

    # --- OPCIÓN 2: VER TABLERO ---
    elif opcion == "Ver Pedidos Pendientes":
        st.header("📋 Tablero de Producción")
        res = supabase.table("pedidos").select("*").eq("estado", "Pendiente").order('id', desc=True).execute()
        
        if res.data:
            busqueda = st.text_input("🔍 Buscar por nombre de cliente o detalle:", "").lower()
            pedidos_mostrados = []
            
            for p in res.data:
                cli = supabase.table("clientes").select("nombre_apellido").eq("id", p['cliente_id']).execute()
                nombre_cli = cli.data[0]['nombre_apellido'] if cli.data else "Cliente"
                if busqueda in nombre_cli.lower() or busqueda in (p['nota'] or "").lower() or busqueda in (p['color'] or "").lower():
                    pedidos_mostrados.append((p, nombre_cli))

            total_visible = sum((float(item[0]['total_operacion'] or 0) - float(item[0]['anticipo_monto'] or 0)) for item in pedidos_mostrados)
            st.metric(label="💰 SALDO PENDIENTE (FILTRADO)", value=f"${total_visible:,.2f}")
            st.divider()

            for p, nombre_cli in pedidos_mostrados:
                saldo = float(p.get('total_operacion') or 0) - float(p.get('anticipo_monto') or 0)
                
                with st.expander(f"🆔 {p['id']} | 🪑 {nombre_cli} | SALDO: ${saldo:,.2f}"):
                    c1, c2 = st.columns(2)
                    with c1:
                        st.markdown("### 💰 Pago")
                        st.write(f"**Total:** ${float(p['total_operacion']):,.2f}")
                        st.write(f"**Anticipo:** ${float(p['anticipo_monto']):,.2f}")
                    with c2:
                        st.markdown("### 🛋️ Producto")
                        st.write(f"**Color:** {p['color']}")
                        st.write(f"**Notas:** {p['nota']}")
                    
                    st.divider()
                    
                    # WhatsApp
                    tel = "".join(filter(str.isdigit, str(p.get('cliente_telefono', ''))))
                    if tel:
                        st.link_button("🟢 Ir al WhatsApp", f"https://wa.me/{tel}", type="primary")
                    
                    # PDF
                    if st.button(f"📄 Generar Remito #{p['id']}", key=f"pdf_{p['id']}"):
                        pdf = FPDF()
                        pdf.add_page()
                        pdf.set_font("Arial", "B", 16)
                        pdf.cell(0, 10, "INNOVA SOFA - REMITO", ln=True, align="C")
                        pdf.set_font("Arial", "", 12)
                        pdf.ln(10)
                        pdf.cell(0, 10, f"Cliente: {nombre_cli}", ln=True)
                        pdf.cell(0, 10, f"Color: {p['color']}", ln=True)
                        pdf.cell(0, 10, f"Saldo: ${saldo:,.2f}", ln=True)
                        
                        nom_f = f"Remito_{p['id']}.pdf"
                        pdf.output(nom_f)
                        with open(nom_f, "rb") as f:
                            st.download_button("⬇️ Descargar", f, file_name=nom_f, key=f"dl_{p['id']}")

                    if st.button("✅ Marcar Terminado", key=f"fin_{p['id']}"):
                        supabase.table("pedidos").update({"estado": "Terminado"}).eq("id", p['id']).execute()
                        st.success("¡Pedido finalizado!")
                        st.rerun()
        else:
            st.info("No hay pedidos pendientes.")

    # --- OPCIÓN 3: REFORZAR SEÑA (ESTA SE HABÍA ROTO) ---
    elif opcion == "Reforzar Seña":
        st.header("💰 Reforzar Seña de Pedido")
        # Traemos pedidos pendientes para elegir a quién sumarle plata
        res = supabase.table("pedidos").select("*, clientes(nombre_apellido)").eq("estado", "Pendiente").execute()
        
        if res.data:
            opciones_pedidos = {f"ID {p['id']} - {p['clientes']['nombre_apellido']}": p['id'] for p in res.data}
            seleccion = st.selectbox("Seleccioná el pedido:", list(opciones_pedidos.keys()))
            id_p = opciones_pedidos[seleccion]
            
            monto_extra = st.number_input("Monto del nuevo refuerzo $", min_value=0.0)
            
            if st.button("Sumar a la Seña"):
                # Buscamos el anticipo actual
                pedido_act = supabase.table("pedidos").select("anticipo_monto").eq("id", id_p).single().execute()
                nuevo_total_seña = float(pedido_act.data['anticipo_monto'] or 0) + monto_extra
                
                supabase.table("pedidos").update({"anticipo_monto": nuevo_total_seña}).eq("id", id_p).execute()
                st.success("¡Seña actualizada correctamente!")
        else:
            st.info("No hay pedidos pendientes para reforzar.")

    # --- OPCIÓN 4: TERMINADOS ---
    elif opcion == "Pedidos Terminados":
        st.header("✅ Historial de Finalizados")
        res = supabase.table("pedidos").select("*, clientes(nombre_apellido)").eq("estado", "Terminado").order('id', desc=True).execute()
        
        if res.data:
            for p in res.data:
                nombre_cli = p['clientes']['nombre_apellido'] if p.get('clientes') else "Cliente"
                with st.expander(f"📦 ID: {p['id']} | {nombre_cli}"):
                    st.write(f"**Color:** {p['color']}")
                    if st.button("Reabrir", key=f"re_{p['id']}"):
                        supabase.table("pedidos").update({"estado": "Pendiente"}).eq("id", p['id']).execute()
                        st.rerun()