import streamlit as st
import time
import streamlit.components.v1 as components
import pandas as pd
from datetime import datetime, date
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import altair as alt

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Study Meter", layout="wide", page_icon="📚")

# --- CSS MEJORADO (Tarjetas más compactas) ---
st.markdown("""
    <style>
    .stApp { background-color: #0f172a; color: #f8fafc; }
    .stTabs [data-baseweb="tab-list"] { justify-content: center; background-color: transparent; gap: 20px; border-bottom: 1px solid #1e293b; }
    .stTabs [data-baseweb="tab"] { color: #94a3b8; font-weight: 600; font-size: 16px; padding-bottom: 10px; }
    .stTabs [aria-selected="true"] { color: #0ea5e9 !important; border-bottom: 3px solid #0ea5e9 !important; }
    
    /* Achicamos el padding de 20px a 14px para que todo sea más compacto */
    [data-testid="stVerticalBlock"] > [style*="flex-direction: column;"] > [data-testid="stVerticalBlock"] { 
        background-color: #162032; border-radius: 12px; padding: 14px; border: 1px solid #334155; 
    }
    
    [data-testid="baseButton-primary"] { background-color: #0ea5e9; border-color: #0ea5e9; color: white; border-radius: 8px; font-weight: bold; }
    [data-testid="baseButton-primary"]:hover { background-color: #0284c7; border-color: #0284c7; }
    [data-testid="baseButton-secondary"] { background-color: #334155; border-color: #334155; color: white; border-radius: 8px; }
    [data-testid="baseButton-secondary"]:hover { border-color: #94a3b8; }
    [data-testid="stMetricValue"] { color: #f8fafc; font-size: 2.2rem; font-weight: 700; }
    [data-testid="stMetricLabel"] { color: #94a3b8; font-size: 0.9rem; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; }
    header {visibility: hidden;}
    .color-circle { width: 24px; height: 24px; border-radius: 50%; margin: 0 auto 10px auto; border: 2px solid #334155; }
    .badge-regular { background-color: #eab308; color: #713f12; padding: 2px 8px; border-radius: 10px; font-size: 10px; font-weight: bold; }
    .badge-aprobada { background-color: #22c55e; color: #14532d; padding: 2px 8px; border-radius: 10px; font-size: 10px; font-weight: bold; }
    .badge-cursando { background-color: #3b82f6; color: #1e3a8a; padding: 2px 8px; border-radius: 10px; font-size: 10px; font-weight: bold; }
    .badge-pendiente { background-color: #64748b; color: #0f172a; padding: 2px 8px; border-radius: 10px; font-size: 10px; font-weight: bold; }
    .badge-libre { background-color: #ef4444; color: #450a0a; padding: 2px 8px; border-radius: 10px; font-size: 10px; font-weight: bold; }
    .nota-box { background-color: #1e293b; border: 1px solid #475569; border-radius: 8px; padding: 15px; text-align: center; margin-top: 15px; }
    </style>
""", unsafe_allow_html=True)

# --- SISTEMA DE GUARDADO EN GOOGLE SHEETS ---
def get_gspread_client():
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    secret_str = st.secrets["google_credentials"]
    try: creds_dict = json.loads(secret_str)
    except: creds_dict = json.loads(secret_str, strict=False)
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    return gspread.authorize(creds)

def guardar_datos():
    try:
        datos = {
            'materias': st.session_state['materias'], 'metodos': st.session_state['metodos'],
            'distracciones': st.session_state['distracciones'], 'historial': st.session_state['historial'],
            'metas': st.session_state['metas'], 'plan_carrera': st.session_state['plan_carrera']
        }
        client = get_gspread_client()
        sheet = client.open('StudyMeterDB').worksheet('database')
        sheet.update_acell('A2', json.dumps(datos))
        return True
    except Exception as e:
        st.error(f"🚨 Error exacto de Google: {e}")
        st.stop()

