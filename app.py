import streamlit as st
import time
import streamlit.components.v1 as components
import pandas as pd

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Study Meter", layout="wide", page_icon="📚")

# --- CSS PARA DARK MODE Y ESTILOS ---
st.markdown("""
    <style>
    /* Forzamos un poco el estilo para acercarnos a las capturas */
    .stApp { background-color: #0f1524; color: white; }
    .stTabs [data-baseweb="tab-list"] { justify-content: center; background-color: transparent; }
    .stTabs [data-baseweb="tab"] { color: #a1a1aa; font-weight: 600; }
    .stTabs [aria-selected="true"] { color: #38bdf8 !important; border-bottom: 2px solid #38bdf8 !important; }
    </style>
""", unsafe_allow_html=True)

# --- INICIALIZACIÓN DE VARIABLES DE ESTADO ---
if 'timer_state' not in st.session_state: st.session_state['timer_state'] = 'IDLE'
if 'study_start' not in st.session_state: st.session_state['study_start'] = 0.0
if 'study_elapsed' not in st.session_state: st.session_state['study_elapsed'] = 0.0
if 'pause_start' not in st.session_state: st.session_state['pause_start'] = 0.0
if 'pause_elapsed' not in st.session_state: st.session_state['pause_elapsed'] = 0.0
if 'interruption_reason' not in st.session_state: st.session_state['interruption_reason'] = ""

