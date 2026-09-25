import streamlit as st
import pandas as pd
import random
import time
from datetime import datetime

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="NEXUS LMS PRO", page_icon="🌌", layout="wide")

# --- LÓGICA DE AUTENTICACIÓN ---
def login_screen():
    st.title("🔐 Acceso al Sistema")
    with st.container():
        password = st.text_input("Introduce la contraseña de Administrador", type="password")
        if st.button("Entrar"):
            if password == "admin123":
                st.session_state['authenticated'] = True
                st.rerun()
            else:
                st.error("Contraseña incorrecta. Inténtalo de nuevo.")

# --- CLASES DE NEGOCIO (EL MOTOR) ---
class Student:
    def __init__(self, student_id, name, email):
        self.id = student_id
        self.name = name
        self.email = email
        self.enrolled_courses = []
        self.grades = []
        self.progress = {} # {course_id: %}
        self.status = "Active"

    def get_average(self):
        return sum(self.grades) / len(self.grades) if self.grades else 0

class Course:
    def __init__(self, course_id, name, category):
        self.id = course_id
        self.name = name
        self.category = category
        self.modules = []

class LMS_Engine:
    def __init__(self):
        self.students = []
        self.courses = []

    def add_student(self, s_id, name, email):
        new_s = Student(s_id, name, email)
        self.students.append(new_s)
        return new_s

    def add_course(self, c_id, name, category):
        new_c = Course(c_id, name, category)
        self.courses.append(new_c)
        return new_c

# --- GESTIÓN DE ESTADO (PERSISTENCIA EN WEB) ---
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False

if 'lms_engine' not in st.session_state:
    engine = LMS_Engine()
    # Datos Seed (Iniciales) para que la web no se vea vacía
    s1 = engine.add_student(1, "Alice Smith", "alice@example.com")
    s2 = engine.add_student(2, "Bob Jones", "bob@example.com")
    s3 = engine.add_student(3, "Charlie Brown", "charlie@example.com")
    s4 = engine.add_student(4, "Diana Prince", "diana@example.com")
    
    c1 = engine.add_course(101, "Python Masterclass", "Programming")
    c2 = engine.add_course(102, "AI & Machine Learning", "Data Science")
    
    for s in engine.students:
        s.enrolled_courses = [c1, c2]
        s.grades = [random.randint(60, 100) for _ in range(3)]
        s.progress = {101: random.randint(10, 90), 102: random.randint(10, 90)}
    
    # Forzar un caso de riesgo para la IA
    s3.grades = [45, 50, 40]
    s3.progress = {101: 20, 102: 15}
    
    st.session_state.lms_engine = engine

# --- FLUJO PRINCIPAL ---
if not st.session_state['authenticated']:
    login_screen()