def cargar_datos():
    try:
        client = get_gspread_client()
        sheet = client.open('StudyMeterDB').worksheet('database')
        valor = sheet.acell('A2').value
        if valor: return json.loads(valor)
    except: return None
    return None

# --- INICIALIZACIÓN DE VARIABLES ---
if 'timer_state' not in st.session_state: st.session_state['timer_state'] = 'IDLE'
if 'study_start' not in st.session_state: st.session_state['study_start'] = 0.0
if 'study_elapsed' not in st.session_state: st.session_state['study_elapsed'] = 0.0
if 'pause_start' not in st.session_state: st.session_state['pause_start'] = 0.0
if 'pause_elapsed' not in st.session_state: st.session_state['pause_elapsed'] = 0.0
if 'interruption_reason' not in st.session_state: st.session_state['interruption_reason'] = ""

if 'datos_cargados' not in st.session_state:
    datos_guardados = cargar_datos()
    if datos_guardados:
        st.session_state['materias'] = datos_guardados.get('materias', [])
        st.session_state['metodos'] = datos_guardados.get('metodos', [])
        st.session_state['distracciones'] = datos_guardados.get('distracciones', [])
        st.session_state['historial'] = datos_guardados.get('historial', [])
        st.session_state['metas'] = datos_guardados.get('metas', [])
        st.session_state['plan_carrera'] = datos_guardados.get('plan_carrera', [])
        for m in st.session_state['metas']:
            if 'nota' not in m: m['nota'] = None
    else:
        st.session_state['materias'] = []
        st.session_state['metodos'] = ["Resumir", "Leer", "Práctica", "Transcribir teoría", "De Todo"]
        st.session_state['distracciones'] = ["Descanso", "Celular", "Llamada", "Comida"]
        st.session_state['historial'] = []
        st.session_state['metas'] = [] 
        st.session_state['plan_carrera'] = []
    st.session_state['datos_cargados'] = True

