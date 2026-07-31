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

# --- CSS MEJORADO ---
st.markdown("""
    <style>
    .stApp { background-color: #0f172a; color: #f8fafc; }
    
    [data-testid="collapsedControl"] { display: none; }
    
    .stTabs [data-baseweb="tab-list"] { justify-content: center; background-color: transparent; gap: 20px; border-bottom: 1px solid #1e293b; }
    .stTabs [data-baseweb="tab"] { color: #94a3b8; font-weight: 600; font-size: 16px; padding-bottom: 10px; }
    .stTabs [aria-selected="true"] { color: #0ea5e9 !important; border-bottom: 3px solid #0ea5e9 !important; }
    
    [data-testid="stVerticalBlock"] > [style*="flex-direction: column;"] > [data-testid="stVerticalBlock"] { 
        background-color: #162032; border-radius: 12px; padding: 12px; border: 1px solid #334155; 
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
    
    .req-cumplido { background-color: rgba(255, 255, 255, 0.12); padding: 6px 10px; border-radius: 6px; margin-bottom: 4px; border: 1px solid rgba(255,255,255,0.05); }
    .req-pendiente { padding: 6px 10px; margin-bottom: 4px; color: #94a3b8; }
    
    div[role="radiogroup"] > label { padding: 10px; border-radius: 8px; transition: 0.3s; margin-bottom: 5px; }
    div[role="radiogroup"] > label:hover { background-color: #1e293b; }
    
    /* CSS para el horario automático (Estilo Bloques) */
    .tabla-horario { width: 100%; border-collapse: collapse; text-align: center; color: #f8fafc; font-family: sans-serif; font-size: 14px; margin-top: 15px; background-color: #0f172a; table-layout: fixed; }
    .tabla-horario th { background-color: #121b29; color: #0ea5e9; padding: 15px 5px; border: 1px solid #2a3441; font-weight: 800; text-transform: uppercase; letter-spacing: 1px; }
    .tabla-horario th:first-child { color: #94a3b8; width: 12%; }
    .tabla-horario td { padding: 10px; border: 1px solid #2a3441; vertical-align: middle; height: 100px; }
    .tabla-horario td:first-child { font-weight: 700; color: #94a3b8; background-color: #121b29; }
    .materia-bloque { background-color: #3b82f6; color: #ffffff; padding: 10px; border-radius: 6px; font-weight: 800; line-height: 1.3; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2); margin: auto; word-wrap: break-word; width: 95%; }
    
    /* CSS para el Historial (Clean Dark) */
    .tabla-historial { width: 100%; border-collapse: collapse; text-align: left; color: #f8fafc; font-family: sans-serif; font-size: 14px; background-color: #0f172a; border: 1px solid #334155; }
    .tabla-historial th { background-color: #162032; color: #94a3b8; padding: 15px; border-bottom: 1px solid #334155; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; }
    .tabla-historial td { padding: 15px; border-bottom: 1px solid #1e293b; vertical-align: middle; }
    .tabla-historial tr:last-child td { border-bottom: none; }
    .tabla-historial tr:hover td { background-color: #1e293b; }
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
            'metas': st.session_state['metas'], 'plan_carrera': st.session_state['plan_carrera'],
            'horarios': st.session_state.get('horarios', [])
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
if 'editando_plan_mat_id' not in st.session_state: st.session_state['editando_plan_mat_id'] = None
if 'current_interruptions' not in st.session_state: st.session_state['current_interruptions'] = []

if 'datos_cargados' not in st.session_state:
    datos_guardados = cargar_datos()
    if datos_guardados:
        st.session_state['materias'] = datos_guardados.get('materias', [])
        st.session_state['metodos'] = datos_guardados.get('metodos', [])
        st.session_state['distracciones'] = datos_guardados.get('distracciones', [])
        st.session_state['historial'] = datos_guardados.get('historial', [])
        st.session_state['metas'] = datos_guardados.get('metas', [])
        st.session_state['plan_carrera'] = datos_guardados.get('plan_carrera', [])
        st.session_state['horarios'] = datos_guardados.get('horarios', [])
        for m in st.session_state['metas']:
            if 'nota' not in m: m['nota'] = None
    else:
        st.session_state['materias'] = []
        st.session_state['metodos'] = ["Resumir", "Leer", "Práctica", "Transcribir teoría", "De Todo"]
        st.session_state['distracciones'] = ["Descanso", "Celular", "Llamada", "Comida"]
        st.session_state['historial'] = []
        st.session_state['metas'] = [] 
        st.session_state['plan_carrera'] = []
        st.session_state['horarios'] = []
    st.session_state['datos_cargados'] = True

if len(st.session_state['materias']) > 0 and isinstance(st.session_state['materias'][0], str):
    st.session_state['materias'] = []

def parse_float_nota(val_str):
    try: return float(str(val_str).replace(',', '.'))
    except: return None

OPCIONES_DIAS = ["---", "Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado"]

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
            todas_interrupciones = []
            if 'INTERRUPCIONES' in df_hist.columns:
                for inter_list in df_hist['INTERRUPCIONES'].dropna():
                    if isinstance(inter_list, list):
                        todas_interrupciones.extend(inter_list)
            
            if not todas_interrupciones:
                st.info("No registraste ninguna interrupción en estas sesiones.")
            else:
                from collections import Counter
                conteo = Counter(todas_interrupciones)
                motivos = []
                frecuencias = []
                for d in st.session_state['distracciones']:
                    if conteo.get(d, 0) > 0:
                        motivos.append(d)
                        frecuencias.append(conteo.get(d, 0))
                
                distr_data = pd.DataFrame({"Motivo": motivos, "Frecuencia": frecuencias})
                if not distr_data.empty:
                    chart_dist = alt.Chart(distr_data).mark_bar(color="#f59e0b").encode(
                        x=alt.X("Frecuencia:Q", axis=alt.Axis(grid=True, tickMinStep=1, title="")),
                        y=alt.Y("Motivo:N", sort='-x', axis=alt.Axis(title="", labelColor="#f8fafc", labelFontWeight="bold"))
                    ).properties(height=200)
                    st.altair_chart(chart_dist, use_container_width=True)

    with st.container(border=True):
        st.caption("TIEMPO POR MATERIA (Minutos)")
        df_g = df_hist.groupby('MATERIA')['TIEMPO (min)'].sum().reset_index()
        color_map = {m['nombre']: m['color'] for m in st.session_state['materias']}
        
        if len(df_g) > 0 and len(color_map) > 0:
            try:
                bars = alt.Chart(df_g).mark_bar().encode(
                    x=alt.X("MATERIA:N", title="", axis=alt.Axis(labelAngle=0, labelColor="#f8fafc")),
                    y=alt.Y("TIEMPO (min):Q", title=""),
                    color=alt.Color("MATERIA:N", scale=alt.Scale(domain=list(color_map.keys()), range=list(color_map.values())), legend=None),
                    tooltip=['MATERIA', 'TIEMPO (min)']
                ).properties(height=250)
                st.altair_chart(bars, use_container_width=True)
            except:
                st.bar_chart(df_g.set_index('MATERIA'), color="#0ea5e9") 
        elif len(df_g) > 0:
            bars = alt.Chart(df_g).mark_bar(color="#0ea5e9").encode(
                x=alt.X("MATERIA:N", title="", axis=alt.Axis(labelAngle=0, labelColor="#f8fafc")),
                y=alt.Y("TIEMPO (min):Q", title=""),
                tooltip=['MATERIA', 'TIEMPO (min)']
            ).properties(height=250)
            st.altair_chart(bars, use_container_width=True)
        else:
            st.info("No hay datos para mostrar el gráfico.")

# ==========================================
# --- MODALES (DIALOGS) ---
# ==========================================
@st.dialog("Detalle de la Materia")
def dialog_detalle_materia(mat_id):
    mat = next((m for m in st.session_state['plan_carrera'] if m['id'] == mat_id), None)
    if not mat: return
    
    # --- MODO EDICIÓN ---
    if st.session_state.get('editando_plan_mat_id') == mat_id:
        st.markdown("### Editar Materia")
        nuevo_nombre = st.text_input("Nombre", value=mat['nombre'])
        
        col1, col2, col3 = st.columns(3)
        opciones_anio = [1, 2, 3, 4, 5, 6]
        idx_anio = opciones_anio.index(int(mat['año'])) if int(mat['año']) in opciones_anio else 0
        nuevo_anio = col1.selectbox("Año", opciones_anio, index=idx_anio)
        
        opciones_cuatri = ["1er Cuatrimestre", "2do Cuatrimestre", "Anual"]
        cuatri_val = mat.get('cuatrimestre', "1er Cuatrimestre")
        idx_cuatri = opciones_cuatri.index(cuatri_val) if cuatri_val in opciones_cuatri else 0
        nuevo_cuatri = col2.selectbox("Cuatrimestre", opciones_cuatri, index=idx_cuatri)
        
        opciones_estado = ["Pendiente", "Cursando", "Regular", "Aprobada/Promocionada", "Libre/Recursado"]
        idx_estado = opciones_estado.index(mat['estado']) if mat['estado'] in opciones_estado else 0
        nuevo_estado = col3.selectbox("Estado", opciones_estado, index=idx_estado)
        
        nueva_nota = mat.get('nota', '')
        nuevos_intentos = mat.get('intentos', ["", "", "", ""])
        while len(nuevos_intentos) < 4: nuevos_intentos.append("") 
        
        horarios_clase = mat.get('horarios_clase', [])
        nuevos_horarios = []
        
        if nuevo_estado == "Aprobada/Promocionada":
            nueva_nota = st.text_input("Nota Final (Opcional)", value=nueva_nota, placeholder="Ej: 8, 9, 10...")
        elif nuevo_estado == "Regular":
            st.caption("Notas de Finales (hasta 4 intentos)")
            c_i1, c_i2 = st.columns(2)
            c_i3, c_i4 = st.columns(2)
            nuevos_intentos[0] = c_i1.text_input("Intento 1", value=nuevos_intentos[0])
            nuevos_intentos[1] = c_i2.text_input("Intento 2", value=nuevos_intentos[1])
            nuevos_intentos[2] = c_i3.text_input("Intento 3", value=nuevos_intentos[2])
            nuevos_intentos[3] = c_i4.text_input("Intento 4", value=nuevos_intentos[3])
        elif nuevo_estado == "Cursando":
            st.caption("Horarios de Cursado (Para tu grilla)")
            while len(horarios_clase) < 3: horarios_clase.append({"dia": "---", "inicio": "", "fin": ""})
            for i in range(3):
                c_d, c_i, c_f = st.columns([2, 1.5, 1.5])
                d_val = horarios_clase[i].get("dia", "---")
                ini_val = horarios_clase[i].get("inicio", horarios_clase[i].get("hora", ""))
                fin_val = horarios_clase[i].get("fin", "")
                
                sel_d = c_d.selectbox(f"Día {i+1}", OPCIONES_DIAS, index=OPCIONES_DIAS.index(d_val) if d_val in OPCIONES_DIAS else 0, key=f"ed_d_{i}")
                val_i = c_i.text_input("Inicio", value=ini_val, placeholder="Ej: 13:45", key=f"ed_i_{i}")
                val_f = c_f.text_input("Fin", value=fin_val, placeholder="Ej: 15:30", key=f"ed_f_{i}")
                
                if sel_d != "---" and val_i.strip():
                    nuevos_horarios.append({"dia": sel_d, "inicio": val_i.strip(), "fin": val_f.strip()})
            
        st.divider()
        st.caption("CORRELATIVIDADES")
        opciones_materias = [m['nombre'] for m in st.session_state['plan_carrera'] if m['id'] != mat_id]
        
        def_reg = [x for x in mat.get('req_regulares', []) if x in opciones_materias]
        def_apr = [x for x in mat.get('req_aprobadas', []) if x in opciones_materias]
        
        nuevas_reg = st.multiselect("Para cursar necesito REGULAR:", opciones_materias, default=def_reg)
        nuevas_apr = st.multiselect("Para cursar necesito APROBADA:", opciones_materias, default=def_apr)
        
        st.write("<br>", unsafe_allow_html=True)
        c_btn1, c_btn2 = st.columns(2)
        if c_btn1.button("Cancelar", use_container_width=True):
            st.session_state['editando_plan_mat_id'] = None
            st.rerun()
        if c_btn2.button("Guardar Cambios", type="primary", use_container_width=True):
            if nuevo_nombre:
                estado_final = nuevo_estado
                nota_definitiva = nueva_nota
                
                if nuevo_estado == "Regular":
                    last_val = None
                    cant_intentos = 0
                    for val in nuevos_intentos:
                        if val.strip():
                            last_val = val.strip()
                            cant_intentos += 1
                    
                    if last_val:
                        val_num = parse_float_nota(last_val)
                        if val_num is not None:
                            if val_num >= 6:
                                estado_final = "Aprobada/Promocionada"
                                nota_definitiva = last_val
                            elif cant_intentos >= 4:
                                estado_final = "Libre/Recursado"
                
                mat['nombre'] = nuevo_nombre
                mat['año'] = nuevo_anio
                mat['cuatrimestre'] = nuevo_cuatri
                mat['estado'] = estado_final
                mat['req_regulares'] = nuevas_reg
                mat['req_aprobadas'] = nuevas_apr
                mat['nota'] = nota_definitiva
                mat['intentos'] = nuevos_intentos
                mat['horarios_clase'] = nuevos_horarios
                
                st.session_state['editando_plan_mat_id'] = None
                if guardar_datos(): st.rerun()
            else:
                st.error("Falta el nombre.")
                
    # --- MODO LECTURA ---
    else:
        st.markdown(f"### {mat['nombre']}")
        cuatri = mat.get('cuatrimestre', 'No definido')
        
        info_str = f"**Año:** {mat['año']} | **Cuatrimestre:** {cuatri} | **Estado:** {mat['estado']}"
        if mat['estado'] == "Aprobada/Promocionada" and mat.get('nota'):
            info_str += f" | **Nota:** {mat['nota']}"
        st.markdown(info_str)
        
        intentos_guardados = mat.get('intentos', [])
        intentos_validos = [i for i in intentos_guardados if i.strip()]
        if intentos_validos:
            st.caption(f"📝 Intentos registrados: {', '.join(intentos_validos)}")
            
        horarios = mat.get('horarios_clase', [])
        if mat['estado'] == "Cursando" and horarios:
            for hc in horarios:
                rango = f"{hc['inicio']} a {hc['fin']}" if hc.get('fin') else hc['inicio']
                st.caption(f"🕒 **{hc['dia']}:** {rango}")
            
        st.divider()
        
        def is_met(m_name, req_type):
            target = next((m for m in st.session_state['plan_carrera'] if m['nombre'] == m_name), None)
            if not target: return False
            if req_type == 'reg': return target['estado'] in ["Regular", "Aprobada/Promocionada"]
            return target['estado'] == "Aprobada/Promocionada"

        st.markdown("#### Correlatividades")
        if not mat.get('req_regulares') and not mat.get('req_aprobadas'):
            st.caption("No tiene correlatividades previas.")
            
        if mat.get('req_regulares'):
            st.write("**Para cursar requiere REGULAR:**")
            for r in mat['req_regulares']:
                cumple = is_met(r, 'reg')
                div_class = "req-cumplido" if cumple else "req-pendiente"
                icon = "✅" if cumple else "⏳"
                st.markdown(f"<div class='{div_class}'>{icon} {r}</div>", unsafe_allow_html=True)
                
        if mat.get('req_aprobadas'):
            st.write("**Para cursar requiere APROBADA:**")
            for r in mat['req_aprobadas']:
                cumple = is_met(r, 'apr')
                div_class = "req-cumplido" if cumple else "req-pendiente"
                icon = "✅" if cumple else "⏳"
                st.markdown(f"<div class='{div_class}'>{icon} {r}</div>", unsafe_allow_html=True)
                
        destraba_reg = [m['nombre'] for m in st.session_state['plan_carrera'] if mat['nombre'] in m.get('req_regulares', [])]
        destraba_apr = [m['nombre'] for m in st.session_state['plan_carrera'] if mat['nombre'] in m.get('req_aprobadas', [])]
        
        if destraba_reg or destraba_apr:
            st.divider()
            st.markdown("#### Destraba")
            for d in destraba_reg:
                st.markdown(f"<div class='req-pendiente'>🔓 {d} (Para cursar)</div>", unsafe_allow_html=True)
            for d in destraba_apr:
                st.markdown(f"<div class='req-pendiente'>🎓 {d} (Para rendir/cursar)</div>", unsafe_allow_html=True)

        st.divider()
        c_del, c_edit = st.columns(2)
        if c_del.button("🗑️ Eliminar", type="secondary", use_container_width=True):
            st.session_state['plan_carrera'] = [m for m in st.session_state['plan_carrera'] if m['id'] != mat_id]
            if guardar_datos(): st.rerun()
        if c_edit.button("✏️ Editar", type="primary", use_container_width=True):
            st.session_state['editando_plan_mat_id'] = mat_id
            st.rerun()

@st.dialog("Agregar Materia al Plan de Estudios")
def dialog_nueva_materia_plan():
    nombre = st.text_input("Nombre de la materia")
    
    col1, col2, col3 = st.columns(3)
    anio = col1.selectbox("Año", [1, 2, 3, 4, 5, 6])
    cuatri = col2.selectbox("Cuatrimestre", ["1er Cuatrimestre", "2do Cuatrimestre", "Anual"])
    estado = col3.selectbox("Estado", ["Pendiente", "Cursando", "Regular", "Aprobada/Promocionada", "Libre/Recursado"])
    
    nota_final = ""
    intentos = ["", "", "", ""]
    nuevos_horarios = []
    
    if estado == "Aprobada/Promocionada":
        nota_final = st.text_input("Nota Final (Opcional)", placeholder="Ej: 8, 9, 10...")
    elif estado == "Regular":
        st.caption("Notas de Finales (hasta 4 intentos)")
        c_i1, c_i2 = st.columns(2)
        c_i3, c_i4 = st.columns(2)
        intentos[0] = c_i1.text_input("Intento 1")
        intentos[1] = c_i2.text_input("Intento 2")
        intentos[2] = c_i3.text_input("Intento 3")
        intentos[3] = c_i4.text_input("Intento 4")
    elif estado == "Cursando":
        st.caption("Horarios de Cursado (Para tu grilla)")
        for i in range(3):
            c_d, c_i, c_f = st.columns([2, 1.5, 1.5])
            sel_d = c_d.selectbox(f"Día {i+1}", OPCIONES_DIAS, key=f"nvo_d_{i}")
            val_i = c_i.text_input("Inicio", placeholder="Ej: 13:45", key=f"nvo_i_{i}")
            val_f = c_f.text_input("Fin", placeholder="Ej: 16:00", key=f"nvo_f_{i}")
            
            if sel_d != "---" and val_i.strip():
                nuevos_horarios.append({"dia": sel_d, "inicio": val_i.strip(), "fin": val_f.strip()})
        
    st.divider()
    st.caption("CORRELATIVIDADES (Opcional)")
    opciones_materias = [m['nombre'] for m in st.session_state['plan_carrera']]
    req_regulares = st.multiselect("Para cursar necesito REGULAR:", opciones_materias)
    req_aprobadas = st.multiselect("Para cursar necesito APROBADA:", opciones_materias)
    
    st.write("<br>", unsafe_allow_html=True)
    if st.button("Guardar en el Plan", type="primary", use_container_width=True):
        if nombre:
            estado_final = estado
            nota_def = nota_final
            
            if estado == "Regular":
                last_val = None
                cant_intentos = 0
                for v in intentos:
                    if v.strip():
                        last_val = v.strip()
                        cant_intentos += 1
                
                if last_val:
                    val_num = parse_float_nota(last_val)
                    if val_num is not None:
                        if val_num >= 6:
                            estado_final = "Aprobada/Promocionada"
                            nota_def = last_val
                        elif cant_intentos >= 4:
                            estado_final = "Libre/Recursado"

            st.session_state['plan_carrera'].append({
                "id": str(time.time()), 
                "nombre": nombre, 
                "año": anio,
                "cuatrimestre": cuatri,
                "estado": estado_final, 
                "req_regulares": req_regulares, 
                "req_aprobadas": req_aprobadas,
                "nota": nota_def,
                "intentos": intentos,
                "horarios_clase": nuevos_horarios
            })
            if guardar_datos(): st.rerun()
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
    colores = {
        "🔵 Celeste": "#0ea5e9", "🔴 Rojo": "#ef4444", "🟢 Verde": "#22c55e",
        "🟡 Amarillo": "#eab308", "🟣 Violeta": "#a855f7", "🟠 Naranja": "#f97316",
        "🩷 Rosa": "#ec4899", "⚪ Gris": "#94a3b8"
    }
    color_elegido = st.selectbox("Color Distintivo", list(colores.keys()))
    c = colores[color_elegido]
    
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
            "TIEMPO (min)": tiempo_neto, "EFIC.": f"{eficiencia}%",
            "INTERRUPCIONES": []
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
# --- LAYOUT PRINCIPAL (MENÚ FIJO) ---
# ==========================================
col_menu, col_contenido = st.columns([1, 4], gap="large")

with col_menu:
    st.markdown("### Menú")
    menu_opcion = st.radio("Navegación", ["Página Principal", "Resumen", "Organización", "Carrera", "Plan de Estudios"], label_visibility="collapsed")

with col_contenido:
    if menu_opcion == "Carrera":
        total_materias = len(st.session_state['plan_carrera'])
        st.header(f"Progreso de la Carrera ({total_materias})")
        
        if not st.session_state['plan_carrera']:
            st.info("Agregá materias en el 'Plan de Estudios' para ver tu progreso general.")
        else:
            df_plan = pd.DataFrame(st.session_state['plan_carrera'])
            
            counts = df_plan['estado'].value_counts().to_dict()
            aprobadas = counts.get("Aprobada/Promocionada", 0)
            regulares = counts.get("Regular", 0)
            cursando = counts.get("Cursando", 0)
            libres = counts.get("Libre/Recursado", 0)
            pendientes = counts.get("Pendiente", 0)
            
            p_apr = (aprobadas / total_materias) * 100 if total_materias > 0 else 0
            p_reg = (regulares / total_materias) * 100 if total_materias > 0 else 0
            p_curs = (cursando / total_materias) * 100 if total_materias > 0 else 0
            p_lib = (libres / total_materias) * 100 if total_materias > 0 else 0
            p_pend = (pendientes / total_materias) * 100 if total_materias > 0 else 0
            
            st.markdown(f"""
            <div style="width: 100%; height: 30px; border-radius: 15px; display: flex; overflow: hidden; margin-bottom: 25px; border: 1px solid #334155;">
                <div style="width: {p_apr}%; background-color: #22c55e;" title="Aprobadas: {p_apr:.1f}%"></div>
                <div style="width: {p_reg}%; background-color: #eab308;" title="Regulares: {p_reg:.1f}%"></div>
                <div style="width: {p_curs}%; background-color: #3b82f6;" title="Cursando: {p_curs:.1f}%"></div>
                <div style="width: {p_lib}%; background-color: #ef4444;" title="Libres: {p_lib:.1f}%"></div>
                <div style="width: {p_pend}%; background-color: #94a3b8;" title="Pendientes: {p_pend:.1f}%"></div>
            </div>
            """, unsafe_allow_html=True)
            
            c1, c2, c3, c4, c5 = st.columns(5)
            c1.markdown(f"<div style='text-align:center;'><div style='font-size:24px; font-weight:bold; color:#22c55e;'>{p_apr:.1f}%</div><div style='color:#94a3b8; font-size:12px; font-weight:bold;'>APROBADAS ({aprobadas})</div></div>", unsafe_allow_html=True)
            c2.markdown(f"<div style='text-align:center;'><div style='font-size:24px; font-weight:bold; color:#eab308;'>{p_reg:.1f}%</div><div style='color:#94a3b8; font-size:12px; font-weight:bold;'>REGULARES ({regulares})</div></div>", unsafe_allow_html=True)
            c3.markdown(f"<div style='text-align:center;'><div style='font-size:24px; font-weight:bold; color:#3b82f6;'>{p_curs:.1f}%</div><div style='color:#94a3b8; font-size:12px; font-weight:bold;'>CURSANDO ({cursando})</div></div>", unsafe_allow_html=True)
            c4.markdown(f"<div style='text-align:center;'><div style='font-size:24px; font-weight:bold; color:#ef4444;'>{p_lib:.1f}%</div><div style='color:#94a3b8; font-size:12px; font-weight:bold;'>LIBRES ({libres})</div></div>", unsafe_allow_html=True)
            c5.markdown(f"<div style='text-align:center;'><div style='font-size:24px; font-weight:bold; color:#94a3b8;'>{p_pend:.1f}%</div><div style='color:#94a3b8; font-size:12px; font-weight:bold;'>PENDIENTES ({pendientes})</div></div>", unsafe_allow_html=True)
            
            st.divider()
            
            col_izq, col_der = st.columns(2, gap="large")
            
            def calcular_prioridad(nombre_mat):
                count = 0
                for m in st.session_state['plan_carrera']:
                    if nombre_mat in m.get('req_regulares', []): count += 1
                    if nombre_mat in m.get('req_aprobadas', []): count += 1
                return count

            with col_izq:
                st.markdown("### 📘 Cursando y Regulares")
                st.caption("Ordenadas por prioridad (las que destraban más materias están arriba).")
                mat_cursando = [m for m in st.session_state['plan_carrera'] if m['estado'] in ["Cursando", "Regular"]]
                mat_cursando.sort(key=lambda x: calcular_prioridad(x['nombre']), reverse=True)
                
                if not mat_cursando:
                    st.info("No tenés materias en estado 'Cursando' o 'Regular'.")
                else:
                    for m in mat_cursando:
                        color_border = "#eab308" if m['estado'] == "Regular" else "#3b82f6"
                        st.markdown(f"""
                        <style>
                            div[data-testid="stButton"] button[key="btn_carr_curs_{m['id']}"] {{
                                background-color: #1e293b; color: #f8fafc; text-align: left;
                                border: none; border-left: 4px solid {color_border}; justify-content: flex-start;
                                padding-left: 15px; font-size: 15px;
                            }}
                        </style>
                        """, unsafe_allow_html=True)
                        if st.button(f"{m['nombre']} ({m['estado']})", key=f"btn_carr_curs_{m['id']}", use_container_width=True):
                            dialog_detalle_materia(m['id'])
            
            with col_der:
                st.markdown("### 🔓 Puedo Cursar")
                st.caption("Materias pendientes o libres que cumplen todos los requisitos para ser cursadas.")
                
                def is_met(m_name, req_type):
                    target = next((m for m in st.session_state['plan_carrera'] if m['nombre'] == m_name), None)
                    if not target: return False
                    if req_type == 'reg': return target['estado'] in ["Regular", "Aprobada/Promocionada"]
                    return target['estado'] == "Aprobada/Promocionada"
                    
                puedo_cursar = []
                for m in st.session_state['plan_carrera']:
                    if m['estado'] in ["Pendiente", "Libre/Recursado"]:
                        req_reg_ok = all(is_met(r, 'reg') for r in m.get('req_regulares', []))
                        req_apr_ok = all(is_met(r, 'apr') for r in m.get('req_aprobadas', []))
                        if req_reg_ok and req_apr_ok:
                            puedo_cursar.append(m)
                            
                puedo_cursar.sort(key=lambda x: calcular_prioridad(x['nombre']), reverse=True)
                            
                if not puedo_cursar:
                    st.info("No hay materias nuevas habilitadas para cursar en este momento.")
                else:
                    for m in puedo_cursar:
                        color_border = "#94a3b8" if m['estado'] == "Pendiente" else "#ef4444"
                        st.markdown(f"""
                        <style>
                            div[data-testid="stButton"] button[key="btn_carr_puedo_{m['id']}"] {{
                                background-color: #1e293b; color: #f8fafc; text-align: left;
                                border: none; border-left: 4px solid {color_border}; justify-content: flex-start;
                                padding-left: 15px; font-size: 15px;
                            }}
                        </style>
                        """, unsafe_allow_html=True)
                        if st.button(m['nombre'], key=f"btn_carr_puedo_{m['id']}", use_container_width=True):
                            dialog_detalle_materia(m['id'])

            st.divider()
            
            # --- PROMEDIO GENERAL ---
            notas_validas = []
            for m in st.session_state['plan_carrera']:
                if m['estado'] == 'Aprobada/Promocionada':
                    val = parse_float_nota(m.get('nota', ''))
                    if val is not None: notas_validas.append(val)
                elif m['estado'] == 'Regular':
                    intentos = m.get('intentos', [])
                    last_val = None
                    for i in intentos:
                        if i.strip(): last_val = i.strip()
                    if last_val:
                        val = parse_float_nota(last_val)
                        if val is not None: notas_validas.append(val)
            
            promedio = sum(notas_validas) / len(notas_validas) if notas_validas else 0.0
            
            st.markdown(f"""
            <div style="background-color: #1e293b; border-radius: 12px; padding: 20px; text-align: center; margin-top: 10px; border: 1px solid #334155;">
                <div style="color: #94a3b8; font-size: 14px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px;">PROMEDIO GENERAL</div>
                <div style="color: #0ea5e9; font-size: 42px; font-weight: 800; line-height: 1;">{promedio:.2f}</div>
            </div>
            """, unsafe_allow_html=True)

    elif menu_opcion == "Plan de Estudios":
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
                
                cols = st.columns(4)
                for i, row in materias_anio.reset_index().iterrows():
                    with cols[i % 4]:
                        with st.container(border=True):
                            color_clase = "badge-pendiente"
                            if row['estado'] == "Regular": color_clase = "badge-regular"
                            elif row['estado'] == "Aprobada/Promocionada": color_clase = "badge-aprobada"
                            elif row['estado'] == "Cursando": color_clase = "badge-cursando"
                            elif row['estado'] == "Libre/Recursado": color_clase = "badge-libre"
                            
                            cuatri_abrev = ""
                            cuatri_val = row.get('cuatrimestre', '')
                            if cuatri_val == "1er Cuatrimestre": cuatri_abrev = "1C"
                            elif cuatri_val == "2do Cuatrimestre": cuatri_abrev = "2C"
                            elif cuatri_val == "Anual": cuatri_abrev = "Anual"
                            
                            cuatri_html = f"<span style='float:right; font-size: 11px; color: #94a3b8; font-weight: bold;'>{cuatri_abrev}</span>" if cuatri_abrev else ""

                            html_badges = f"""
                            <div style="margin-bottom: 8px;">
                                <span class='{color_clase}'>{row['estado']}</span>
                                {cuatri_html}
                            </div>
                            """
                            st.markdown(html_badges, unsafe_allow_html=True)
                            
                            if st.button(row['nombre'], key=f"btn_info_{row['id']}", use_container_width=True):
                                dialog_detalle_materia(row['id'])
                                
                            html_reqs = ""
                            if isinstance(row.get('req_regulares'), list) and len(row['req_regulares']) > 0: 
                                html_reqs += f"<div style='font-size: 11px; color: #94a3b8; margin-bottom: 2px;'><b>Reg:</b> {', '.join(row['req_regulares'])}</div>"
                            if isinstance(row.get('req_aprobadas'), list) and len(row['req_aprobadas']) > 0: 
                                html_reqs += f"<div style='font-size: 11px; color: #94a3b8; margin-bottom: 2px;'><b>Apr:</b> {', '.join(row['req_aprobadas'])}</div>"
                            
                            if html_reqs:
                                st.markdown(html_reqs, unsafe_allow_html=True)

    elif menu_opcion == "Resumen":
        st.header("Tus Estadísticas")
        renderizar_analitica()

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

    elif menu_opcion == "Página Principal":
        tabs = st.tabs(["Cronómetro", "Analítica", "Metas", "Historial"])

        with tabs[0]:
            if st.session_state['timer_state'] == 'IDLE':
                col_izq, col_der = st.columns([1, 1.5], gap="large")
                
                with col_izq:
                    # --- SECCIÓN: METAS ACTUALES ---
                    st.markdown("### Metas actuales")
                    st.caption("Progreso de tus metas vigentes.")
                    
                    hoy = date.today()
                    metas_actuales = []
                    for m in st.session_state['metas']:
                        try:
                            if date.fromisoformat(m['fecha_examen']) >= hoy:
                                metas_actuales.append(m)
                        except: pass
                        
                    if not metas_actuales:
                        st.info("No tenés metas de exámenes próximas. ¡Todo al día!")
                    else:
                        for meta in metas_actuales:
                            with st.container(border=True):
                                try: fecha_str = date.fromisoformat(meta['fecha_examen']).strftime('%d/%m/%Y')
                                except: fecha_str = ""
                                
                                st.markdown(f"<div style='color: #94a3b8; font-size: 11px; text-transform: uppercase; margin-bottom: 2px;'>{meta['materia']} - Fecha: {fecha_str}</div>", unsafe_allow_html=True)
                                st.markdown(f"<div style='font-size: 18px; font-weight: bold; margin-bottom: 8px;'>{meta['nombre']}</div>", unsafe_allow_html=True)
                                
                                progreso = min(meta['horas_acumuladas'] / meta['meta_horas'], 1.0)
                                st.progress(progreso)
                                
                                h_acum = int(meta['horas_acumuladas'])
                                m_acum = int((meta['horas_acumuladas'] - h_acum) * 60)
                                st.markdown(f"<div style='font-size: 12px; color: #94a3b8; margin-top: 5px;'>{h_acum}h {m_acum}m / {meta['meta_horas']}h 00m</div>", unsafe_allow_html=True)

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
                        st.session_state['current_interruptions'].append(motivo)
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
                            "TIEMPO (min)": minutos_estudio, "EFIC.": "100%",
                            "INTERRUPCIONES": st.session_state.get('current_interruptions', [])
                        }
                        st.session_state['historial'].append(nueva_sesion)
                        st.session_state['current_interruptions'] = []
                        
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

            # --- SECCIÓN: HORARIO DE CURSADO AUTOMÁTICO A LO ANCHO ---
            if st.session_state['timer_state'] == 'IDLE':
                st.divider()
                st.markdown("### Mi Horario de Cursado")
                st.caption("Se completa solo con los horarios que cargues al editar tus materias 'Cursando' en el Plan de Estudios.")
                
                horarios_completos = []
                for m in st.session_state['plan_carrera']:
                    if m['estado'] == "Cursando" and 'horarios_clase' in m:
                        for hc in m['horarios_clase']:
                            if hc.get('dia') != "---" and hc.get('inicio'):
                                # Magia para leer la hora aunque pongas "19" o "9" sin los ceros
                                ini_c = hc['inicio'].strip()
                                if ":" not in ini_c: ini_c += ":00"
                                if len(ini_c.split(":")[0]) == 1: ini_c = "0" + ini_c
                                
                                fin_c = hc.get('fin', '').strip()
                                if fin_c:
                                    if ":" not in fin_c: fin_c += ":00"
                                    if len(fin_c.split(":")[0]) == 1: fin_c = "0" + fin_c
                                
                                horarios_completos.append({
                                    "materia": m['nombre'],
                                    "dia": hc['dia'],
                                    "inicio": ini_c,
                                    "fin": fin_c
                                })
                
                def get_sortable_time(t_str):
                    try: return datetime.strptime(t_str, "%H:%M").time()
                    except: return datetime.strptime("23:59", "%H:%M").time()

                # Extraer todos los horarios únicos (tanto de inicio como de fin)
                time_points = set()
                for hc in horarios_completos:
                    time_points.add(hc['inicio'])
                    if hc['fin']:
                        time_points.add(hc['fin'])

                # Ordenamos todos los horarios para crear las filas exactas del calendario
                sorted_times = sorted(list(time_points), key=get_sortable_time)
                
                if not sorted_times:
                    st.info("No tenés horarios cargados. Andá a Carrera o Plan de Estudios, tocá en 'Editar' en una materia Cursando y poné a qué hora la tenés.")
                else:
                    dias_semana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado"]
                    
                    matriz = {t: {d: [] for d in dias_semana} for t in sorted_times}
                    
                    for hc in horarios_completos:
                        if hc['dia'] in dias_semana:
                            t_ini = get_sortable_time(hc['inicio'])
                            t_fin = get_sortable_time(hc['fin']) if hc['fin'] else get_sortable_time("23:59")
                            
                            # Cargar la materia en todos los bloques temporales que ocupa
                            for t_row in sorted_times:
                                t_actual = get_sortable_time(t_row)
                                if t_ini <= t_actual < t_fin:
                                    matriz[t_row][hc['dia']].append(hc)
                                    
                    html_tabla = "<table class='tabla-horario'>"
                    html_tabla += "<tr><th>HORARIO</th>"
                    for d in dias_semana: html_tabla += f"<th>{d.upper()}</th>"
                    html_tabla += "</tr>"
                    
                    # Diccionario para saber si tenemos que saltear una celda porque ya la fusionamos (rowspan)
                    skip_cells = {d: 0 for d in dias_semana}
                    
                    for i, t_row in enumerate(sorted_times):
                        html_tabla += f"<tr><td>{t_row}</td>"
                        for d in dias_semana:
                            if skip_cells[d] > 0:
                                skip_cells[d] -= 1
                                continue
                                
                            items = matriz[t_row][d]
                            if items:
                                mat = items[0]
                                span = 1
                                # Mirar hacia abajo cuántas filas abarca esta misma clase para fusionarlas
                                for j in range(i + 1, len(sorted_times)):
                                    next_t = sorted_times[j]
                                    next_items = matriz[next_t][d]
                                    if next_items and next_items[0]['materia'] == mat['materia']:
                                        span += 1
                                    else:
                                        break
                                
                                skip_cells[d] = span - 1
                                
                                # Diseño del bloque: hora arriba, materia, hora abajo (bien limpio)
                                texto = f"<span style='font-size: 11px; font-weight: normal; opacity: 0.8;'>{mat['inicio']}</span><br>"
                                texto += f"{mat['materia']}"
                                if mat['fin']: 
                                    texto += f"<br><span style='font-size: 11px; font-weight: normal; opacity: 0.8;'>{mat['fin']}</span>"
                                
                                html_tabla += f"<td rowspan='{span}'><div class='materia-bloque' style='height: 100%; min-height: 70px; display: flex; flex-direction: column; justify-content: center;'>{texto}</div></td>"
                            else:
                                html_tabla += "<td></td>"
                        html_tabla += "</tr>"
                    html_tabla += "</table>"
                    
                    st.markdown(html_tabla, unsafe_allow_html=True)
        with tabs[1]:
            renderizar_analitica()

        with tabs[2]:
            materias_con_metas = list(set([m['materia'] for m in st.session_state['metas']]))
            
            c_filt1, c_filt2, c_filt3, c_btn3 = st.columns([1, 2, 2, 2])
            with c_filt1: st.markdown("<div style='margin-top: 30px; color:#94a3b8;'>⚙️ <b>Filtros</b></div>", unsafe_allow_html=True)
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
                
                html_hist = "<table class='tabla-historial'>"
                html_hist += "<tr><th>FECHA</th><th>MATERIA</th><th>MÉTODO</th><th>TIEMPO (min)</th><th>EFIC.</th></tr>"
                for _, row in df_mostrar.iterrows():
                    html_hist += f"<tr><td>{row.get('FECHA', '')}</td><td>{row.get('MATERIA', '')}</td><td>{row.get('MÉTODO', '')}</td><td>{row.get('TIEMPO (min)', '')}</td><td>{row.get('EFIC.', '')}</td></tr>"
                html_hist += "</table>"
                
                st.markdown(html_hist, unsafe_allow_html=True)
