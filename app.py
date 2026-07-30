import streamlit as st
import time

# --- CONFIGURACIÓN ---
st.set_page_config(page_title="Study Meter", layout="centered", page_icon="📚")

# --- ESTADOS DE LA APP ---
# Posibles estados: 'IDLE' (inicio), 'RUNNING' (corriendo), 'INTERRUPT' (preguntando motivo), 
# 'PAUSED' (en pausa), 'FINISHED' (pantalla final)
if 'timer_state' not in st.session_state:
    st.session_state['timer_state'] = 'IDLE'
if 'interruption_reason' not in st.session_state:
    st.session_state['interruption_reason'] = ""
if 'elapsed_time' not in st.session_state:
    st.session_state['elapsed_time'] = "00:00:00" # Placeholder por ahora

# --- ESTILOS CSS (Para acercarnos al Dark Mode de tus fotos) ---
st.markdown("""
    <style>
    .big-timer { font-size: 80px; font-weight: bold; text-align: center; color: white; margin-bottom: 20px;}
    .center-text { text-align: center; color: white; }
    </style>
""", unsafe_allow_html=True)


# ==========================================
# --- FLUJO DEL CRONÓMETRO ---
# ==========================================

# 1. ESTADO: INICIO (Botón Iniciar Estudio)
if st.session_state['timer_state'] == 'IDLE':
    st.markdown("<h3 class='center-text'>Tu Plan Para Hoy</h3>", unsafe_allow_html=True)
    
    with st.container(border=True):
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.radio("Modo", ["Libre", "Pomodoro"], horizontal=True, label_visibility="collapsed")
            if st.button("▶ INICIAR ESTUDIO", type="primary", use_container_width=True):
                st.session_state['timer_state'] = 'RUNNING'
                st.rerun()

# 2. ESTADO: CORRIENDO (Cronómetro activo)
elif st.session_state['timer_state'] == 'RUNNING':
    st.markdown("<p class='center-text'>Cronómetro</p>", unsafe_allow_html=True)
    st.markdown("<div class='big-timer'>00:00:02</div>", unsafe_allow_html=True) # Acá luego meteremos lógica real de tiempo
    
    col1, col2, col3, col4 = st.columns([1, 1, 2, 2])
    with col2:
        if st.button("❌"):
            st.session_state['timer_state'] = 'IDLE'
            st.rerun()
    with col3:
        if st.button("⏸ Pausar", use_container_width=True):
            st.session_state['timer_state'] = 'INTERRUPT'
            st.rerun()
    with col4:
        if st.button("⏹ Terminar", use_container_width=True):
            st.session_state['timer_state'] = 'FINISHED'
            st.rerun()

# 3. ESTADO: INTERRUPCIÓN (Modal de motivo)
elif st.session_state['timer_state'] == 'INTERRUPT':
    with st.container(border=True):
        st.markdown("<h2 class='center-text'>Interrupción</h2>", unsafe_allow_html=True)
        st.markdown("<p class='center-text'>¿Cuál fue el motivo?</p>", unsafe_allow_html=True)
        
        c1, c2 = st.columns(2)
        motivos = ["Descanso", "Celular", "Llamada", "Comida", "Otro..."]
        
        for i, motivo in enumerate(motivos):
            col = c1 if i % 2 == 0 else c2
            if col.button(motivo, use_container_width=True):
                st.session_state['interruption_reason'] = motivo
                st.session_state['timer_state'] = 'PAUSED'
                st.rerun()
                
        st.divider()
        if st.button("CANCELAR", use_container_width=True):
            st.session_state['timer_state'] = 'RUNNING'
            st.rerun()

# 4. ESTADO: PAUSADO (Esperando reanudar)
elif st.session_state['timer_state'] == 'PAUSED':
    st.markdown("<h1 class='center-text'>⏸ PAUSA</h1>", unsafe_allow_html=True)
    st.markdown(f"<p class='center-text' style='color: gray;'>{st.session_state['interruption_reason']}</p>", unsafe_allow_html=True)
    st.markdown("<div class='big-timer'>00:00:25</div>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("REANUDAR", type="primary", use_container_width=True):
            st.session_state['timer_state'] = 'RUNNING'
            st.rerun()

# 5. ESTADO: FINALIZADO (Clasificar la sesión)
elif st.session_state['timer_state'] == 'FINISHED':
    st.markdown("<h2 class='center-text'>Sesión Finalizada</h2>", unsafe_allow_html=True)
    st.markdown("<p class='center-text'>Completa los datos de tu sesión.</p>", unsafe_allow_html=True)
    
    st.subheader("MATERIA")
    materias = ["Física 2", "Estabilidad", "Álgebra", "Física 1", "Programación", "Probabilidad"]
    materia_sel = st.radio("Selecciona", materias, horizontal=True, label_visibility="collapsed")
    
    st.divider()
    
    st.subheader("MÉTODO")
    metodos = ["Resumir", "Leer", "Práctica", "Transcribir teoría", "De Todo"]
    metodo_sel = st.radio("Método", metodos, horizontal=True, label_visibility="collapsed")
    
    st.divider()
    
    if st.button("CONTINUAR ➔", type="primary", use_container_width=True):
        st.toast(f"Guardando sesión de {materia_sel} ({metodo_sel})...")
        # Acá iría tu función para subir a Google Sheets
        st.session_state['timer_state'] = 'IDLE'
        time.sleep(1)
        st.rerun()