if len(st.session_state['materias']) > 0 and isinstance(st.session_state['materias'][0], str):
    st.session_state['materias'] = []

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
    c_filt1, c_filt2, c_filt3, c_filt4 = st.columns([1, 2, 2, 2])
    with c_filt1: st.markdown("<div style='margin-top: 30px; color:#94a3b8;'>⚙️ <b>Filtros</b></div>", unsafe_allow_html=True)
    
    nombres_materias = list(set([h['MATERIA'] for h in st.session_state['historial']]))
    nombres_metodos = list(set([h['MÉTODO'] for h in st.session_state['historial']]))
    
    # Se agregaron Keys únicos a los filtros
    f_mat = c_filt2.selectbox("Materias", ["Todas las materias"] + nombres_materias, key="filtro_mat_analitica", label_visibility="collapsed")
    f_hist = c_filt3.selectbox("Historial", ["Todo el Historial", "Últimos 7 días", "Último Mes"], key="filtro_tiempo_analitica", label_visibility="collapsed")
    f_met = c_filt4.selectbox("Métodos", ["Todos los métodos"] + nombres_metodos, key="filtro_met_analitica", label_visibility="collapsed")
    
    st.write("<br>", unsafe_allow_html=True)

    if not st.session_state['historial']:
        st.info("Todavía no hay datos para procesar. ¡Hacé tu primera sesión!")
        return

    df_hist = pd.DataFrame(st.session_state['historial'])
    
    if f_mat != "Todas las materias": df_hist = df_hist[df_hist['MATERIA'] == f_mat]
    if f_met != "Todos los métodos": df_hist = df_hist[df_hist['MÉTODO'] == f_met]
    if f_hist == "Últimos 7 días":
        df_hist['FECHA_OBJ'] = pd.to_datetime(df_hist['FECHA'], format='%d/%m/%Y')
        df_hist = df_hist[df_hist['FECHA_OBJ'] >= (pd.Timestamp.now() - pd.Timedelta(days=7))]
    elif f_hist == "Último Mes":
        df_hist['FECHA_OBJ'] = pd.to_datetime(df_hist['FECHA'], format='%d/%m/%Y')
        df_hist = df_hist[df_hist['FECHA_OBJ'] >= (pd.Timestamp.now() - pd.Timedelta(days=30))]

    if df_hist.empty:
        st.warning("No hay datos para los filtros seleccionados.")
        return

    total_minutos = df_hist['TIEMPO (min)'].sum()
    horas = total_minutos // 60
    minutos = total_minutos % 60
    
    materia_top = df_hist.groupby('MATERIA')['TIEMPO (min)'].sum().idxmax()
    materia_top_min = df_hist.groupby('MATERIA')['TIEMPO (min)'].sum().max()
    top_h = materia_top_min // 60
    top_m = materia_top_min % 60
    
    df_hist['EFIC_NUM'] = df_hist['EFIC.'].str.replace('%','').astype(float)
    efic_promedio = int(df_hist['EFIC_NUM'].mean()) if not df_hist.empty else 0

    c1, c2 = st.columns(2)
    with c1:
        with st.container(border=True): st.metric("TOTAL DE HORAS ESTUDIADAS", f"{horas}h {minutos}m")
    with c2:
        with st.container(border=True): st.metric("MATERIA MÁS ESTUDIADA", f"{materia_top}", f"{top_h}h {top_m}m")
        
    c3, c4 = st.columns(2)
    with c3:
        with st.container(border=True):
            st.caption("EFICIENCIA GLOBAL")
            source_efic = pd.DataFrame({"Cat": ["Eficiencia", "Falta"], "Valor": [efic_promedio, 100-efic_promedio]})
            chart_efic = alt.Chart(source_efic).mark_arc(innerRadius=60).encode(
                theta=alt.Theta(field="Valor", type="quantitative"),
                color=alt.Color(field="Cat", type="nominal", scale=alt.Scale(domain=["Eficiencia", "Falta"], range=["#0ea5e9", "#1e293b"]), legend=None),
                tooltip=['Cat', 'Valor']
            ).properties(height=200)
            st.altair_chart(chart_efic, use_container_width=True)
            st.markdown(f"<div style='text-align:center; margin-top:-140px; font-size:32px; font-weight:bold; color:white;'>{efic_promedio}%</div><div style='height:90px;'></div>", unsafe_allow_html=True)

    with c4:
        with st.container(border=True):
            st.caption("INTERRUPCIONES COMUNES")
            distr_data = pd.DataFrame({
                "Motivo": st.session_state['distracciones'][:5],
                "Frecuencia": [22, 11, 6, 2, 1][:len(st.session_state['distracciones'][:5])]
            })
            chart_dist = alt.Chart(distr_data).mark_bar(color="#f59e0b", cornerRadiusEnd=4, height=15).encode(
                x=alt.X("Frecuencia:Q", axis=alt.Axis(grid=True, tickMinStep=2, title="")),
                y=alt.Y("Motivo:N", sort='-x', axis=alt.Axis(title="", labelColor="#f8fafc", labelFontWeight="bold"))
            ).properties(height=200)
            st.altair_chart(chart_dist, use_container_width=True)

    with st.container(border=True):
        st.caption("TIEMPO POR MATERIA (Minutos)")
        df_g = df_hist.groupby('MATERIA')['TIEMPO (min)'].sum().reset_index()
        color_map = {m['nombre']: m['color'] for m in st.session_state['materias']}
        bars = alt.Chart(df_g).mark_bar(cornerRadiusTop=4).encode(
            x=alt.X("MATERIA:N", title="", axis=alt.Axis(labelAngle=0, labelColor="#f8fafc")),
            y=alt.Y("TIEMPO (min):Q", title=""),
            color=alt.Color("MATERIA:N", scale=alt.Scale(domain=list(color_map.keys()), range=list(color_map.values())), legend=None),
            tooltip=['MATERIA', 'TIEMPO (min)']
        ).properties(height=250)
        st.altair_chart(bars, use_container_width=True)

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
    opciones_materias = [m['nombre'] for m in st.session_state['plan_carrera']]
    req_regulares = st.multiselect("Para cursar necesito REGULAR:", opciones_materias)
    req_aprobadas = st.multiselect("Para cursar necesito APROBADA:", opciones_materias)
    if st.button("Guardar en el Plan", type="primary", use_container_width=True):
        if nombre:
            st.session_state['plan_carrera'].append({
                "id": str(time.time()), "nombre": nombre, "año": anio,
                "estado": estado, "req_regulares": req_regulares, "req_aprobadas": req_aprobadas
            })
            if guardar_datos(): st.rerun()

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
                "meta_horas": meta_horas, "fecha_examen": fecha_examen.isoformat(), 
                "horas_acumuladas": 0.0, "nota": None
            }
            st.session_state['metas'].append(nueva)
            if guardar_datos(): st.rerun()

