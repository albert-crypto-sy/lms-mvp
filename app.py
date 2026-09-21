import streamlit as st
import sqlite3
import qrcode
import io
import os
from fpdf import FPDF
from datetime import datetime

# --- CONFIGURACIÓN E INICIALIZACIÓN DE LA BDD ---
DB_NAME = "lms_database.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Configuración global (Logo empresa)
    c.execute('''CREATE TABLE IF NOT EXISTS config (id INTEGER PRIMARY KEY, logo_path TEXT)''')
    # Módulos
    c.execute('''CREATE TABLE IF NOT EXISTS modulos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    titulo TEXT, 
                    sinopsis TEXT, 
                    logo_path TEXT)''')
    # Formadores
    c.execute('''CREATE TABLE IF NOT EXISTS formadores (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    nombre TEXT)''')
    # Preguntas de Test por Módulo
    c.execute('''CREATE TABLE IF NOT EXISTS preguntas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    modulo_id INTEGER, 
                    pregunta TEXT, 
                    opcion_a TEXT, 
                    opcion_b TEXT, 
                    respuesta_correcta TEXT)''')
    # Sesiones / Formaciones
    c.execute('''CREATE TABLE IF NOT EXISTS sesiones (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    fecha TEXT, 
                    ubicacion TEXT, 
                    tipologia TEXT, 
                    modulo_id INTEGER, 
                    formador_id INTEGER, 
                    comentarios TEXT)''')
    # Usuarios / Asistentes
    c.execute('''CREATE TABLE IF NOT EXISTS usuarios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    nombre TEXT, 
                    empresa TEXT, 
                    email TEXT UNIQUE, 
                    password TEXT)''')
    # Asistencias y Aprobados
    c.execute('''CREATE TABLE IF NOT EXISTS asistencias (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    sesion_id INTEGER, 
                    usuario_id INTEGER, 
                    completado INTEGER DEFAULT 0,
                    UNIQUE(sesion_id, usuario_id))''')
    
    # Insertar config inicial si no existe
    c.execute("SELECT COUNT(*) FROM config")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO config (id, logo_path) VALUES (1, '')")
    conn.commit()
    conn.close()

init_db()

# --- FUNCIONES AUXILIARES ---
def get_db():
    return sqlite3.connect(DB_NAME)

