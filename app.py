import streamlit as st
import time
import streamlit.components.v1 as components
import pandas as pd
from datetime import datetime

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Study Meter", layout="wide", page_icon="📚")

# --- CSS MEJORADO (Dark Mode + Tarjetas) ---
st.markdown("""
    <style>
    .stApp { background-color: #0f1524; color: white; }
    
    /* Estilo de las pestañas */
    .stTabs [data-baseweb="tab-list"] { justify-content: center; background-color: transparent; gap: 20px; }
    .stTabs [data-baseweb="tab"] { color: #a1a1aa; font-weight: 600; font-size: 16px; }
    .stTabs [aria-selected="true"] { color: #38bdf8 !important; border-bottom: 3px solid #38bdf8 !important; }
    
    /* Tarjetas (Containers) más estilizadas */
    [data-testid="stVerticalBlock"] > [style*="flex-direction: column;"] > [data-testid="stVerticalBlock"] {
        background-color: #1e293b;
        border-radius: 15px;
        padding: 20px;
        border: 1px solid #334155;
    }
    
    /* Tipografías y colores de métricas */
    [data-testid="stMetricValue"] { color: #f8fafc; font-size: 2.5rem; font-weight: 700; }
    [data-testid="stMetricLabel"] { color: #94a3b8; font-size: 1rem; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; }
    </style>
""", unsafe_allow_html=True)

# --- INICIALIZACIÓN DE VARIABLES (BASE DE DATOS EN MEMORIA) ---
if 'timer_state' not in st.session_state: st.session_state['timer_state'] = 'IDLE'
if 'study_start' not in st.session_state: st.session_state['study_start'] = 0.0
if 'study_elapsed' not in st.session_state: st.session_state['study_elapsed'] = 0.0
if 'pause_start' not in st.session_state: st.session_state['pause_start'] = 0.0
if 'pause_elapsed' not in st.session_state: st.session_state['pause_elapsed'] = 0.0
if 'interruption_reason' not in st.session_state: st.session_state['interruption_reason'] = ""

# Base de datos dinámica para la sesión
if 'materias' not in st.session_state: 
    st.session_state['materias'] = ["Física 2", "Estabilidad", "Álgebra", "Física 1", "Programación", "Probabilidad"]
if 'metodos' not in st.session_state: 
    st.session_state['metodos'] = ["Resumir", "Leer", "Práctica", "Transcribir teoría", "De Todo"]
if 'historial' not in st.session_state: 
    st.session_state['historial'] = [] # Acá se guardan las sesiones reales

# --- FUNCIÓN: RELOJ EN VIVO (JavaScript) ---
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
    components.html(html_code, height=150)

# ==========================================
# --- TABS (PESTAÑAS PRINCIPALES) ---
# ==========================================
tabs = st.tabs(["Amigos", "Cronómetro", "Analítica", "Metas", "Historial"])

with tabs[0]:
    st.info("Sección Amigos en construcción...")

# ==========================================
# --- PESTAÑA: CRONÓMETRO ---
# ==========================================
with tabs[1]:
    if st.session_state['timer_state'] == 'IDLE':
        col_izq, col_der = st.columns([1, 1.5], gap="large")
        
        with col_izq:
            st.markdown("### TU PLAN PARA HOY")
            st.write("**Final Álgebra**")
            st.progress(0.0)
            st.caption("Faltan 7h 04m / 7h 04m")
            
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
        
        st.write("") # Espaciador
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
        
        motivos = ["Descanso", "Celular", "Llamada", "Comida", "Editado Manualmente", "Otro..."]
        c1, c2 = st.columns(2)
        for i, motivo in enumerate(motivos):
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
        st.markdown("<h1 style='text-align: center; color: #38bdf8;'>⏸ PAUSA</h1>", unsafe_allow_html=True)
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
        st.markdown("<p style='text-align: center; color: #94a3b8;'>Clasificá tu sesión antes de guardarla.</p>", unsafe_allow_html=True)
        st.write("<br>", unsafe_allow_html=True)
        
        materia_sel = st.radio("MATERIA", st.session_state['materias'], horizontal=True)
        st.divider()
        metodo_sel = st.radio("MÉTODO", st.session_state['metodos'], horizontal=True, index=4)
        st.divider()
            
        if st.button("GUARDAR SESIÓN ➔", type="primary", use_container_width=True):
            # Guardamos la info dinámicamente en el historial
            minutos_estudio = round(st.session_state['study_elapsed'] / 60)
            nueva_sesion = {
                "FECHA": datetime.now().strftime("%d/%m/%Y %H:%M"),
                "MATERIA": materia_sel,
                "MÉTODO": metodo_sel,
                "TIEMPO (min)": minutos_estudio,
                "EFIC.": "100%" # Después le agregamos lógica a esto
            }
            st.session_state['historial'].append(nueva_sesion)
            
            st.toast(f"¡{minutos_estudio} minutos de {materia_sel} guardados!")
            
            # Reseteamos el reloj
            st.session_state['timer_state'] = 'IDLE'
            st.session_state['study_elapsed'] = 0.0
            st.session_state['pause_elapsed'] = 0.0
            time.sleep(1)
            st.rerun()

# ==========================================
# --- PESTAÑA: ANALÍTICA (AHORA DINÁMICA) ---
# ==========================================
with tabs[2]:
    if not st.session_state['historial']:
        st.info("Todavía no hay datos. ¡Hacé tu primera sesión en el Cronómetro para ver las estadísticas!")
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
            st.metric("TOTAL DE HORAS ESTUDIADAS", f"{horas}h {minutos}m")
        with c2:
            st.metric("MATERIA MÁS ESTUDIADA", f"{materia_top}", f"{top_h}h {top_m}m")
            
        st.divider()
        st.markdown("### Tiempo por Materia")
        st.bar_chart(df_hist.groupby('MATERIA')['TIEMPO (min)'].sum())

# ==========================================
# --- PESTAÑA: METAS ---
# ==========================================
with tabs[3]:
    st.markdown("### Tus Exámenes y Objetivos")
    st.info("Acá vamos a enlazar la creación manual de materias y fechas de exámenes.")
    
    # Placeholder visual mejorado
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("#### Parcial 2 - Física 2")
        st.progress(0.70)
        st.caption("Progreso actual basado en horas")
    with c2:
        st.markdown("#### Final - Álgebra")
        st.progress(0.10)
        st.caption("Faltan 25 días")

# ==========================================
# --- PESTAÑA: HISTORIAL (AHORA DINÁMICO) ---
# ==========================================
with tabs[4]:
    if not st.session_state['historial']:
        st.write("Tu historial está vacío.")
    else:
        st.markdown("### Historial de Sesiones")
        # Mostramos el DataFrame real del state invertido (lo más nuevo arriba)
        df_mostrar = pd.DataFrame(st.session_state['historial']).iloc[::-1]
        st.dataframe(df_mostrar, hide_index=True, use_container_width=True)