@st.dialog("Editar Meta")
def dialog_editar_meta(meta_idx):
    meta_actual = st.session_state['metas'][meta_idx]
    nombres_materias = [m["nombre"] for m in st.session_state['materias']]
    try: fecha_obj = date.fromisoformat(meta_actual['fecha_examen'])
    except: fecha_obj = date.today()
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
            if guardar_datos(): st.rerun()

@st.dialog("Asignar Nota Final")
def dialog_asignar_nota(meta_idx):
    meta_actual = st.session_state['metas'][meta_idx]
    st.write(f"**Examen:** {meta_actual['nombre']} ({meta_actual['materia']})")
    nota = st.text_input("NOTA FINAL", placeholder="Ej: 80T + 79P = 79.5 o 8.5")
    c1, c2 = st.columns(2)
    if c1.button("Cancelar", use_container_width=True): st.rerun()
    if c2.button("Guardar Nota", type="primary", use_container_width=True):
        if nota:
            st.session_state['metas'][meta_idx]['nota'] = nota
            if guardar_datos(): st.rerun()

@st.dialog("Nueva Materia Activa")
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
        if guardar_datos(): st.rerun()

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
        if guardar_datos(): st.rerun()

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
                        
                        # --- ACÁ REARMÉ LA TARJETA PARA QUE SEA SÚPER COMPACTA ---
                        html_content = f"""
                        <div style="margin-bottom: 6px;">
                            <span class='{color_clase}' style='font-size: 10px; padding: 2px 6px;'>{row['estado']}</span>
                        </div>
                        <div style="font-size: 15px; font-weight: 700; line-height: 1.2; margin-bottom: 6px;">{row['nombre']}</div>
                        """
                        if row['req_regulares']: html_content += f"<div style='font-size: 11px; color: #94a3b8; margin-bottom: 2px;'><b>Reg:</b> {', '.join(row['req_regulares'])}</div>"
                        if row['req_aprobadas']: html_content += f"<div style='font-size: 11px; color: #94a3b8; margin-bottom: 2px;'><b>Apr:</b> {', '.join(row['req_aprobadas'])}</div>"
                        
                        st.markdown(html_content, unsafe_allow_html=True)
                        st.write("") # Micro espacio
                        if st.button("🗑️", key=f"del_plan_{row['id']}", help="Eliminar del plan"):
                            st.session_state['plan_carrera'] = [m for m in st.session_state['plan_carrera'] if m['id'] != row['id']]
                            if guardar_datos(): st.rerun()

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
            estado_badge = ""
            for plan_mat in st.session_state['plan_carrera']:
                if plan_mat['nombre'] == mat['nombre']:
                    if plan_mat['estado'] == "Cursando":
                        estado_badge = "<div style='margin-top: 8px;'><span class='badge-cursando'>Cursando</span></div>"
                    elif plan_mat['estado'] == "Regular":
                        estado_badge = "<div style='margin-top: 8px;'><span class='badge-regular'>Regular</span></div>"
                    break

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
                    if guardar_datos(): st.rerun()
                    
    st.write("<br>", unsafe_allow_html=True)

    with st.container(border=True):
        c_dist1, c_dist2 = st.columns([4, 1])
        with c_dist1: st.markdown("### Gestionar Distracciones")
        with c_dist2:
            nueva_dist = st.text_input("Nueva Distracción", label_visibility="collapsed", placeholder="Ej: Baño...")
            if st.button("➕ Añadir", type="secondary", key="btn_dist", use_container_width=True):
                if nueva_dist and nueva_dist not in st.session_state['distracciones']:
                    st.session_state['distracciones'].append(nueva_dist)
                    if guardar_datos(): st.rerun()

        cols_dist = st.columns(4)
        for i, dist in enumerate(st.session_state['distracciones']):
            with cols_dist[i % 4]:
                st.markdown(f"""
                <div style="border: 1px solid #334155; border-radius: 12px; padding: 15px; text-align: center; background-color: #1e293b; margin-bottom: 10px;">
                    <div style="color: #94a3b8; font-size: 14px;">⚫</div>
                    <div style="font-weight: 600; font-size: 15px; margin-top: 5px;">{dist}</div>
                </div>
                """, unsafe_allow_html=True)
                if st.button("🗑️", key=f"del_dist_{i}", use_container_width=True):
                    st.session_state['distracciones'].pop(i)
                    if guardar_datos(): st.rerun()

    st.write("<br>", unsafe_allow_html=True)

    with st.container(border=True):
        c_met1, c_met2 = st.columns([4, 1])
        with c_met1: st.markdown("### Gestionar Métodos")
        with c_met2:
            nuevo_met = st.text_input("Nuevo Método", label_visibility="collapsed", placeholder="Ej: Mapa mental...")
            if st.button("➕ Añadir", type="secondary", key="btn_met", use_container_width=True):
                if nuevo_met and nuevo_met not in st.session_state['metodos']:
                    st.session_state['metodos'].append(nuevo_met)
                    if guardar_datos(): st.rerun()

        cols_met = st.columns(4)
        for i, met in enumerate(st.session_state['metodos']):
            with cols_met[i % 4]:
                st.markdown(f"""
                <div style="border: 1px solid #334155; border-radius: 12px; padding: 15px; text-align: center; background-color: #1e293b; margin-bottom: 10px;">
                    <div style="color: #94a3b8; font-size: 14px;">⚫</div>
                    <div style="font-weight: 600; font-size: 15px; margin-top: 5px;">{met}</div>
                </div>
                """, unsafe_allow_html=True)
                if st.button("🗑️", key=f"del_met_{i}", use_container_width=True):
                    st.session_state['metodos'].pop(i)
                    if guardar_datos(): st.rerun()

