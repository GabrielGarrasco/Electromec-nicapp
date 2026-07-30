import streamlit as st
import time
import streamlit.components.v1 as components
import pandas as pd
from datetime import datetime, date
import json

# Nuevas herramientas para la Nube
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Study Meter", layout="wide", page_icon="📚")

# --- CSS MEJORADO ---
st.markdown("""
    <style>
    .stApp { background-color: #0f172a; color: #f8fafc; }
    
    .stTabs [data-baseweb="tab-list"] { justify-content: center; background-color: transparent; gap: 20px; border-bottom: 1px solid #1e293b; }
    .stTabs [data-baseweb="tab"] { color: #94a3b8; font-weight: 600; font-size: 16px; padding-bottom: 10px; }
    .stTabs [aria-selected="true"] { color: #0ea5e9 !important; border-bottom: 3px solid #0ea5e9 !important; }
    
    [data-testid="stVerticalBlock"] > [style*="flex-direction: column;"] > [data-testid="stVerticalBlock"] {
        background-color: #162032; border-radius: 12px; padding: 20px; border: 1px solid #334155;
    }
    
    [data-testid="baseButton-primary"] { background-color: #0ea5e9; border-color: #0ea5e9; color: white; border-radius: 8px; font-weight: bold; }
    [data-testid="baseButton-primary"]:hover { background-color: #0284c7; border-color: #0284c7; }
    [data-testid="baseButton-secondary"] { background-color: #334155; border-color: #334155; color: white; border-radius: 8px; }
    [data-testid="baseButton-secondary"]:hover { border-color: #94a3b8; }
    
    [data-testid="stMetricValue"] { color: #f8fafc; font-size: 2.2rem; font-weight: 700; }
    [data-testid="stMetricLabel"] { color: #94a3b8; font-size: 0.9rem; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; }
    
    header {visibility: hidden;}
    
    .color-circle { width: 24px; height: 24px; border-radius: 50%; margin: 0 auto 10px auto; border: 2px solid #334155; }
    
    .badge-regular { background-color: #eab308; color: #713f12; padding: 2px 8px; border-radius: 12px; font-size: 12px; font-weight: bold; }
    .badge-aprobada { background-color: #22c55e; color: #14532d; padding: 2px 8px; border-radius: 12px; font-size: 12px; font-weight: bold; }
    .badge-cursando { background-color: #3b82f6; color: #1e3a8a; padding: 2px 8px; border-radius: 12px; font-size: 12px; font-weight: bold; }
    .badge-pendiente { background-color: #64748b; color: #0f172a; padding: 2px 8px; border-radius: 12px; font-size: 12px; font-weight: bold; }
    .badge-libre { background-color: #ef4444; color: #450a0a; padding: 2px 8px; border-radius: 12px; font-size: 12px; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# --- SISTEMA DE GUARDADO EN GOOGLE SHEETS ---
def get_gspread_client():
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds_dict = json.loads(st.secrets["google_credentials"])
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    return gspread.authorize(creds)

def guardar_datos():
    try:
        datos = {
            'materias': st.session_state['materias'],
            'metodos': st.session_state['metodos'],
            'distracciones': st.session_state['distracciones'],
            'historial': st.session_state['historial'],
            'metas': st.session_state['metas'],
            'plan_carrera': st.session_state['plan_carrera']
        }
        client = get_gspread_client()
        sheet = client.open('StudyMeterDB').worksheet('database')
        # Mandamos el bloque de datos a la celda A2
        sheet.update(values=[[json.dumps(datos)]], range_name="A2")
    except Exception as e:
        st.error(f"Ocurrió un error al guardar en la nube: {e}")

def cargar_datos():
    try:
        client = get_gspread_client()
        sheet = client.open('StudyMeterDB').worksheet('database')
        valor = sheet.acell('A2').value
        if valor:
            return json.loads(valor)
    except:
        return None
    return None

# --- INICIALIZACIÓN DE VARIABLES ---
if 'timer_state' not in st.session_state: st.session_state['timer_state'] = 'IDLE'
if 'study_start' not in st.session_state: st.session_state['study_start'] = 0.0
if 'study_elapsed' not in st.session_state: st.session_state['study_elapsed'] = 0.0
if 'pause_start' not in st.session_state: st.session_state['pause_start'] = 0.0
if 'pause_elapsed' not in st.session_state: st.session_state['pause_elapsed'] = 0.0
if 'interruption_reason' not in st.session_state: st.session_state['interruption_reason'] = ""

# Cargamos los datos desde Sheets solo la primera vez que arranca la app
if 'datos_cargados' not in st.session_state:
    datos_guardados = cargar_datos()
    if datos_guardados:
        st.session_state['materias'] = datos_guardados.get('materias', [])
        st.session_state['metodos'] = datos_guardados.get('metodos', [])
        st.session_state['distracciones'] = datos_guardados.get('distracciones', [])
        st.session_state['historial'] = datos_guardados.get('historial', [])
        st.session_state['metas'] = datos_guardados.get('metas', [])
        st.session_state['plan_carrera'] = datos_guardados.get('plan_carrera', [])
    else:
        st.session_state['materias'] = []
        st.session_state['metodos'] = ["Resumir", "Leer", "Práctica", "Transcribir teoría", "De Todo"]
        st.session_state['distracciones'] = ["Descanso", "Celular", "Llamada", "Comida"]
        st.session_state['historial'] = []
        st.session_state['metas'] = [] 
        st.session_state['plan_carrera'] = []
    
    st.session_state['datos_cargados'] = True

# --- RELOJ EN VIVO ---
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

def renderizar_analitica():
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
            with st.container(border=True): st.metric("TOTAL HORAS ESTUDIADAS", f"{horas}h {minutos}m")
        with c2:
            with st.container(border=True): st.metric("MATERIA TOP", f"{materia_top}", f"{top_h}h {top_m}m")
            
        st.divider()
        st.markdown("### Tiempo por Materia")
        st.bar_chart(df_hist.groupby('MATERIA')['TIEMPO (min)'].sum(), color="#0ea5e9")


# ==========================================
# --- MODALES (DIALOGS) ---
# ==========================================
@st.dialog("Agregar Materia al Plan de Estudios")
def dialog_nueva_materia_plan():
    nombre = st.text_input("Nombre de la materia")
    
    col1, col2 = st.columns(2)
    anio = col1.selectbox("Año de cursado", [1, 2, 3, 4, 5, 6])
    estado = col2.selectbox("Estado actual", ["Pendiente", "Cursando", "Regular", "Aprobada/Promocionada", "Libre/Recursado"])
    
    st.divider()
    st.caption("CORRELATIVIDADES (Opcional)")
    opciones_materias = [m['nombre'] for m in st.session_state['plan_carrera']]
    
    req_regulares = st.multiselect("Para cursar necesito REGULAR:", opciones_materias)
    req_aprobadas = st.multiselect("Para cursar necesito APROBADA:", opciones_materias)
    
    st.write("<br>", unsafe_allow_html=True)
    if st.button("Guardar en el Plan", type="primary", use_container_width=True):
        if nombre:
            st.session_state['plan_carrera'].append({
                "id": str(time.time()), "nombre": nombre, "año": anio,
                "estado": estado, "req_regulares": req_regulares, "req_aprobadas": req_aprobadas
            })
            guardar_datos()
            st.rerun()
        else:
            st.error("Falta el nombre de la materia.")

@st.dialog("Nueva Meta de Examen")
def dialog_nueva_meta():
    nombres_materias = [m["nombre"] for m in st.session_state['materias']]
    if not nombres_materias:
        st.warning("Primero agregá materias activas desde el menú 'Organización'.")
        return
        
    nombre = st.text_input("NOMBRE (EJ: PARCIAL 1)")
    materia = st.selectbox("MATERIA (de tus materias activas)", nombres_materias)
    
    col1, col2 = st.columns(2)
    meta_horas = col1.number_input("META (HORAS)", min_value=1, step=1, value=20)
    fecha_examen = col2.date_input("FECHA EXAMEN", min_value=date.today())
    
    c1, c2 = st.columns(2)
    if c1.button("Cancelar", use_container_width=True): st.rerun()
    if c2.button("Guardar", type="primary", use_container_width=True):
        if nombre:
            nueva = {
                "id": str(time.time()), "nombre": nombre, "materia": materia,
                "meta_horas": meta_horas, "fecha_examen": fecha_examen.isoformat(), "horas_acumuladas": 0.0
            }
            st.session_state['metas'].append(nueva)
            guardar_datos()
            st.rerun()

@st.dialog("Editar Meta")
def dialog_editar_meta(meta_idx):
    meta_actual = st.session_state['metas'][meta_idx]
    nombres_materias = [m["nombre"] for m in st.session_state['materias']]
    
    try:
        fecha_obj = date.fromisoformat(meta_actual['fecha_examen'])
    except:
        fecha_obj = date.today()
        
    idx_materia = nombres_materias.index(meta_actual['materia']) if meta_actual['materia'] in nombres_materias else 0
        
    nombre = st.text_input("NOMBRE", value=meta_actual['nombre'])
    materia = st.selectbox("MATERIA", nombres_materias, index=idx_materia)
    
    col1, col2 = st.columns(2)
    meta_horas = col1.number_input("META (HORAS)", min_value=1, step=1, value=int(meta_actual['meta_horas']))
    fecha_examen = col2.date_input("FECHA EXAMEN", value=fecha_obj)
    
    c1, c2 = st.columns(2)
    if c1.button("Cancelar", use_container_width=True): st.rerun()
    if c2.button("Actualizar", type="primary", use_container_width=True):
        if nombre:
            st.session_state['metas'][meta_idx]['nombre'] = nombre
            st.session_state['metas'][meta_idx]['materia'] = materia
            st.session_state['metas'][meta_idx]['meta_horas'] = meta_horas
            st.session_state['metas'][meta_idx]['fecha_examen'] = fecha_examen.isoformat()
            guardar_datos()
            st.rerun()

@st.dialog("Nueva Materia Activa (Cronómetro)")
def dialog_nueva_materia_activa():
    materias_validas = [m['nombre'] for m in st.session_state['plan_carrera'] if m['estado'] in ["Cursando", "Regular"]]
    materias_ya_activas = [m['nombre'] for m in st.session_state['materias']]
    
    opciones_disponibles = [m for m in materias_validas if m not in materias_ya_activas]
    
    if not opciones_disponibles:
        st.warning("No tenés materias en estado 'Cursando' o 'Regular' disponibles para agregar. Modificá tu Plan de Estudios primero.")
        return
        
    n = st.selectbox("Seleccionar Materia", opciones_disponibles)
    c = st.color_picker("Color Distintivo", "#0ea5e9")
    
    if st.button("Activar Materia", type="primary", use_container_width=True):
        st.session_state['materias'].append({"nombre": n, "color": c})
        guardar_datos()
        st.rerun()

@st.dialog("Detalle de Sesión (Manual)", width="large")
def dialog_agregar_sesion():
    nombres_materias = [m["nombre"] for m in st.session_state['materias']]
    if not nombres_materias:
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
    materia = c2.selectbox("MATERIA", nombres_materias)
    metodo = c3.selectbox("MÉTODO", st.session_state['metodos'])
    
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
        guardar_datos()
        st.rerun()


# ==========================================
# --- MENÚ LATERAL (SIDEBAR) ---
# ==========================================
with st.sidebar:
    st.markdown("## Menú")
    menu_opcion = st.radio("Navegación", ["Página Principal", "Resumen", "Plan de Estudios", "Organización"], label_visibility="collapsed")


# ==========================================
# --- VISTA: PLAN DE ESTUDIOS ---
# ==========================================
if menu_opcion == "Plan de Estudios":
    c_head1, c_head2 = st.columns([4, 1])
    with c_head1:
        st.header("Plan de Estudios")
        st.caption("Gestioná todas las materias de tu carrera y sus correlatividades.")
    with c_head2:
        if st.button("➕ Añadir Materia", type="primary", use_container_width=True):
            dialog_nueva_materia_plan()
            
    st.divider()
    
    if not st.session_state['plan_carrera']:
        st.info("Todavía no agregaste ninguna materia a tu plan de estudios.")
    else:
        df_plan = pd.DataFrame(st.session_state['plan_carrera'])
        anios = sorted(df_plan['año'].unique())
        
        for anio in anios:
            st.markdown(f"### Año {anio}")
            materias_anio = df_plan[df_plan['año'] == anio]
            
            cols = st.columns(3)
            for i, row in materias_anio.reset_index().iterrows():
                with cols[i % 3]:
                    with st.container(border=True):
                        color_clase = "badge-pendiente"
                        if row['estado'] == "Regular": color_clase = "badge-regular"
                        elif row['estado'] == "Aprobada/Promocionada": color_clase = "badge-aprobada"
                        elif row['estado'] == "Cursando": color_clase = "badge-cursando"
                        elif row['estado'] == "Libre/Recursado": color_clase = "badge-libre"
                        
                        st.markdown(f"<span class='{color_clase}'>{row['estado']}</span>", unsafe_allow_html=True)
                        st.markdown(f"#### {row['nombre']}")
                        
                        if row['req_regulares']:
                            st.caption(f"**Req. Regular:** {', '.join(row['req_regulares'])}")
                        if row['req_aprobadas']:
                            st.caption(f"**Req. Aprobada:** {', '.join(row['req_aprobadas'])}")
                        
                        if st.button("🗑️", key=f"del_plan_{row['id']}", help="Eliminar del plan"):
                            st.session_state['plan_carrera'] = [m for m in st.session_state['plan_carrera'] if m['id'] != row['id']]
                            guardar_datos()
                            st.rerun()


# ==========================================
# --- VISTA: RESUMEN (ANALÍTICA DIRECTA) ---
# ==========================================
elif menu_opcion == "Resumen":
    st.header("Tus Estadísticas")
    renderizar_analitica()


# ==========================================
# --- VISTA: ORGANIZACIÓN ---
# ==========================================
elif menu_opcion == "Organización":
    
    with st.container(border=True):
        c_head1, c_head2 = st.columns([4, 1])
        with c_head1:
            st.markdown("### Materias Activas (Cronómetro)")
            st.caption("Añadí acá solo las materias de tu plan que estás cursando o rindiendo AHORA.")
        with c_head2:
            if st.button("➕ Nueva Materia", type="secondary", use_container_width=True):
                dialog_nueva_materia_activa()
                
        cols_mat = st.columns(3)
        for i, mat in enumerate(st.session_state['materias']):
            # --- ACÁ BUSCAMOS EL ESTADO EN EL PLAN DE CARRERA ---
            estado_badge = ""
            for plan_mat in st.session_state['plan_carrera']:
                if plan_mat['nombre'] == mat['nombre']:
                    if plan_mat['estado'] == "Cursando":
                        estado_badge = "<div style='margin-top: 8px;'><span class='badge-cursando'>Cursando</span></div>"
                    elif plan_mat['estado'] == "Regular":
                        estado_badge = "<div style='margin-top: 8px;'><span class='badge-regular'>Regular</span></div>"
                    break # Si ya la encontró, frena la búsqueda

            with cols_mat[i % 3]:
                st.markdown(f"""
                <div style="border: 1px solid #334155; border-radius: 12px; padding: 20px; text-align: center; background-color: #1e293b; margin-bottom: 15px;">
                    <div class="color-circle" style="background-color: {mat['color']};"></div>
                    <div style="font-size: 16px; font-weight: 600;">{mat['nombre']}</div>
                    {estado_badge}
                </div>
                """, unsafe_allow_html=True)
                if st.button("🗑️ Eliminar", key=f"del_mat_{i}", use_container_width=True):
                    st.session_state['materias'].pop(i)
                    guardar_datos()
                    st.rerun()

# ==========================================
# --- VISTA: PÁGINA PRINCIPAL ---
# ==========================================
elif menu_opcion == "Página Principal":
    tabs = st.tabs(["Cronómetro", "Analítica", "Metas", "Historial"])

    # --- CRONÓMETRO ---
    with tabs[0]:
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
            c_back, c_title, c_empty = st.columns([1, 10, 1])
            with c_back:
                if st.button("⬅️ Volver", help="Regresar a Pausa"):
                    st.session_state['timer_state'] = 'PAUSED'
                    st.rerun()
            with c_title:
                st.markdown("<h2 style='text-align: center; margin-top: -10px;'>Sesión Finalizada</h2>", unsafe_allow_html=True)
            
            nombres_materias = [m["nombre"] for m in st.session_state['materias']]
            
            if not nombres_materias or not st.session_state['metodos']:
                st.error("No hay materias o métodos cargados. Andá al menú 'Organización' para agregarlos.")
            else:
                with st.container(border=True):
                    st.caption("MATERIA")
                    materia_sel = st.radio("MATERIA", nombres_materias, horizontal=True, label_visibility="collapsed")
                    st.divider()
                    
                    st.caption("VINCULAR OBJETIVO")
                    metas_filtradas = [m for m in st.session_state['metas'] if m['materia'] == materia_sel]
                    opciones_meta = {"-- Sin vincular --": None}
                    for m in metas_filtradas: opciones_meta[m['nombre']] = m['id']
                    meta_sel = st.selectbox("VINCULAR OBJETIVO", list(opciones_meta.keys()), label_visibility="collapsed")
                    st.divider()
                    
                    st.caption("MÉTODO")
                    metodo_sel = st.radio("MÉTODO", st.session_state['metodos'], horizontal=True, label_visibility="collapsed")
                    
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
                    
                    guardar_datos()
                    st.toast(f"¡{minutos_estudio} minutos guardados!")
                    st.session_state['timer_state'] = 'IDLE'
                    st.session_state['study_elapsed'] = 0.0
                    st.session_state['pause_elapsed'] = 0.0
                    time.sleep(1)
                    st.rerun()

    # --- ANALÍTICA ---
    with tabs[1]:
        renderizar_analitica()

    # --- METAS ---
    with tabs[2]:
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
                        try:
                            fecha_str = date.fromisoformat(meta['fecha_examen']).strftime('%d/%m/%Y')
                        except:
                            fecha_str = meta['fecha_examen']
                            
                        st.caption(f"{meta['materia'].upper()} - Fecha: {fecha_str}")
                        st.markdown(f"### {meta['nombre']}")
                        
                        progreso = min(meta['horas_acumuladas'] / meta['meta_horas'], 1.0)
                        st.progress(progreso)
                        
                        h_acum = int(meta['horas_acumuladas'])
                        m_acum = int((meta['horas_acumuladas'] - h_acum) * 60)
                        st.caption(f"{h_acum}h {m_acum}m / {meta['meta_horas']}h 00m")
                        
                        st.write("")
                        c_ed1, c_ed2 = st.columns(2)
                        if c_ed1.button("✏️ Editar", key=f"edit_meta_{i}", use_container_width=True):
                            dialog_editar_meta(i)
                        if c_ed2.button("🗑️ Eliminar", key=f"del_meta_{i}", use_container_width=True):
                            st.session_state['metas'].pop(i)
                            guardar_datos()
                            st.rerun()

    # --- HISTORIAL ---
    with tabs[3]:
        c_btn1, c_btn2, c_btn3 = st.columns([1, 2, 1])
        with c_btn3:
            if st.button("➕ Agregar Sesión", type="primary", use_container_width=True):
                dialog_agregar_sesion()
                
        if not st.session_state['historial']:
            st.write("Tu historial está vacío.")
        else:
            df_mostrar = pd.DataFrame(st.session_state['historial']).iloc[::-1]
            st.dataframe(df_mostrar, hide_index=True, use_container_width=True)
