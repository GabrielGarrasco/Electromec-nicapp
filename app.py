import streamlit as st
import time
import streamlit.components.v1 as components
import pandas as pd
from datetime import datetime, date

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Study Meter", layout="wide", page_icon="📚")

# --- CSS MEJORADO ---
st.markdown("""
    <style>
    .stApp { background-color: #0f172a; color: #f8fafc; }
    
    /* Pestañas */
    .stTabs [data-baseweb="tab-list"] { justify-content: center; background-color: transparent; gap: 20px; border-bottom: 1px solid #1e293b; }
    .stTabs [data-baseweb="tab"] { color: #94a3b8; font-weight: 600; font-size: 16px; padding-bottom: 10px; }
    .stTabs [aria-selected="true"] { color: #0ea5e9 !important; border-bottom: 3px solid #0ea5e9 !important; }
    
    /* Tarjetas (Containers) */
    [data-testid="stVerticalBlock"] > [style*="flex-direction: column;"] > [data-testid="stVerticalBlock"] {
        background-color: #1e293b; border-radius: 12px; padding: 20px; border: 1px solid #334155; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    
    /* Botones primarios y secundarios */
    [data-testid="baseButton-primary"] { background-color: #0ea5e9; border-color: #0ea5e9; color: white; border-radius: 8px; font-weight: bold; }
    [data-testid="baseButton-primary"]:hover { background-color: #0284c7; border-color: #0284c7; }
    [data-testid="baseButton-secondary"] { background-color: #334155; border-color: #334155; color: white; border-radius: 8px; }
    [data-testid="baseButton-secondary"]:hover { border-color: #94a3b8; }
    
    /* Tipografías y métricas */
    [data-testid="stMetricValue"] { color: #f8fafc; font-size: 2.2rem; font-weight: 700; }
    [data-testid="stMetricLabel"] { color: #94a3b8; font-size: 0.9rem; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; }
    </style>
""", unsafe_allow_html=True)

# --- INICIALIZACIÓN DE VARIABLES DINÁMICAS ---
if 'timer_state' not in st.session_state: st.session_state['timer_state'] = 'IDLE'
if 'study_start' not in st.session_state: st.session_state['study_start'] = 0.0
if 'study_elapsed' not in st.session_state: st.session_state['study_elapsed'] = 0.0
if 'pause_start' not in st.session_state: st.session_state['pause_start'] = 0.0
if 'pause_elapsed' not in st.session_state: st.session_state['pause_elapsed'] = 0.0
if 'interruption_reason' not in st.session_state: st.session_state['interruption_reason'] = ""

# Listas personalizables
if 'materias' not in st.session_state: 
    st.session_state['materias'] = ["Física 2", "Estabilidad", "Álgebra", "Física 1", "Programación", "Probabilidad"]
if 'metodos' not in st.session_state: 
    st.session_state['metodos'] = ["Resumir", "Leer", "Práctica", "Transcribir teoría", "De Todo"]
if 'distracciones' not in st.session_state:
    st.session_state['distracciones'] = ["Descanso", "Celular", "Llamada", "Comida", "Otro..."]

# Base de datos local
if 'historial' not in st.session_state: st.session_state['historial'] = []
if 'metas' not in st.session_state: st.session_state['metas'] = [] 

# --- RELOJ EN VIVO (JavaScript) ---
def render_live_timer(elapsed_seconds, is_running):
    html_code = f"""
    <div id="clock" style="font-size: 85px; font-weight: 700; text-align: center; color: #f8fafc; font-family: 'Courier New', Courier, monospace; letter-spacing: 4px; margin: 20px 0;">00:00:00</div>
    <script>
        var elapsedMs = {elapsed_seconds * 1000};
        var isRunning = {'true' if is_running else 'false'};
        var start = Date.now() - elapsedMs;
        function updateClock() {{
            var delta = isRunning ? (Date.now() - start) : elapsedMs;
            var hrs = Math.floor(delta / 3600000).toString().padStart(2, '0');
            var mins = Math.floor((delta % 3600000) / 60000).toString().padStart(2, '0');
            var secs = Math.floor((delta % 60000) / 1000).toString().padStart(2, '0');
            document.getElementById("clock").innerHTML = hrs + ":" + mins + ":" + secs;
        }}
        updateClock();
        if (isRunning) {{ setInterval(updateClock, 1000); }}
    </script>
    """
    components.html(html_code, height=130)