def generar_qr(sesion_id):
    # Genera un código QR con el enlace/ID de la sesión
    qr_data = f"http://localhost:8501/?sesion_id={sesion_id}"
    qr = qrcode.QRCode(version=1, box_size=8, border=2)
    qr.add_data(qr_data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

def generar_pdf_diploma(nombre_alumno, fecha, nombre_modulo, logo_empresa_path, logo_modulo_path):
    pdf = FPDF(orientation="L", unit="mm", format="A4")
    pdf.add_page()
    pdf.rect(5, 5, 287, 200) # Marco
    
    # Logo Empresa
    if logo_empresa_path and os.path.exists(logo_empresa_path):
        pdf.image(logo_empresa_path, x=20, y=15, w=35)
    
    # Logo Módulo
    if logo_modulo_path and os.path.exists(logo_modulo_path):
        pdf.image(logo_modulo_path, x=240, y=15, w=35)
        
    pdf.ln(30)
    pdf.set_font("Helvetica", "B", 28)
    pdf.cell(0, 15, "CERTIFICADO DE ASISTENCIA", ln=True, align="C")
    
    pdf.set_font("Helvetica", "", 14)
    pdf.ln(10)
    pdf.cell(0, 10, "Otorgado con orgullo a:", ln=True, align="C")
    
    pdf.set_font("Helvetica", "B", 22)
    pdf.cell(0, 15, nombre_alumno, ln=True, align="C")
    
    pdf.set_font("Helvetica", "", 14)
    pdf.ln(5)
    pdf.cell(0, 10, f"Por haber completado con éxito la formación técnica de:", ln=True, align="C")
    
    pdf.set_font("Helvetica", "B", 18)
    pdf.cell(0, 12, f"Módulo: {nombre_modulo}", ln=True, align="C")
    
    pdf.set_font("Helvetica", "I", 12)
    pdf.ln(10)
    pdf.cell(0, 10, f"Fecha de impartición: {fecha}", ln=True, align="C")
    
    return pdf.output()

# --- NAVEGACIÓN Y SESIÓN ---
st.set_page_config(page_title="LMS Técnico MVP", layout="wide")

if "user" not in st.session_state:
    st.session_state.user = None

# Query Params para auto-registro vía QR
query_params = st.query_params
sesion_qr_id = query_params.get("sesion_id", None)

# --- PANEL LATERAL ---
st.sidebar.title("LMS Técnico")

if st.session_state.user:
    st.sidebar.write(f"👤 **Usuario:** {st.session_state.user['nombre']}")
    st.sidebar.write(f"🔑 **Rol:** {st.session_state.user['rol'].upper()}")
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state.user = None
        st.rerun()
else:
    modo = st.sidebar.radio("Navegación", ["Portal Alumno / QR", "Acceso Admin"])

# --- VISTA 1: PORTAL ALUMNO / REGISTRO POR QR ---
if not st.session_state.user and modo == "Portal Alumno / QR":
    st.title("🎓 Portal del Asistente")
    
    if sesion_qr_id:
        st.info(f"📍 Te estás registrando para la **Sesión ID #{sesion_qr_id}**")
    
    tab1, tab2 = st.tabs(["Iniciar Sesión", "Registro Nuevo Asistente"])
    
    with tab1:
        email_in = st.text_input("Email")
        pass_in = st.text_input("Contraseña", type="password")
        if st.button("Entrar"):
            conn = get_db()
            c = conn.cursor()
            c.execute("SELECT id, nombre FROM usuarios WHERE email=? AND password=?", (email_in, pass_in))
            u = c.fetchone()
            conn.close()
            if u:
                st.session_state.user = {"id": u[0], "nombre": u[1], "rol": "alumno"}
                # Si venía de un QR, registrar asistencia
                if sesion_qr_id:
                    conn = get_db()
                    c = conn.cursor()
                    c.execute("INSERT OR IGNORE INTO asistencias (sesion_id, usuario_id) VALUES (?, ?)", (sesion_qr_id, u[0]))
                    conn.commit()
                    conn.close()
                st.rerun()
            else:
                st.error("Credenciales incorrectas")

    with tab2:
        with st.form("registro_form"):
            nombre = st.text_input("Nombre Completo")
            empresa = st.text_input("Empresa")
            email = st.text_input("Correo Electrónico")
            password = st.text_input("Contraseña deseada", type="password")
            submitted = st.form_submit_button("Registrarse y Confirmar Asistencia")
            
            if submitted:
                if nombre and email and password:
                    try:
                        conn = get_db()
                        c = conn.cursor()
                        c.execute("INSERT INTO usuarios (nombre, empresa, email, password) VALUES (?,?,?,?)", 
                                  (nombre, empresa, email, password))
                        uid = c.lastrowid
                        if sesion_qr_id:
                            c.execute("INSERT INTO asistencias (sesion_id, usuario_id) VALUES (?, ?)", (sesion_qr_id, uid))
                        conn.commit()
                        conn.close()
                        st.success("¡Registro completado con éxito! Ahora inicia sesión.")
                    except sqlite3.IntegrityError:
                        st.error("El email ya está registrado.")
                else:
                    st.warning("Completa los campos obligatorios.")

# --- VISTA 2: ACCESO ADMIN LOGIN ---
elif not st.session_state.user and modo == "Acceso Admin":
    st.title("🔐 Acceso Administrador")
    admin_pass = st.text_input("Clave de Administrador", type="password")
    if st.button("Acceder como Admin"):
        if admin_pass == "admin123": # Clave por defecto para el MVP
            st.session_state.user = {"id": 0, "nombre": "Administrador", "rol": "admin"}
            st.rerun()
        else:
            st.error("Clave incorrecta (Prueba: admin123)")

# --- ÁREA PRIVADA: ALUMNO ---
elif st.session_state.user and st.session_state.user["rol"] == "alumno":
    st.title(f"Bienvenido/a, {st.session_state.user['nombre']}")
    st.subheader("Mis Sesiones y Formaciones")
    
    conn = get_db()
    c = conn.cursor()
    c.execute('''
        SELECT s.id, s.fecha, m.titulo, m.id, a.completado, m.logo_path
        FROM asistencias a
        JOIN sesiones s ON a.sesion_id = s.id
        JOIN modulos m ON s.modulo_id = m.id
        WHERE a.usuario_id = ?
    ''', (st.session_state.user["id"],))
    mis_sesiones = c.fetchall()
    
    if not mis_sesiones:
        st.write("Aún no estás inscrito en ninguna sesión. Escanea el código QR en la formación presencial.")
    else:
        for s_id, fecha, mod_titulo, mod_id, completado, mod_logo in mis_sesiones:
            with st.expander(f"📚 {mod_titulo} - Fecha: {fecha}"):
                if completado == 1:
                    st.success("✅ Test superado y formación completada.")
                    # Generar PDF al vuelo
                    c.execute("SELECT logo_path FROM config WHERE id=1")
                    cfg = c.fetchone()
                    logo_empresa = cfg[0] if cfg else ""
                    
                    pdf_bytes = generar_pdf_diploma(
                        nombre_alumno=st.session_state.user["nombre"],
                        fecha=fecha,
                        nombre_modulo=mod_titulo,
                        logo_empresa_path=logo_empresa,
                        logo_modulo_path=mod_logo
                    )
                    st.download_button(
                        label="📄 Descargar Diploma (PDF)",
                        data=bytes(pdf_bytes),
                        file_name=f"Diploma_{mod_titulo}.pdf",
                        mime="application/pdf"
                    )
                else:
                    st.warning("⚠️ Debes realizar el test de evaluación para obtener el diploma.")
                    # Buscar preguntas del módulo
                    c.execute("SELECT id, pregunta, opcion_a, opcion_b, respuesta_correcta FROM preguntas WHERE modulo_id=?", (mod_id,))
                    preguntas = c.fetchall()
                    
                    if preguntas:
                        with st.form(f"test_form_{s_id}"):
                            respuestas_usuario = {}
                            for p_id, preg, op_a, op_b, corr in preguntas:
                                respuestas_usuario[p_id] = (st.radio(preg, [op_a, op_b], key=f"p_{p_id}"), corr)
                            
                            if st.form_submit_button("Enviar y Finalizar Test"):
                                aprobado = True
                                for p_id, (resp, corr) in respuestas_usuario.items():
                                    if resp != corr:
                                        aprobado = False
                                
                                if aprobado:
                                    c.execute("UPDATE asistencias SET completado=1 WHERE sesion_id=? AND usuario_id=?", (s_id, st.session_state.user["id"]))
                                    conn.commit()
                                    st.success("🎉 ¡Felicidades! Has aprobado el test. Actualiza la página o vuelve a abrir para descargar el diploma.")
                                    st.rerun()
                                else:
                                    st.error("Algunas respuestas son incorrectas. Inténtalo de nuevo.")
                    else:
                        st.info("Esta sesión no tiene test asignado aún.")
    conn.close()

# --- ÁREA PRIVADA: ADMINISTRADOR ---
elif st.session_state.user and st.session_state.user["rol"] == "admin":
    st.title("⚙️ Panel de Administración LMS")
    
    opcion = st.sidebar.selectbox("Gestión", [
        "Configuración Empresa", 
        "Módulos y Test", 
        "Formadores", 
        "Programar Sesiones y QR"
    ])
    
    conn = get_db()
    c = conn.cursor()
    
    # 1. CONFIGURACIÓN
    if opcion == "Configuración Empresa":
        st.subheader("Logo de la Empresa")
        uploaded_logo = st.file_uploader("Subir Logo Empresa", type=["png", "jpg", "jpeg"])
        if uploaded_logo:
            path = os.path.join("logo_empresa.png")
            with open(path, "wb") as f:
                f.write(uploaded_logo.getbuffer())
            c.execute("UPDATE config SET logo_path=? WHERE id=1", (path,))
            conn.commit()
            st.success("Logo actualizado.")
            
    # 2. MÓDULOS Y TEST
    elif opcion == "Módulos y Test":
        st.subheader("Crear Módulo")
        with st.form("modulo_form"):
            titulo = st.text_input("Título del Módulo")
            sinopsis = st.text_area("Sinopsis")
            logo_mod = st.file_uploader("Logo del Módulo", type=["png", "jpg", "jpeg"])
            if st.form_submit_button("Guardar Módulo"):
                mod_path = ""
                if logo_mod:
                    mod_path = f"logo_mod_{titulo}.png"
                    with open(mod_path, "wb") as f:
                        f.write(logo_mod.getbuffer())
                c.execute("INSERT INTO modulos (titulo, sinopsis, logo_path) VALUES (?,?,?)", (titulo, sinopsis, mod_path))
                conn.commit()
                st.success("Módulo creado.")
                
        st.divider()
        st.subheader("Añadir Pregunta de Test a Módulo")
        c.execute("SELECT id, titulo FROM modulos")
        mods = c.fetchall()
        if mods:
            mod_sel = st.selectbox("Seleccionar Módulo", mods, format_func=lambda x: x[1])
            preg = st.text_input("Pregunta")
            op_a = st.text_input("Opción A")
            op_b = st.text_input("Opción B")
            corr = st.selectbox("Respuesta Correcta", [op_a, op_b])
            if st.button("Añadir Pregunta"):
                c.execute("INSERT INTO preguntas (modulo_id, pregunta, opcion_a, opcion_b, respuesta_correcta) VALUES (?,?,?,?,?)",
                          (mod_sel[0], preg, op_a, op_b, corr))
                conn.commit()
                st.success("Pregunta añadida.")

    # 3. FORMADORES
    elif opcion == "Formadores":
        st.subheader("Añadir Formador")
        nombre_f = st.text_input("Nombre del Formador")
        if st.button("Guardar Formador"):
            c.execute("INSERT INTO formadores (nombre) VALUES (?)", (nombre_f,))
            conn.commit()
            st.success("Formador guardado.")

    # 4. SESIONES Y QR
    elif opcion == "Programar Sesiones y QR":
        st.subheader("Programar Nueva Sesión")
        c.execute("SELECT id, titulo FROM modulos")
        mods = c.fetchall()
        c.execute("SELECT id, nombre FROM formadores")
        forms = c.fetchall()
        
        if mods and forms:
            fecha = st.date_input("Fecha de la Sesión").strftime("%d/%m/%Y")
            ubicacion = st.text_input("Ubicación (ej: Aula 1 / Online)")
            tipo = st.selectbox("Tipología", ["Presencial", "Online", "Híbrida"])
            mod_sel = st.selectbox("Módulo Impartido", mods, format_func=lambda x: x[1])
            form_sel = st.selectbox("Formador", forms, format_func=lambda x: x[1])
            coment = st.text_area("Comentarios")
            
            if st.button("Crear Sesión y Generar QR"):
                c.execute("INSERT INTO sesiones (fecha, ubicacion, tipologia, modulo_id, formador_id, comentarios) VALUES (?,?,?,?,?,?)",
                          (fecha, ubicacion, tipo, mod_sel[0], form_sel[0], coment))
                conn.commit()
                st.success("Sesión programada con éxito.")
        else:
            st.warning("Debes crear al menos un Módulo y un Formador primero.")
            
        st.divider()
        st.subheader("Sesiones Existentes y Código QR de Registro")
        c.execute('''
            SELECT s.id, s.fecha, m.titulo, f.nombre 
            FROM sesiones s
            JOIN modulos m ON s.modulo_id = m.id
            JOIN formadores f ON s.formador_id = f.id
        ''')
        sesiones_lista = c.fetchall()
        for s_id, s_fecha, m_tit, f_nom in sesiones_lista:
            col1, col2 = st.columns([2, 1])
            with col1:
                st.write(f"📌 **Sesión #{s_id} - {m_tit}**")
                st.write(f"🗓️ Fecha: {s_fecha} | 👤 Formador: {f_nom}")
            with col2:
                qr_bytes = generar_qr(s_id)
                st.image(qr_bytes, width=150, caption=f"QR Sesión #{s_id}")

    conn.close()