# ==========================================
# --- VISTA: PÁGINA PRINCIPAL ---
# ==========================================
elif menu_opcion == "Página Principal":
    tabs = st.tabs(["Cronómetro", "Analítica", "Metas", "Historial"])

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
                    
                    if guardar_datos():
                        st.toast(f"¡{minutos_estudio} minutos guardados!")
                        st.session_state['timer_state'] = 'IDLE'
                        st.session_state['study_elapsed'] = 0.0
                        st.session_state['pause_elapsed'] = 0.0
                        time.sleep(1)
                        st.rerun()

    with tabs[1]:
        renderizar_analitica()

    with tabs[2]:
        materias_con_metas = list(set([m['materia'] for m in st.session_state['metas']]))
        
        c_filt1, c_filt2, c_filt3, c_btn3 = st.columns([1, 2, 2, 2])
        with c_filt1: st.markdown("<div style='margin-top: 30px; color:#94a3b8;'>⚙️ <b>Filtros</b></div>", unsafe_allow_html=True)
        # Se agregaron Keys únicos a los filtros
        f_mat_metas = c_filt2.selectbox("Materias", ["Todas las materias"] + materias_con_metas, key="filtro_materias_metas", label_visibility="collapsed")
        f_est_metas = c_filt3.selectbox("Estado", ["Todas", "Actuales", "Pasadas"], key="filtro_estado_metas", label_visibility="collapsed")
        
        with c_btn3:
            st.write("<br>", unsafe_allow_html=True)
            if st.button("➕ Nueva Meta", type="primary", use_container_width=True):
                dialog_nueva_meta()
                
        st.divider()
                
        if not st.session_state['metas']:
            st.info("No tenés metas creadas. Tocá '+ Nueva Meta' para armar tu plan de examen.")
        else:
            metas_filtradas = st.session_state['metas']
            if f_mat_metas != "Todas las materias":
                metas_filtradas = [m for m in metas_filtradas if m['materia'] == f_mat_metas]
                
            hoy = date.today()
            if f_est_metas == "Actuales":
                metas_filtradas = [m for m in metas_filtradas if date.fromisoformat(m['fecha_examen']) >= hoy]
            elif f_est_metas == "Pasadas":
                metas_filtradas = [m for m in metas_filtradas if date.fromisoformat(m['fecha_examen']) < hoy]

            if not metas_filtradas:
                st.warning("No hay metas que coincidan con los filtros seleccionados.")
            else:
                cols = st.columns(3)
                for i, meta in enumerate(metas_filtradas):
                    original_idx = st.session_state['metas'].index(meta)
                    
                    with cols[i % 3]:
                        with st.container(border=True):
                            try: fecha_obj = date.fromisoformat(meta['fecha_examen'])
                            except: fecha_obj = date.today()
                            fecha_str = fecha_obj.strftime('%d/%m/%Y')
                            
                            is_pasada = fecha_obj < hoy
                            etiqueta_estado = "<span style='color: #3b82f6; float:right; font-size: 14px;'>Examen pasado</span>" if is_pasada else ""
                            
                            st.markdown(f"<div style='color: #94a3b8; font-size: 12px; font-weight: bold; text-transform: uppercase;'>{meta['materia']} {etiqueta_estado}</div>", unsafe_allow_html=True)
                            st.markdown(f"### {meta['nombre']}")
                            st.caption(f"📅 {fecha_str}")
                            
                            progreso = min(meta['horas_acumuladas'] / meta['meta_horas'], 1.0)
                            st.progress(progreso)
                            
                            h_acum = int(meta['horas_acumuladas'])
                            m_acum = int((meta['horas_acumuladas'] - h_acum) * 60)
                            
                            pct = int(progreso * 100)
                            st.markdown(f"<div style='display:flex; justify-content:space-between; font-size: 13px; color: #94a3b8;'><span>{h_acum}h {m_acum}m / {meta['meta_horas']}h 00m</span><span>{pct}%</span></div>", unsafe_allow_html=True)
                            
                            if is_pasada:
                                if meta.get('nota'):
                                    st.markdown(f"<div class='nota-box'><b>NOTA FINAL</b>&nbsp;&nbsp;&nbsp;&nbsp; <span style='font-size: 20px; font-weight: 800; color: white;'>{meta['nota']}</span></div>", unsafe_allow_html=True)
                                else:
                                    st.write("<br>", unsafe_allow_html=True)
                                    if st.button("🎖️ Asignar Nota", key=f"nota_{original_idx}", use_container_width=True):
                                        dialog_asignar_nota(original_idx)
                            
                            st.write("<br>", unsafe_allow_html=True)
                            c_ed1, c_ed2 = st.columns(2)
                            if c_ed1.button("✏️ Editar", key=f"edit_meta_{original_idx}", use_container_width=True):
                                dialog_editar_meta(original_idx)
                            if c_ed2.button("🗑️ Eliminar", key=f"del_meta_{original_idx}", use_container_width=True):
                                st.session_state['metas'].pop(original_idx)
                                if guardar_datos(): st.rerun()

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