else:
    # --- SIDEBAR DE NAVEGACIÓN ---
    st.sidebar.image("https://cdn-icons-png.flaticon.com/512/2593/2593344.png", width=100)
    st.sidebar.title("NEXUS Control Panel")
    st.sidebar.caption(f"Admin Mode: ON")
    
    menu = st.sidebar.radio(
        "Navegación",
        ["📊 Dashboard Principal", "👥 Gestión de Alumnos", "📚 Catálogo de Cursos", "📈 Analítica Avanzada", "🌌 NEXUS AI (PRO)"]
    )
    
    st.sidebar.divider()
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state['authenticated'] = False
        st.rerun()

    engine = st.session_state.lms_engine

    # --- MÓDULO 1: DASHBOARD ---
    if menu == "📊 Dashboard Principal":
        st.title("📊 Dashboard Operativo")
        
        # Métricas Top
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Estudiantes Totales", len(engine.students))
        m2.metric("Cursos Activos", len(engine.courses))
        
        avg_all = sum(s.get_average() for s in engine.students) / len(engine.students)
        m3.metric("Promedio General", f"{avg_all:.1f}%")
        
        active_users = len([s for s in engine.students if s.status == "Active"])
        m4.metric("Usuarios Activos", active_users)

        st.divider()

        col_a, col_b = st.columns(2)
        with col_a:
            st.subheader("Resumen de Estudiantes")
            df_students = pd.DataFrame([
                {"Nombre": s.name, "Promedio": round(s.get_average(), 1), "Estado": s.status} 
                for s in engine.students
            ])
            st.dataframe(df_students, use_container_width=True)

        with col_b:
            st.subheader("Actividad Reciente")
            st.write("✅ Curso 'Python' actualizado hace 2h")
            st.write("⚠️ Alerta de riesgo: Charlie Brown")
            st.write("🆕 Nuevo alumno: Elena R.")

    # --- MÓDULO 2: GESTIÓN DE ALUMNOS ---
    elif menu == "👥 Gestión de Alumnos":
        st.title("👥 Gestión de Estudiantes")
        
        with st.expander("➕ Añadir Nuevo Estudiante"):
            with st.form("new_student"):
                name = st.text_input("Nombre Completo")
                email = st.text_input("Email")
                submitted = st.form_submit_button("Registrar")
                if submitted:
                    new_id = len(engine.students) + 1
                    engine.add_student(new_id, name, email)
                    st.success(f"Estudiante {name} registrado con éxito.")
                    st.rerun()

        st.subheader("Listado de Usuarios")
        for s in engine.students:
            with st.container():
                c1, c2, c3, c4 = st.columns([2, 3, 2, 1])
                c1.write(f"**{s.name}**")
                c2.write(f"📧 {s.email}")
                c3.write(f"🎓 {len(s.enrolled_courses)} cursos")
                if c4.button("Ver", key=s.id):
                    st.info(f"Detalles de {s.name}: Promedio {s.get_average():.1f}%")

    # --- MÓDULO 3: CURSOS ---
    elif menu == "📚 Catálogo de Cursos":
        st.title("📚 Catálogo de Cursos")
        
        col_c1, col_c2 = st.columns([1, 2])
        with col_c1:
            st.subheader("Nuevo Curso")
            with st.form("new_course"):
                c_name = st.text_input("Nombre del Curso")
                c_cat = st.selectbox("Categoría", ["Tech", "Business", "Arts", "Science"])
                if st.form_submit_button("Crear"):
                    engine.add_course(len(engine.courses)+100, c_name, c_cat)
                    st.success("Curso creado")
                    st.rerun()

        with col_c2:
            st.subheader("Cursos Disponibles")
            for c in engine.courses:
                st.write(f"**{c.name}** | *{c.category}*")
                st.caption("---------------------------------------")

    # --- MÓDULO 4: ANALÍTICA ---
    elif menu == "📈 Analítica Avanzada":
        st.title("📈 Analítica de Rendimiento")
        
        chart_data = pd.DataFrame({
            'Estudiante': [s.name for s in engine.students],
            'Nota': [s.get_average() for s in engine.students]
        })
        
        st.subheader("Distribución de Notas por Alumno")
        st.bar_chart(chart_data.set_index('Estudiante'))

        st.subheader("Matriz de Progreso")
        # Creación de tabla de calor manual para visualización
        prog_data = []
        for s in engine.students:
            for cid, val in s.progress.items():
                c_name = next(c.name for c in engine.courses if c.id == cid)
                prog_data.append({"Alumno": s.name, "Curso": c_name, "Progreso": val})
        
        st.dataframe(pd.DataFrame(prog_data), use_container_width=True)

    # --- MÓDULO 5: NEXUS AI (EL EFECTO WOW) ---
    elif menu == "🌌 NEXUS AI (PRO)":
        st.title("🌌 NEXUS AI: Autonomous LMS")
        st.write("Sistema de Inteligencia Artificial Activo. Monitorizando patrones de aprendizaje en tiempo real...")
        
        st.divider()
        
        col_ai_1, col_ai_2 = st.columns([1, 2])

        with col_ai_1:
            st.subheader("🤖 Configuración IA")
            st.toggle("Modo Adaptativo", value=True)
            st.toggle("Predicción de Abandono", value=True)
            st.selectbox("Modelo de IA", ["Nexus-Alpha", "Nexus-Omega (High Performance)"])
            st.button("🔄 Forzar Re-entrenamiento")

        with col_ai_2:
            st.subheader("🚨 Alertas Predictivas de Riesgo")
            
            risk_detected = False
            for s in engine.students:
                # Algoritmo de riesgo: Nota < 60 Y progreso < 30
                if s.get_average() < 60 and min(s.progress.values()) < 30:
                    risk_detected = True
                    with st.expander(f"⚠️ RIESGO ALTO: {s.name}", expanded=True):
                        st.error(f"**Patrón detectado:** Descenso de rendimiento y baja interacción.")
                        st.write(f"**Acción recomendada:** Generar ruta de refuerzo en `{next(c.name for c in s.enrolled_courses if c.id == 101)}`")
                        if st.button("Ejecutar Plan de Recuperación IA", key=f"btn_{s.id}"):
                            with st.spinner("IA re-diseñando contenidos..."):
                                time.sleep(2)
                                st.success("✅ Contenidos personalizados enviados al alumno.")

            if not risk_detected:
                st.success("✅ No se detectan anomalías. Todos los estudiantes siguen trayectorias óptimas.")

        st.divider()
        st.subheader("🧠 Generador de Rutas de Aprendizaje (Neural Path)")
        selected_s = st.selectbox("Seleccionar Estudiante para Simulación:", [s.name for s in engine.students])
        student_obj = next(s for s in engine.students if s.name == selected_s)

        # Simulación de UX visual de la IA
        st.write(f"**Ruta Neuronal Sugerida para {student_obj.name}:**")
        steps = ["Evaluación Inicial", "Módulo Base", "Refuerzo Específico", "Proyecto de Aplicación", "Certificación"]
        
        cols = st.columns(len(steps))
        for i, step in enumerate(steps):
            with cols[i]:
                st.markdown(f"**{step}**")
                # Simulación de progreso de la ruta
                progress_val = (i+1) * 20
                st.progress(progress_val)
                if i == 0: st.caption("✅ Completado")
                elif i == 1: st.caption("🔄 En proceso")
                else: st.caption("⏳ Pendiente")