# ==========================================
# --- MODALES (DIALOGS) ---
# ==========================================
@st.dialog("Nueva Meta de Examen")
def dialog_nueva_meta():
    if not st.session_state['materias']:
        st.warning("Primero agregá materias desde el menú 'Organización'.")
        return
        
    nombre = st.text_input("NOMBRE (EJ: PARCIAL 1)")
    materia = st.selectbox("MATERIA", st.session_state['materias'])
    
    col1, col2 = st.columns(2)
    meta_horas = col1.number_input("META (HORAS)", min_value=1, step=1, value=20)
    fecha_examen = col2.date_input("FECHA EXAMEN", min_value=date.today())
    
    st.write("<br>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    if c1.button("Cancelar", use_container_width=True):
        st.rerun()
    if c2.button("Guardar", type="primary", use_container_width=True):
        if nombre:
            nueva = {
                "id": str(time.time()), "nombre": nombre, "materia": materia,
                "meta_horas": meta_horas, "fecha_examen": fecha_examen, "horas_acumuladas": 0.0
            }
            st.session_state['metas'].append(nueva)
            st.rerun()

@st.dialog("Detalle de Sesión (Manual)", width="large")
def dialog_agregar_sesion():
    if not st.session_state['materias']:
        st.warning("Agregá materias en 'Organización' para poder registrar sesiones.")
        return

    st.markdown("### Métricas Rápidas")
    col1, col2, col3, col4, col5 = st.columns(5)
    tiempo_neto = col1.number_input("TIEMPO NETO (min)", min_value=1, value=60)
    tiempo_pausa = col3.number_input("TIEMPO PAUSA (min)", min_value=0, value=10)
    
    total_min = tiempo_neto + tiempo_pausa
    col2.metric("TOTAL", f"{total_min} min")
    eficiencia = round((tiempo_neto / total_min * 100) if total_min > 0 else 0)
    col5.metric("EFICIENCIA", f"{eficiencia}%")
    
    st.divider()
    c1, c2, c3 = st.columns(3)
    fecha = c1.date_input("FECHA")
    materia = c2.selectbox("MATERIA", st.session_state['materias'], key="mat_manual")
    metodo = c3.selectbox("MÉTODO", st.session_state['metodos'], key="met_manual")
    
    metas_disponibles = [m for m in st.session_state['metas'] if m['materia'] == materia]
    opciones_obj = {"-- Sin vincular --": None}
    for m in metas_disponibles: opciones_obj[f"{m['nombre']} ({m['materia']})"] = m['id']
    objetivo_sel = st.selectbox("VINCULAR OBJETIVO", list(opciones_obj.keys()))
    
    if st.button("Guardar Sesión", type="primary", use_container_width=True):
        nueva_sesion = {
            "FECHA": fecha.strftime("%d/%m/%Y"), "MATERIA": materia, "MÉTODO": metodo,
            "TIEMPO (min)": tiempo_neto, "EFIC.": f"{eficiencia}%"
        }
        st.session_state['historial'].append(nueva_sesion)
        
        id_meta = opciones_obj[objetivo_sel]
        if id_meta:
            for m in st.session_state['metas']:
                if m['id'] == id_meta:
                    m['horas_acumuladas'] += (tiempo_neto / 60)
                    break
        st.rerun()


# ==========================================
# --- MENÚ LATERAL (SIDEBAR) ---
# ==========================================
with st.sidebar:
    st.markdown("### Menú")
    menu_opcion = st.radio("Navegación", ["Página Principal", "Resumen", "Organización"], label_visibility="collapsed")


# ==========================================
# --- VISTA: ORGANIZACIÓN ---
# ==========================================
if menu_opcion == "Organización":
    st.header("Organización")
    st.caption("Añadí o personalizá tus listas. Lo que agregues acá se reflejará en el cronómetro y los historiales.")
    
    # MATERIAS
    with st.container(border=True):
        st.subheader("Gestionar Materias")
        c1, c2 = st.columns([3, 1])
        nueva_mat = c1.text_input("Nombre de la materia", key="nueva_mat")
        if c2.button("+ Nueva Materia", use_container_width=True):
            if nueva_mat and nueva_mat not in st.session_state['materias']:
                st.session_state['materias'].append(nueva_mat)
                st.rerun()
        if st.session_state['materias']:
            st.write("**Actuales:** " + " | ".join([f"`{m}`" for m in st.session_state['materias']]))

    # DISTRACCIONES
    with st.container(border=True):
        st.subheader("Gestionar Distracciones")
        st.caption("Motivos usuales de pausas.")
        c1, c2 = st.columns([3, 1])
        nueva_dist = c1.text_input("Nombre de la distracción", key="nueva_dist")
        if c2.button("+ Nueva Distracción", use_container_width=True):
            if nueva_dist and nueva_dist not in st.session_state['distracciones']:
                st.session_state['distracciones'].append(nueva_dist)
                st.rerun()
        if st.session_state['distracciones']:
            st.write("**Actuales:** " + " | ".join([f"`{d}`" for d in st.session_state['distracciones']]))

    # MÉTODOS
    with st.container(border=True):
        st.subheader("Gestionar Métodos")
        st.caption("Modos de estudio usados comúnmente.")
        c1, c2 = st.columns([3, 1])
        nuevo_met = c1.text_input("Nombre del método", key="nuevo_met")
        if c2.button("+ Nuevo Método", use_container_width=True):
            if nuevo_met and nuevo_met not in st.session_state['metodos']:
                st.session_state['metodos'].append(nuevo_met)
                st.rerun()
        if st.session_state['metodos']:
            st.write("**Actuales:** " + " | ".join([f"`{m}`" for m in st.session_state['metodos']]))


# ==========================================
# --- VISTA: PÁGINA PRINCIPAL / RESUMEN ---
# ==========================================
elif menu_opcion in ["Página Principal", "Resumen"]:
    tabs = st.tabs(["Amigos", "Cronómetro", "Analítica", "Metas", "Historial"])

    with tabs[0]:
        st.info("Sección Amigos en construcción...")

    # --- CRONÓMETRO ---
    with tabs[1]:
        if st.session_state['timer_state'] == 'IDLE':
            col_izq, col_der = st.columns([1, 1.5], gap="large")
            with col_izq:
                st.markdown("### ¿Qué estudiamos hoy?")
                st.caption("Elegí una meta de la pestaña Metas para ver tu progreso acá.")
            with col_der:
                st.write("<br>", unsafe_allow_html=True)
                st.radio("Modo de Estudio", ["Libre", "Pomodoro"], horizontal=True, label_visibility="collapsed")
                if st.button("▶ INICIAR ESTUDIO", type="primary", use_container_width=True):
                    st.session_state['study_start'] = time.time()
                    st.session_state['timer_state'] = 'RUNNING'
                    st.rerun()

        elif st.session_state['timer_state'] == 'RUNNING':
            st.markdown("<p style='text-align: center; color: #94a3b8; font-size: 1.2rem;'>Cronómetro Libre</p>", unsafe_allow_html=True)
            current_elapsed = st.session_state['study_elapsed'] + (time.time() - st.session_state['study_start'])
            render_live_timer(current_elapsed, True)
            
            c1, c2, c3 = st.columns([1, 2, 2])
            with c1:
                if st.button("❌", use_container_width=True):
                    st.session_state['timer_state'] = 'IDLE'
                    st.session_state['study_elapsed'] = 0.0
                    st.rerun()
            with c2:
                if st.button("⏸ Pausar", use_container_width=True):
                    st.session_state['study_elapsed'] += time.time() - st.session_state['study_start']
                    st.session_state['timer_state'] = 'INTERRUPT'
                    st.rerun()
            with c3:
                if st.button("⏹ Terminar", type="primary", use_container_width=True):
                    st.session_state['study_elapsed'] += time.time() - st.session_state['study_start']
                    st.session_state['timer_state'] = 'FINISHED'
                    st.rerun()

        elif st.session_state['timer_state'] == 'INTERRUPT':
            st.markdown("<h2 style='text-align: center;'>Interrupción</h2>", unsafe_allow_html=True)
            st.markdown("<p style='text-align: center; color: #94a3b8;'>¿Cuál fue el motivo?</p>", unsafe_allow_html=True)
            st.write("<br>", unsafe_allow_html=True)
            
            # Ahora usa la lista dinámica de distracciones
            c1, c2 = st.columns(2)
            for i, motivo in enumerate(st.session_state['distracciones']):
                col = c1 if i % 2 == 0 else c2
                if col.button(motivo, use_container_width=True):
                    st.session_state['interruption_reason'] = motivo
                    st.session_state['pause_start'] = time.time()
                    st.session_state['pause_elapsed'] = 0.0
                    st.session_state['timer_state'] = 'PAUSED'
                    st.rerun()
            
            st.divider()
            if st.button("CANCELAR", use_container_width=True):
                st.session_state['timer_state'] = 'RUNNING'
                st.session_state['study_start'] = time.time()
                st.rerun()

        elif st.session_state['timer_state'] == 'PAUSED':
            st.markdown("<h1 style='text-align: center; color: #0ea5e9;'>⏸ PAUSA</h1>", unsafe_allow_html=True)
            st.markdown(f"<p style='text-align: center; color: #94a3b8; font-size: 1.2rem;'>Motivo: {st.session_state['interruption_reason']}</p>", unsafe_allow_html=True)
            current_pause = st.session_state['pause_elapsed'] + (time.time() - st.session_state['pause_start'])
            render_live_timer(current_pause, True)
            
            c1, c2, c3 = st.columns([1, 2, 1])
            with c2:
                if st.button("REANUDAR", type="primary", use_container_width=True):
                    st.session_state['study_start'] = time.time()
                    st.session_state['timer_state'] = 'RUNNING'
                    st.rerun()

        elif st.session_state['timer_state'] == 'FINISHED':
            st.markdown("<h2 style='text-align: center;'>Sesión Finalizada</h2>", unsafe_allow_html=True)
            
            if not st.session_state['materias'] or not st.session_state['metodos']:
                st.error("No hay materias o métodos cargados. Andá al menú 'Organización' para agregarlos.")
                if st.button("Volver al Inicio"):
                    st.session_state['timer_state'] = 'IDLE'
                    st.rerun()
            else:
                with st.container(border=True):
                    materia_sel = st.radio("MATERIA", st.session_state['materias'], horizontal=True)
                    st.divider()
                    
                    metas_filtradas = [m for m in st.session_state['metas'] if m['materia'] == materia_sel]
                    opciones_meta = {"-- Sin vincular --": None}
                    for m in metas_filtradas: opciones_meta[m['nombre']] = m['id']
                    
                    meta_sel = st.selectbox("VINCULAR OBJETIVO", list(opciones_meta.keys()))
                    st.divider()
                    
                    metodo_sel = st.radio("MÉTODO", st.session_state['metodos'], horizontal=True)
                    
                st.write("")
                if st.button("GUARDAR SESIÓN ➔", type="primary", use_container_width=True):
                    minutos_estudio = round(st.session_state['study_elapsed'] / 60)
                    
                    nueva_sesion = {
                        "FECHA": datetime.now().strftime("%d/%m/%Y"),
                        "MATERIA": materia_sel, "MÉTODO": metodo_sel,
                        "TIEMPO (min)": minutos_estudio, "EFIC.": "100%" 
                    }
                    st.session_state['historial'].append(nueva_sesion)
                    
                    id_meta = opciones_meta[meta_sel]
                    if id_meta:
                        for m in st.session_state['metas']:
                            if m['id'] == id_meta:
                                m['horas_acumuladas'] += (minutos_estudio / 60)
                                break
                    
                    st.toast(f"¡{minutos_estudio} minutos guardados!")
                    st.session_state['timer_state'] = 'IDLE'
                    st.session_state['study_elapsed'] = 0.0
                    st.session_state['pause_elapsed'] = 0.0
                    time.sleep(1)
                    st.rerun()

    # --- ANALÍTICA ---
    with tabs[2]:
        if not st.session_state['historial']:
            st.info("Todavía no hay datos para procesar. ¡Hacé tu primera sesión!")
            c1, c2 = st.columns(2)
            with c1:
                with st.container(border=True): st.metric("TOTAL HORAS ESTUDIADAS", "0h 0m")
            with c2:
                with st.container(border=True): st.metric("MATERIA TOP", "-")
        else:
            df_hist = pd.DataFrame(st.session_state['historial'])
            total_minutos = df_hist['TIEMPO (min)'].sum()
            horas = total_minutos // 60
            minutos = total_minutos % 60
            
            materia_top = df_hist.groupby('MATERIA')['TIEMPO (min)'].sum().idxmax()
            materia_top_min = df_hist.groupby('MATERIA')['TIEMPO (min)'].sum().max()
            top_h = materia_top_min // 60
            top_m = materia_top_min % 60

            c1, c2 = st.columns(2)
            with c1:
                with st.container(border=True):
                    st.metric("TOTAL HORAS ESTUDIADAS", f"{horas}h {minutos}m")
            with c2:
                with st.container(border=True):
                    # Acá arreglé el texto fijo para que sea dinámico y limpio
                    st.metric("MATERIA TOP", f"{materia_top}", f"{top_h}h {top_m}m")
                
            st.divider()
            st.markdown("### Tiempo por Materia")
            st.bar_chart(df_hist.groupby('MATERIA')['TIEMPO (min)'].sum(), color="#0ea5e9")

    # --- METAS ---
    with tabs[3]:
        c_btn1, c_btn2, c_btn3 = st.columns([1, 2, 1])
        with c_btn3:
            if st.button("➕ Nueva Meta", type="primary", use_container_width=True):
                dialog_nueva_meta()
                
        if not st.session_state['metas']:
            st.info("No tenés metas creadas. Tocá '+ Nueva Meta' para armar tu plan de examen.")
        else:
            cols = st.columns(3)
            for i, meta in enumerate(st.session_state['metas']):
                with cols[i % 3]:
                    with st.container(border=True):
                        st.caption(f"{meta['materia'].upper()} - Fecha: {meta['fecha_examen'].strftime('%d/%m/%Y')}")
                        st.markdown(f"### {meta['nombre']}")
                        
                        progreso = min(meta['horas_acumuladas'] / meta['meta_horas'], 1.0)
                        st.progress(progreso)
                        
                        h_acum = int(meta['horas_acumuladas'])
                        m_acum = int((meta['horas_acumuladas'] - h_acum) * 60)
                        st.caption(f"{h_acum}h {m_acum}m / {meta['meta_horas']}h 00m")

    # --- HISTORIAL ---
    with tabs[4]:
        c_btn1, c_btn2, c_btn3 = st.columns([1, 2, 1])
        with c_btn3:
            if st.button("➕ Agregar Sesión", type="primary", use_container_width=True):
                dialog_agregar_sesion()
                
        if not st.session_state['historial']:
            st.write("Tu historial está vacío.")
        else:
            df_mostrar = pd.DataFrame(st.session_state['historial']).iloc[::-1]
            st.dataframe(df_mostrar, hide_index=True, use_container_width=True)