# --- FUNCIÓN: RELOJ EN VIVO (JavaScript Inyectado) ---
def render_live_timer(elapsed_seconds, is_running):
    html_code = f"""
    <div id="clock" style="font-size: 80px; font-weight: bold; text-align: center; color: white; font-family: monospace; letter-spacing: 5px;">00:00:00</div>
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
# --- ESTRUCTURA DE PESTAÑAS (TABS) ---
# ==========================================
tabs = st.tabs(["Amigos", "Cronómetro", "Analítica", "Metas", "Historial"])

with tabs[0]:
    st.info("Sección Amigos en construcción...")

# ==========================================
# --- PESTAÑA: CRONÓMETRO ---
# ==========================================
with tabs[1]:
    if st.session_state['timer_state'] == 'IDLE':
        with st.container(border=True):
            st.markdown("<h4 style='text-align: center;'>TU PLAN PARA HOY</h4>", unsafe_allow_html=True)
            st.write("**Final Álgebra**")
            st.progress(0.0)
            st.caption("Faltan 7h 04m / 7h 04m")
            
        with st.container(border=True):
            c1, c2, c3 = st.columns([1,2,1])
            with c2:
                st.radio("Modo", ["Libre", "Pomodoro"], horizontal=True, label_visibility="collapsed")
                if st.button("▶ INICIAR ESTUDIO", type="primary", use_container_width=True):
                    st.session_state['study_start'] = time.time()
                    st.session_state['timer_state'] = 'RUNNING'
                    st.rerun()

    elif st.session_state['timer_state'] == 'RUNNING':
        st.markdown("<p style='text-align: center; color: #a1a1aa;'>Cronómetro</p>", unsafe_allow_html=True)
        
        current_elapsed = st.session_state['study_elapsed'] + (time.time() - st.session_state['study_start'])
        render_live_timer(current_elapsed, True)
        
        c1, c2, c3 = st.columns([1,1,1])
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
            if st.button("⏹ Terminar", use_container_width=True):
                st.session_state['study_elapsed'] += time.time() - st.session_state['study_start']
                st.session_state['timer_state'] = 'FINISHED'
                st.rerun()

    elif st.session_state['timer_state'] == 'INTERRUPT':
        with st.container(border=True):
            st.markdown("<h2 style='text-align: center;'>Interrupción</h2>", unsafe_allow_html=True)
            st.markdown("<p style='text-align: center; color: #a1a1aa;'>¿Cuál fue el motivo?</p>", unsafe_allow_html=True)
            
            motivos = ["Descanso", "Celular", "Llamada", "Comida", "Otro..."]
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
        st.markdown(f"<p style='text-align: center; color: #a1a1aa;'>{st.session_state['interruption_reason']}</p>", unsafe_allow_html=True)
        
        current_pause = st.session_state['pause_elapsed'] + (time.time() - st.session_state['pause_start'])
        render_live_timer(current_pause, True)
        
        c1, c2, c3 = st.columns([1,2,1])
        with c2:
            if st.button("REANUDAR", type="primary", use_container_width=True):
                st.session_state['study_start'] = time.time()
                st.session_state['timer_state'] = 'RUNNING'
                st.rerun()

    elif st.session_state['timer_state'] == 'FINISHED':
        st.markdown("<h2 style='text-align: center;'>Sesión Finalizada</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #a1a1aa;'>Completa los datos de tu sesión.</p>", unsafe_allow_html=True)
        
        with st.container(border=True):
            st.subheader("MATERIA")
            materia_sel = st.radio("Materia", ["Física 2", "Estabilidad", "Álgebra", "Física 1", "Programación", "Probabilidad"], horizontal=True, label_visibility="collapsed")
            
            st.divider()
            
            st.subheader("MÉTODO")
            metodo_sel = st.radio("Método", ["Resumir", "Leer", "Práctica", "Transcribir teoría", "De Todo"], horizontal=True, index=4, label_visibility="collapsed")
            
        st.write("")
        if st.button("CONTINUAR ➔", type="primary", use_container_width=True):
            st.toast("¡Sesión guardada!")
            st.session_state['timer_state'] = 'IDLE'
            st.session_state['study_elapsed'] = 0.0
            st.session_state['pause_elapsed'] = 0.0
            time.sleep(1.5)
            st.rerun()

# ==========================================
# --- PESTAÑA: ANALÍTICA ---
# ==========================================
with tabs[2]:
    c1, c2 = st.columns(2)
    with c1:
        with st.container(border=True):
            st.caption("TOTAL DE HORAS ESTUDIADAS")
            st.markdown("<h2>67h 49m</h2>", unsafe_allow_html=True)
    with c2:
        with st.container(border=True):
            st.caption("MATERIA MÁS ESTUDIADA")
            st.markdown("<h2>FÍSICA 2</h2>", unsafe_allow_html=True)
            st.caption("67h 49m")
            
    st.info("Acá vamos a conectar los gráficos reales de eficiencia e interrupciones en los próximos pasos.")

# ==========================================
# --- PESTAÑA: METAS ---
# ==========================================
with tabs[3]:
    c1, c2, c3 = st.columns(3)
    with c1:
        with st.container(border=True):
            st.caption("FÍSICA 2 - Examen pasado")
            st.markdown("### Parcial 2")
            st.progress(0.70)
            st.caption("28h 02m / 40h 00m")
    with c2:
        with st.container(border=True):
            st.caption("FÍSICA 2 - Examen pasado")
            st.markdown("### Recuperatorio 1er parcial")
            st.progress(0.30)
            st.caption("3h 33m / 12h 00m")
    with c3:
        with st.container(border=True):
            st.caption("ESTABILIDAD - Examen pasado")
            st.markdown("### Global Estabilidad")
            st.progress(0.0)
            st.caption("0h 00m / 8h 00m")

# ==========================================
# --- PESTAÑA: HISTORIAL ---
# ==========================================
with tabs[4]:
    historial_data = pd.DataFrame({
        "FECHA": ["2/7/2026", "1/7/2026", "1/7/2026"],
        "MATERIA": ["FÍSICA 2", "FÍSICA 2", "FÍSICA 2"],
        "TIEMPO": ["11 min", "240 min", "103 min"],
        "EFIC.": ["100%", "55%", "78%"]
    })
    st.dataframe(historial_data, hide_index=True, use_container_width=True)
