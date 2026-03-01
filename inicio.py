import streamlit as st
from supabase import create_client
import pandas as pd
from fpdf import FPDF
from datetime import datetime
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

    # -- MENU PRINCIPAL --
    if "vista_actual" not in st.session_state:
        st.session_state.vista_actual = "Menu_Principal"

    # --- DEBAJO DE TU SELECTBOX DE MENÚ ---
    st.sidebar.divider() # Una línea para separar
    st.sidebar.subheader("🏢 Área Mayorista")

    # Botón que activa la vista mayorista
    if st.sidebar.button("📦 Nueva Venta Mayorista", use_container_width=True, key="btn_venta_may"):
        st.session_state.vista_actual = "Nueva_Venta_Mayorista"
        st.rerun()

    # Botón para ver los clientes fijos
    if st.sidebar.button("👥 Mis Mayoristas", use_container_width=True, key="btn_lista_may"):
        st.session_state.vista_actual = "Lista_Mayoristas"
        st.rerun()

    # 1. SI LA VISTA ES EL MENÚ NORMAL, MOSTRAMOS LO DE SIEMPRE
    if st.session_state.vista_actual == "Menu_Principal":   
        # --- OPCIÓN 1: REGISTRAR --
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
                # 1. Traemos los datos
                res = supabase.table("pedidos").select("*").eq("estado", "Pendiente").order('id', desc=True).execute()

                if res.data:
                # --- PUNTO 2: DASHBOARD DE CAJA ---
                    total_operacion_gral = sum(float(p['total_operacion'] or 0) for p in res.data)
                    total_senas_gral = sum(float(p['anticipo_monto'] or 0) for p in res.data)
                    total_calle = total_operacion_gral - total_senas_gral
                
                d1, d2, d3 = st.columns(3)
                with d1:
                    st.metric("💰 TOTAL EN LA CALLE", f"${total_calle:,.2f}")
                with d2:
                    st.metric("🛋️ PEDIDOS ACTIVOS", len(res.data))
                with d3:
                    st.metric("📥 SEÑAS COBRADAS", f"${total_senas_gral:,.2f}")
                
                st.divider()

                # --- BUSCADOR ---
                busqueda = st.text_input("🔍 Buscar por nombre, color o detalle:", "").lower()
                pedidos_mostrados = []
                for p in res.data:
                    cli = supabase.table("clientes").select("nombre_apellido").eq("id", p['cliente_id']).execute()
                    nombre_cli = cli.data[0]['nombre_apellido'] if cli.data else "Cliente"
                    if busqueda in nombre_cli.lower() or busqueda in (p['nota'] or "").lower() or busqueda in (p['color'] or "").lower():
                        pedidos_mostrados.append((p, nombre_cli))

                    # --- LISTADO CON SEMÁFORO DE DÍAS ---
                for p, nombre_cli in pedidos_mostrados:
                    saldo = float(p.get('total_operacion') or 0) - float(p.get('anticipo_monto') or 0)
                    
                    # CÁLCULO DE DÍAS (PUNTO 3)
                    fecha_pedido_str = p.get('fecha_creacion')
                    if fecha_pedido_str:
                        # Convierte la fecha de Supabase a algo que Python entienda
                        fecha_pedido = datetime.fromisoformat(fecha_pedido_str.replace('Z', '+00:00'))
                        hoy = datetime.now(fecha_pedido.tzinfo)
                        dias = (hoy - fecha_pedido).days
                    else:
                        dias = 0

                        # Lógica de colores según tus reglas
                    if dias >= 25:
                        alerta = "🔴"
                        msg_dias = f":red[**URGENTE: {dias} días**]"
                    elif 10 <= dias < 25:
                        alerta = "🟠"
                        msg_dias = f":orange[**EN ESPERA: {dias} días**]"
                    else:
                        alerta = "🟢"
                        msg_dias = f":green[**NUEVO: {dias} días**]"

                    with st.expander(f"{alerta} {dias}d | {nombre_cli} | ID: {p['id']}"):
                        st.write(f"⏱️ Tiempo en taller: {msg_dias}")
                        
                        c1, c2 = st.columns(2)
                        with c1:
                            st.markdown("### 💰 Pago")
                            st.write(f"**Total:** ${float(p['total_operacion']):,.2f}")
                            st.write(f"**Anticipo:** ${float(p['anticipo_monto']):,.2f}")
                            st.warning(f"🚩 Restan: ${saldo:,.2f}")
                        with c2:
                            st.markdown("### 🛋️ Producto")
                            st.write(f"**Color:** {p['color']}")
                            st.write(f"**Notas:** {p['nota']}")
                    
                        # WhatsApp
                        tel = "".join(filter(str.isdigit, str(p.get('cliente_telefono', ''))))
                        if tel:
                            st.link_button("✅ Ir al WhatsApp", f"https://wa.me/{tel}")
                        
                            # PDF
                            if st.button(f"📄 Remito #{p['id']}", key=f"pend_pdf_{p['id']}"):
                                pdf = FPDF()
                                pdf.add_page()
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
                                    st.download_button(
                                        label="⬇️ Descargar",
                                        data=f,
                                        file_name=nom_f,
                                        mime="application/pdf",
                                        key=f"pend_dl_{p['id']}"
                                    )

                        if st.button("✅ Marcar Terminado", key=f"pend_fin_{p['id']}"): # Agregamos 'pend_'
                            supabase.table("pedidos").update({"estado": "Terminado"}).eq("id", p['id']).execute()
                            st.success("¡Pedido finalizado!")
                            st.rerun()
                            
                        # --- OPCIÓN 3: REFORZAR SEÑA  ---
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

                # --- OPCIÓN 4: PEDIDOS TERMINADOS (EL HISTORIAL) ---
        elif opcion == "Pedidos Terminados":
            st.header("✅ Historial de Pedidos Finalizados")
            res = supabase.table("pedidos").select("*, clientes(nombre_apellido)").eq("estado", "Terminado").order('id', desc=True).execute()

            if res.data:
                busqueda_h = st.text_input("🔍 Buscar en el historial (Nombre o detalle):", "").lower()
            
            for p in res.data:
                nombre_cli = p['clientes']['nombre_apellido'] if p.get('clientes') else "Cliente"
                # Calculamos el total para mostrarlo
                total_cobrado = float(p.get('total_operacion') or 0)
                
                if busqueda_h in nombre_cli.lower() or busqueda_h in (p['nota'] or "").lower():
                    with st.expander(f"📦 ID: {p['id']} | {nombre_cli} | Cobrado: ${total_cobrado:,.2f}"):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown("### 💰 Información de Pago")
                            st.write(f"**Total Cobrado:** ${total_cobrado:,.2f}")
                            st.write(f"**Anticipo inicial:** ${float(p['anticipo_monto']):,.2f}")
                        with col2:
                            st.markdown("### 🛋️ Detalle del Producto")
                            st.write(f"**Color:** {p['color']}")
                            st.write(f"**Notas:** {p['nota']}")
                        
                        st.divider()
                        
                        if st.button(f"📄 Generar Remito #{p['id']}", key=f"hist_pdf_{p['id']}"):
                            st.info(f"Generando remito para el pedido #{p['id']}...")

                        # Botón para devolver a pendientes por si se marcó por error
                        if st.button(f"🔄 Reabrir Pedido #{p['id']}", key=f"hist_re_{p['id']}"):
                            supabase.table("pedidos").update({"estado": "Pendiente"}).eq("id", p['id']).execute()
                            st.success("Pedido devuelto a la lista de pendientes")
                            st.rerun()
        else:
            st.info("Aún no tenés pedidos terminados.")

        # 2. SI LA VISTA ES MAYORISTA, MOSTRAMOS LO NUEVO
    elif st.session_state.vista_actual == "Nueva_Venta_Mayorista":
        st.header("📦 Nueva Venta Mayorista")
        
        # 1. Botón para volver
        if st.button("⬅️ Volver al Menú"):
            st.session_state.vista_actual = "Menu_Principal"
            st.rerun()

        # 2. Traemos los mayoristas de la tabla
        res_m = supabase.table("clientes_mayoristas").select("*").execute()
        
        if res_m.data:
            nombres_m = {m['nombre_comercio']: m for m in res_m.data}
            seleccion = st.selectbox("Elegí el Mayorista", list(nombres_m.keys()))
            
            m_info = nombres_m[seleccion]
            st.info(f"📍 Entrega en: {m_info['direccion']} | 📱 WA: {m_info['whatsapp']}")

            with st.form("form_may"):
                col1, col2 = st.columns(2)
                with col1:
                    producto = st.text_input("Producto/Modelo")
                    cantidad = st.number_input("Cantidad", min_value=1)
                with col2:
                    color = st.text_input("Color")
                    precio_u = st.number_input("Precio por Unidad $")
                
                nota = st.text_area("Notas adicionales")
                
                if st.form_submit_button("Cargar Pedido"):
                    total = cantidad * precio_u
                    # Aquí insertamos en la tabla de pedidos normal
                    supabase.table("pedidos").insert({
                        "cliente_id": m_info['id'], # ID del mayorista
                        "color": color,
                        "nota": f"CANT: {cantidad} - {producto}. {nota}",
                        "total_operacion": total,
                        "estado": "Pendiente",
                        "tipo": "Mayorista" # Para diferenciarlos
                    }).execute()
                    st.success("✅ Pedido mayorista cargado con éxito")
        else:
            st.warning("Aún no tenés mayoristas cargados.")
            if st.button("➕ Cargar mi primer mayorista"):
                st.session_state.vista_actual = "Lista_Mayoristas"
                st.rerun()