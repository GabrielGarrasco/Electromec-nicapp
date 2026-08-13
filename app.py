import streamlit as st
import time
import streamlit.components.v1 as components
import pandas as pd
from datetime import datetime, date
import plotly.express as px
import plotly.graph_objects as go
import random
import re

# --- IMPORTACIÓN DE MÓDULOS PROPIOS ---
from db import cargar_datos_sheet, guardar_datos
from utils import parse_float_nota, calcular_datos_racha, calcular_proximo_repaso
from ui import cargar_css

# --- CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(page_title="Electromecánica", page_icon="⚙️", layout="wide")
cargar_css()

# --- INICIALIZACIÓN DE VARIABLES ---
if 'timer' not in st.session_state:
    st.session_state['timer'] = {
        'state': 'IDLE',
        'start': 0.0,
        'elapsed': 0.0,
        'pause_start': 0.0,
        'pause_elapsed': 0.0,
        'interruption_reason': "",
        'interruptions': [],
        'mode': 'Libre',
        'focus_time': 25,
        'break_time': 5
    }

if 'editando_plan_mat_id' not in st.session_state: st.session_state['editando_plan_mat_id'] = None

if 'datos_cargados' not in st.session_state:
    datos_generales, temarios_guardados = cargar_datos_sheet()
    
    if datos_generales:
        st.session_state['materias'] = datos_generales.get('materias', [])
        st.session_state['metodos'] = datos_generales.get('metodos', [])
        st.session_state['distracciones'] = datos_generales.get('distracciones', [])
        st.session_state['historial'] = datos_generales.get('historial', [])
        st.session_state['metas'] = datos_generales.get('metas', [])
        st.session_state['plan_carrera'] = datos_generales.get('plan_carrera', [])
        st.session_state['horarios'] = datos_generales.get('horarios', [])
        st.session_state['calendario_manual'] = datos_generales.get('calendario_manual', "")
        st.session_state['xp_total'] = datos_generales.get('xp_total', 0)
        st.session_state['recompensas'] = datos_generales.get('recompensas', [
            {"nombre": "Comida chatarra", "costo": 3000},
            {"nombre": "Tarde libre sin culpa", "costo": 5000}
        ])
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
        st.session_state['calendario_manual'] = ""
        st.session_state['xp_total'] = 0
        st.session_state['recompensas'] = [
            {"nombre": "Comida chatarra", "costo": 3000},
            {"nombre": "Tarde libre sin culpa", "costo": 5000}
        ]
        
    st.session_state['temarios'] = temarios_guardados if temarios_guardados else {}
    st.session_state['datos_cargados'] = True

if len(st.session_state['materias']) > 0 and isinstance(st.session_state['materias'][0], str):
    st.session_state['materias'] = []

OPCIONES_DIAS = ["---", "Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado"]

# CÁLCULO DE RACHA
racha_actual, mejor_racha, protectores, dias_para_protector = calcular_datos_racha(st.session_state['historial'])

# --- MODO INVASIÓN ---
hoy_date = date.today()
examenes_proximos = []
for m in st.session_state['metas']:
    if m.get('fecha_examen'):
        try:
            f_ex = date.fromisoformat(m['fecha_examen'])
            if 0 <= (f_ex - hoy_date).days <= 7:
                examenes_proximos.append(m)
        except:
            pass

modo_invasion = len(examenes_proximos) >= 2
multiplicador_xp = 2 if modo_invasion else 1

if modo_invasion:
    st.markdown("""
    <style>
        .stApp { background-color: #420516 !important; }
        div[data-testid="stSidebar"] { background-color: #420516 !important; }
        div.stButton > button:first-child { background-color: #7D1935 !important; border-color: #7B113A !important; color: white !important; }
        div[border="true"], .historico-box { background-color: #59244b !important; border: 1px solid #7B113A !important; }
        .custom-hr { border-top: 1px solid #7B113A !important; }
        .analitica-title, .historico-title, h1, h2, h3, h4, p, div, span { color: #f8fafc !important; }
        .materia-pill, .badge-cursando, .badge-regular { background-color: #7D1935 !important; color: #f8fafc !important; border: 1px solid #950101 !important; }
    </style>
    <div style='background-color: #950101; padding: 10px; text-align: center; font-weight: bold; margin-bottom: 15px; border-radius: 8px;'>
        ALERTA DE INVASIÓN: Múltiples exámenes próximos. XP x2 activada.
    </div>
    """, unsafe_allow_html=True)


# --- MODALES (DIALOGS) ---
@st.dialog("Racha de Estudio", width="small")
def dialog_racha():
    st.markdown(f"""
    <div style='text-align: center;'>
        <h1 style='font-size: 40px; margin-bottom: 0px; color: #f8fafc;'>{racha_actual} días</h1>
        <p style='color: #7498b6; font-weight: bold; margin-top: 0px;'>Racha actual</p>
    </div>
    """, unsafe_allow_html=True)
    
    shields_html = "<div style='display: flex; justify-content: center; gap: 10px; margin: 20px 0;'>"
    for i in range(3):
        color = "#10b981" if i < protectores else "#153f59"
        opacity = "1" if i < protectores else "0.3"
        shields_html += f"<div style='width: 35px; height: 35px; border-radius: 50%; background-color: {color}; opacity: {opacity}; display: flex; justify-content: center; align-items: center; font-size: 16px; border: 1px solid #02253d;'></div>"
    shields_html += "</div>"
    
    st.markdown(f"""
    <div style='background-color: #02152b; border-radius: 12px; padding: 15px; text-align: center; border: 1px solid #153f59;'>
        <div style='color: #7498b6; font-size: 11px; font-weight: 800; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 10px;'>PROTECTORES</div>
        {shields_html}
        <div style='font-weight: 800; font-size: 13px; color: #f8fafc;'>Faltan {dias_para_protector} días continuos para otro.</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.write("<br>", unsafe_allow_html=True)
    if st.button("Cerrar", type="primary", use_container_width=True):
        st.session_state['show_racha_modal'] = False
        st.rerun()

if st.session_state.get('show_racha_modal', False):
    dialog_racha()

# --- RELOJ EN VIVO (CON ALARMA) ---
def render_live_timer(elapsed_seconds, is_running):
    mode = st.session_state['timer']['mode']
    target_ms = st.session_state['timer']['focus_time'] * 60000 if mode == 'Pomodoro' else 0
    
    html_code = f"""
    <div id="clock" style="font-size: 75px; font-weight: 700; text-align: center; color: #f8fafc; font-family: 'Courier New', Courier, monospace; letter-spacing: 2px; margin: 15px 0;">00:00:00</div>
    <script>
        var elapsedMs = {elapsed_seconds * 1000};
        var isRunning = {'true' if is_running else 'false'};
        var mode = "{mode}";
        var targetMs = {target_ms};
        var start = Date.now() - elapsedMs;
        var audio = new Audio('https://assets.mixkit.co/active_storage/sfx/2869/2869-preview.mp3');
        
        function updateClock() {{
            var delta = isRunning ? (Date.now() - start) : elapsedMs;
            
            if (mode === 'Pomodoro') {{
                var remaining = targetMs - delta;
                if (remaining <= 0) {{
                    if (!window.audioPlayed) {{ audio.play(); window.audioPlayed = true; }}
                    document.getElementById("clock").innerHTML = "¡TIEMPO!";
                    document.getElementById("clock").style.color = "#10b981";
                    return;
                }}
                var hrs = Math.floor(remaining / 3600000).toString().padStart(2, '0');
                var mins = Math.floor((remaining % 3600000) / 60000).toString().padStart(2, '0');
                var secs = Math.floor((remaining % 60000) / 1000).toString().padStart(2, '0');
                document.getElementById("clock").innerHTML = (hrs !== "00" ? hrs + ":" : "") + mins + ":" + secs;
            }} else {{
                var hrs = Math.floor(delta / 3600000).toString().padStart(2, '0');
                var mins = Math.floor((delta % 3600000) / 60000).toString().padStart(2, '0');
                var secs = Math.floor((delta % 60000) / 1000).toString().padStart(2, '0');
                document.getElementById("clock").innerHTML = hrs + ":" + mins + ":" + secs;
            }}
        }}
        updateClock();
        if (isRunning) {{ setInterval(updateClock, 1000); }}
    </script>
    """
    components.html(html_code, height=120)

def renderizar_analitica():
    st.markdown("### Estadísticas")
    df_hist = pd.DataFrame(st.session_state['historial'])
    
    if not df_hist.empty:
        df_hist['FECHA_OBJ'] = pd.to_datetime(df_hist['FECHA'], format='%d/%m/%Y', errors='coerce')
        df_hist['TIEMPO (min)'] = pd.to_numeric(df_hist['TIEMPO (min)'], errors='coerce').fillna(0)
        df_hist['EFIC_NUM'] = df_hist['EFIC.'].astype(str).str.replace('%','').astype(float)
        
        efic_promedio = int(df_hist['EFIC_NUM'].mean())
        total_minutos = df_hist['TIEMPO (min)'].sum()
        materia_top = df_hist.groupby('MATERIA')['TIEMPO (min)'].sum().idxmax() if total_minutos > 0 else "N/A"
        top_h = int(df_hist.groupby('MATERIA')['TIEMPO (min)'].sum().max() // 60) if total_minutos > 0 else 0
        
        hoy = pd.Timestamp.now().normalize()
        fechas_7d = [hoy - pd.Timedelta(days=i) for i in range(6, -1, -1)]
        df_7d = df_hist[df_hist['FECHA_OBJ'] >= fechas_7d[0]]
        mins_semana = df_7d['TIEMPO (min)'].sum() if not df_7d.empty else 0
        h_sem, m_sem = int(mins_semana // 60), int(mins_semana % 60)
        
        df_hoy = df_hist[df_hist['FECHA_OBJ'] == hoy]
        mins_hoy = df_hoy['TIEMPO (min)'].sum() if not df_hoy.empty else 0
        h_hoy, m_hoy = int(mins_hoy // 60), int(mins_hoy % 60)
    else:
        efic_promedio = total_minutos = top_h = h_sem = m_sem = h_hoy = m_hoy = 0
        materia_top = "N/A"
        df_7d = pd.DataFrame()
        fechas_7d = []

    c1, c2 = st.columns([1, 2])
    with c1:
        with st.container(border=True):
            st.markdown("<div class='analitica-title'>EFICIENCIA</div>", unsafe_allow_html=True)
            
            donut_color = "#10b981" if efic_promedio > 0 else "#021d34"
            fig_efic = go.Figure(data=[go.Pie(
                labels=["Eficiencia", "Falta"], 
                values=[efic_promedio, max(0, 100-efic_promedio)],
                hole=.75,
                marker_colors=[donut_color, "#021d34"],
                textinfo='none',
                hoverinfo='label+percent'
            )])
            fig_efic.update_layout(
                showlegend=False,
                margin=dict(t=0, b=0, l=0, r=0),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                height=180,
                annotations=[dict(text=f"<b>{efic_promedio}%</b>", x=0.5, y=0.5, showarrow=False, font=dict(size=28, color="#f8fafc"))]
            )
            st.plotly_chart(fig_efic, use_container_width=True, config={'displayModeBar': False})
            
    with c2:
        with st.container(border=True):
            st.markdown("<div class='analitica-title'>HORAS (SEMANAL)</div>", unsafe_allow_html=True)
            if df_7d.empty:
                st.info("Sin datos esta semana.")
            else:
                df_barras = df_7d.groupby('MATERIA')['TIEMPO (min)'].sum().reset_index()
                df_barras['Horas'] = df_barras['TIEMPO (min)'] / 60
                
                fig_bars = px.bar(df_barras, x='Horas', y='MATERIA', orientation='h')
                fig_bars.update_traces(marker_color='#365b77')
                fig_bars.update_layout(
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font_color='#7498b6',
                    margin=dict(l=0, r=0, t=0, b=0),
                    height=180,
                    xaxis=dict(gridcolor='#153f59', title=""),
                    yaxis=dict(title="", categoryorder='total ascending')
                )
                st.plotly_chart(fig_bars, use_container_width=True, config={'displayModeBar': False})
                
    st.markdown("<div class='analitica-title' style='margin-top: 15px;'>DESEMPEÑO POR AÑO (PROMEDIOS)</div>", unsafe_allow_html=True)
    notas_por_anio = {1: [], 2: [], 3: [], 4: [], 5: [], 6: []}
    
    for mat in st.session_state['plan_carrera']:
        if not str(mat['año']).isdigit():
            continue
        anio = int(mat['año'])
        notas_mat = []
        nf = parse_float_nota(mat.get('nota', ''))
        if nf is not None: notas_mat.append(nf)
            
        for meta in st.session_state['metas']:
            if meta['materia'] == mat['nombre'] and meta.get('nota'):
                nm = parse_float_nota(meta['nota'])
                if nm is not None: notas_mat.append(nm)
                    
        if notas_mat:
            promedio_mat = sum(notas_mat) / len(notas_mat)
            if anio in notas_por_anio: notas_por_anio[anio].append(promedio_mat)
            
    data_radar = []
    for a in range(1, 7):
        if notas_por_anio[a]:
            data_radar.append({'Año': f"Año {a}", 'Promedio': sum(notas_por_anio[a])/len(notas_por_anio[a])})
        else:
            data_radar.append({'Año': f"Año {a}", 'Promedio': 0})
            
    df_radar = pd.DataFrame(data_radar)
    fig = px.line_polar(df_radar, r='Promedio', theta='Año', line_close=True, range_r=[0,10])
    fig.update_traces(fill='toself', line_color='#10b981')
    fig.update_layout(
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color='#7498b6',
        margin=dict(l=20, r=20, t=20, b=20), height=300,
        polar=dict(radialaxis=dict(visible=True, range=[0, 10], color='#7498b6', gridcolor='#153f59'),
                   angularaxis=dict(color='#f8fafc', gridcolor='#153f59'))
    )
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    st.markdown("<div class='analitica-title' style='margin-top: 15px;'>HISTÓRICO</div>", unsafe_allow_html=True)
    ch1, ch2, ch3, ch4 = st.columns(4)
    with ch1:
        with st.container(border=True):
            st.markdown("<div class='historico-box'><div class='historico-title'>MEJOR RACHA</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='historico-val'>{mejor_racha} d</div></div>", unsafe_allow_html=True)
    with ch2:
        with st.container(border=True):
            st.markdown("<div class='historico-box'><div class='historico-title'>MATERIA TOP</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='historico-val' style='font-size: 16px;'>{materia_top}</div>", unsafe_allow_html=True)
    with ch3:
        with st.container(border=True):
            st.markdown("<div class='historico-box'><div class='historico-title'>% GLOBAL</div>", unsafe_allow_html=True)
            st.markdown(f"<div class='historico-val'>{efic_promedio}%</div></div>", unsafe_allow_html=True)
    with ch4:
        with st.container(border=True):
            st.markdown("<div class='historico-box'><div class='historico-title'>HORAS TOTALES</div>", unsafe_allow_html=True)
            h_tot = int(total_minutos // 60)
            st.markdown(f"<div class='historico-val'>{h_tot}h</div></div>", unsafe_allow_html=True)

    st.write("<br>", unsafe_allow_html=True)
    if not df_hist.empty:
        csv = df_hist.drop(columns=['FECHA_OBJ'], errors='ignore').to_csv(index=False).encode('utf-8')
        st.download_button(label="📥 Exportar Historial (CSV)", data=csv, file_name='historial_estudio.csv', mime='text/csv', use_container_width=True)

@st.dialog("Detalle de la Materia")
def dialog_detalle_materia(mat_id):
    mat = next((m for m in st.session_state['plan_carrera'] if m['id'] == mat_id), None)
    if not mat: return
    
    if st.session_state.get('editando_plan_mat_id') == mat_id:
        st.markdown("### Editar Materia")
        nuevo_nombre = st.text_input("Nombre", value=mat['nombre'])
        
        col1, col2, col3 = st.columns(3)
        opciones_anio = [1, 2, 3, 4, 5, 6, "Extracurricular"]
        val_anio_actual = int(mat['año']) if str(mat['año']).isdigit() else mat['año']
        idx_anio = opciones_anio.index(val_anio_actual) if val_anio_actual in opciones_anio else 0
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
            
        st.markdown("<hr class='custom-hr'>", unsafe_allow_html=True)
        st.markdown("<div style='font-size: 14px; font-weight: bold; margin-bottom: 5px; color: #7498b6;'>Correlatividades</div>", unsafe_allow_html=True)
        opciones_materias = [m['nombre'] for m in st.session_state['plan_carrera'] if m['id'] != mat_id]
        def_reg = [x for x in mat.get('req_regulares', []) if x in opciones_materias]
        def_apr = [x for x in mat.get('req_aprobadas', []) if x in opciones_materias]
        nuevas_reg = st.multiselect("Para cursar necesito REGULAR:", opciones_materias, default=def_reg)
        nuevas_apr = st.multiselect("Para cursar necesito APROBADA:", opciones_materias, default=def_apr)
        
        st.markdown("<hr class='custom-hr'>", unsafe_allow_html=True)
        st.markdown("<div style='font-size: 14px; font-weight: bold; margin-bottom: 5px; color: #7498b6;'>📖 Temario</div>", unsafe_allow_html=True)
        nombre_mat_actual = mat['nombre']
        temario_actual = st.session_state.get('temarios', {}).get(nombre_mat_actual, [])
        texto_temario_default = "\n".join([t['tema'] for t in temario_actual])
        
        with st.expander("Ver / Editar Temario"):
            st.info("Pegá acá la lista de temas (uno por renglón).")
            texto_temario_nuevo = st.text_area("Temas", value=texto_temario_default, height=150, label_visibility="collapsed")
        
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
                
                temas_list = [t.strip() for t in texto_temario_nuevo.split('\n') if t.strip()]
                temario_guardar = []
                for t_nombre in temas_list:
                    tema_previo = next((t for t in temario_actual if t['tema'] == t_nombre), None)
                    if tema_previo:
                        temario_guardar.append(tema_previo)
                    else:
                        temario_guardar.append({'tema': t_nombre, 'nivel': 0, 'proximo_repaso': None})
                        
                if nuevo_nombre != nombre_mat_actual and nombre_mat_actual in st.session_state['temarios']:
                    del st.session_state['temarios'][nombre_mat_actual]
                    
                st.session_state['temarios'][nuevo_nombre] = temario_guardar
                
                st.session_state['editando_plan_mat_id'] = None
                if guardar_datos(): st.rerun()
            else:
                st.error("Falta el nombre.")
                
    else:
        st.markdown(f"### {mat['nombre']}")
        cuatri = mat.get('cuatrimestre', 'No definido')
        
        info_str = f"**Año:** {mat['año']} &nbsp;|&nbsp; **Cuatrimestre:** {cuatri} &nbsp;|&nbsp; **Estado:** {mat['estado']}"
        if mat['estado'] == "Aprobada/Promocionada" and mat.get('nota'):
            info_str += f" &nbsp;|&nbsp; **Nota:** {mat['nota']}"
        st.markdown(info_str)
        
        intentos_guardados = mat.get('intentos', [])
        intentos_validos = [i for i in intentos_guardados if i.strip()]
        if intentos_validos:
            st.caption(f"Intentos registrados: {', '.join(intentos_validos)}")
            
        horarios = mat.get('horarios_clase', [])
        if mat['estado'] == "Cursando" and horarios:
            for hc in horarios:
                rango = f"{hc['inicio']} a {hc['fin']}" if hc.get('fin') else hc['inicio']
                st.markdown(f"<p style='margin-bottom: 2px; color:#94b8d7;'><b>{hc['dia']}:</b> {rango}</p>", unsafe_allow_html=True)
            
        st.markdown("<hr class='custom-hr'>", unsafe_allow_html=True)
        
        def is_met(m_name, req_type):
            target = next((m for m in st.session_state['plan_carrera'] if m['nombre'] == m_name), None)
            if not target: return False
            if req_type == 'reg': return target['estado'] in ["Regular", "Aprobada/Promocionada"]
            return target['estado'] == "Aprobada/Promocionada"

        st.markdown("<div style='font-size: 14px; font-weight: bold; margin-bottom: 5px; color:#7498b6;'>Correlatividades</div>", unsafe_allow_html=True)
        if not mat.get('req_regulares') and not mat.get('req_aprobadas'):
            st.caption("No tiene correlatividades previas.")
            
        if mat.get('req_regulares'):
            st.write("**Para cursar requiere REGULAR:**")
            for r in mat['req_regulares']:
                cumple = is_met(r, 'reg')
                st.markdown(f"<div style='font-size: 13px; color: {'#10b981' if cumple else '#7498b6'};'>{'[OK]' if cumple else '[ ]'} {r}</div>", unsafe_allow_html=True)
                
        if mat.get('req_aprobadas'):
            st.write("**Para cursar requiere APROBADA:**")
            for r in mat['req_aprobadas']:
                cumple = is_met(r, 'apr')
                st.markdown(f"<div style='font-size: 13px; color: {'#10b981' if cumple else '#7498b6'};'>{'[OK]' if cumple else '[ ]'} {r}</div>", unsafe_allow_html=True)
                
        destraba_reg = [m['nombre'] for m in st.session_state['plan_carrera'] if mat['nombre'] in m.get('req_regulares', [])]
        destraba_apr = [m['nombre'] for m in st.session_state['plan_carrera'] if mat['nombre'] in m.get('req_aprobadas', [])]
        
        if destraba_reg or destraba_apr:
            st.markdown("<hr class='custom-hr'>", unsafe_allow_html=True)
            st.markdown("<div style='font-size: 14px; font-weight: bold; margin-bottom: 5px; color:#7498b6;'>Destraba</div>", unsafe_allow_html=True)
            for d in destraba_reg: st.markdown(f"<div style='font-size: 13px; color: #94b8d7;'>- {d} (Para cursar)</div>", unsafe_allow_html=True)
            for d in destraba_apr: st.markdown(f"<div style='font-size: 13px; color: #94b8d7;'>- {d} (Para rendir/cursar)</div>", unsafe_allow_html=True)

        st.write("<br>", unsafe_allow_html=True)
        c_del, c_edit = st.columns(2)
        if c_del.button("Eliminar", type="secondary", use_container_width=True):
            st.session_state['plan_carrera'] = [m for m in st.session_state['plan_carrera'] if m['id'] != mat_id]
            if guardar_datos(): st.rerun()
        if c_edit.button("Editar", type="primary", use_container_width=True):
            st.session_state['editando_plan_mat_id'] = mat_id
            st.rerun()

@st.dialog("Agregar Materia al Plan")
def dialog_nueva_materia_plan():
    nombre = st.text_input("Nombre de la materia")
    col1, col2, col3 = st.columns(3)
    anio = col1.selectbox("Año", [1, 2, 3, 4, 5, 6, "Extracurricular"])
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
                "id": str(time.time()), "nombre": nombre, "año": anio, "cuatrimestre": cuatri,
                "estado": estado_final, "req_regulares": req_regulares, "req_aprobadas": req_aprobadas,
                "nota": nota_def, "intentos": intentos, "horarios_clase": nuevos_horarios
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
    dias_sel = st.multiselect("DÍAS DE ESTUDIO", ["L", "M", "X", "J", "V", "S", "D"], default=["L", "M", "X", "J", "V"])
    
    st.divider()
    temas_materia = st.session_state.get('temarios', {}).get(materia, [])
    opciones_temas = [t['tema'] for t in temas_materia]
    temas_examen = st.multiselect("Temas que entran (Opcional)", opciones_temas, help="Si dejás esto vacío, se asume que entran todos los temas de la materia.")
    
    c1, c2 = st.columns(2)
    if c1.button("Cancelar", use_container_width=True): st.rerun()
    if c2.button("Guardar", type="primary", use_container_width=True):
        if nombre:
            nueva = {
                "id": str(time.time()), "nombre": nombre, "materia": materia,
                "meta_horas": meta_horas, "fecha_examen": fecha_examen.isoformat(), 
                "horas_acumuladas": 0.0, "nota": None, "dias_estudio": dias_sel,
                "temas_examen": temas_examen
            }
            st.session_state['metas'].append(nueva)
            if guardar_datos(): st.rerun()

@st.dialog("Editar Meta de Examen")
def dialog_editar_meta(meta_idx):
    meta = st.session_state['metas'][meta_idx]
    nombres_materias = [m["nombre"] for m in st.session_state['materias']]
    
    if not nombres_materias:
        st.warning("No hay materias activas.")
        return

    nombre = st.text_input("NOMBRE (EJ: PARCIAL 1)", value=meta.get('nombre', ''))
    
    idx_mat = nombres_materias.index(meta['materia']) if meta.get('materia') in nombres_materias else 0
    materia = st.selectbox("MATERIA", nombres_materias, index=idx_mat)
    
    col1, col2 = st.columns(2)
    meta_horas = col1.number_input("META (HORAS)", min_value=1, step=1, value=int(meta.get('meta_horas', 20)))
    
    try: default_date = date.fromisoformat(meta.get('fecha_examen', date.today().isoformat()))
    except: default_date = date.today()
    fecha_examen = col2.date_input("FECHA EXAMEN", value=default_date)
    
    dias_sel = st.multiselect("DÍAS DE ESTUDIO", ["L", "M", "X", "J", "V", "S", "D"], default=meta.get('dias_estudio', ["L", "M", "X", "J", "V"]))
    
    st.divider()
    temas_materia = st.session_state.get('temarios', {}).get(materia, [])
    opciones_temas = [t['tema'] for t in temas_materia]
    temas_actuales = [t for t in meta.get('temas_examen', []) if t in opciones_temas]
    temas_examen = st.multiselect("Temas que entran (Opcional)", opciones_temas, default=temas_actuales)
    
    st.write("<br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    if c1.button("🗑️ Eliminar", use_container_width=True):
        st.session_state['metas'].pop(meta_idx)
        if guardar_datos(): st.rerun()
    if c2.button("Cancelar", use_container_width=True): 
        st.rerun()
    if c3.button("Guardar", type="primary", use_container_width=True):
        if nombre:
            meta['nombre'] = nombre
            meta['materia'] = materia
            meta['meta_horas'] = meta_horas
            meta['fecha_examen'] = fecha_examen.isoformat()
            meta['dias_estudio'] = dias_sel
            meta['temas_examen'] = temas_examen
            if guardar_datos(): st.rerun()

@st.dialog("Asignar Nota Final")
def dialog_asignar_nota(meta_idx):
    meta_actual = st.session_state['metas'][meta_idx]
    st.write(f"**Examen:** {meta_actual['nombre']} ({meta_actual['materia']})")
    nota = st.text_input("NOTA FINAL", placeholder="Ej: 80 o 8.5")
    c1, c2 = st.columns(2)
    if c1.button("Cancelar", use_container_width=True): st.rerun()
    if c2.button("Guardar Nota", type="primary", use_container_width=True):
        if nota:
            st.session_state['metas'][meta_idx]['nota'] = nota
            if guardar_datos(): st.rerun()

@st.dialog("Histórico de Notas", width="large")
def dialog_historico_notas():
    notas_guardadas = [m for m in st.session_state['metas'] if m.get('nota') is not None and str(m['nota']).strip() != ""]
    if not notas_guardadas:
        st.info("Todavía no tenés notas registradas en tus exámenes pasados.")
        return
    def get_date(m):
        try: return date.fromisoformat(m['fecha_examen'])
        except: return date.min
    notas_guardadas.sort(key=get_date, reverse=True)
    
    html_notas = "<table class='tabla-historial' style='width: 100%;'>"
    html_notas += "<tr><th>FECHA</th><th>MATERIA</th><th>EXAMEN</th><th>NOTA</th></tr>"
    for m in notas_guardadas:
        try: fecha_str = date.fromisoformat(m['fecha_examen']).strftime('%d/%m/%Y')
        except: fecha_str = "---"
        html_notas += f"<tr><td><span style='font-weight:bold; color:#f8fafc;'>{fecha_str}</span></td><td><div class='materia-pill'>{m['materia']}</div></td><td>{m['nombre']}</td><td><span class='efic-green'>{m['nota']}</span></td></tr>"
    html_notas += "</table>"
    st.markdown(html_notas, unsafe_allow_html=True)

@st.dialog("Nueva Materia Activa")
def dialog_nueva_materia_activa():
    materias_validas = [m['nombre'] for m in st.session_state['plan_carrera'] if m['estado'] in ["Cursando", "Regular"]]
    materias_ya_activas = [m['nombre'] for m in st.session_state['materias']]
    opciones_disponibles = [m for m in materias_validas if m not in materias_ya_activas]
    if not opciones_disponibles:
        st.warning("No tenés materias en estado 'Cursando' o 'Regular' disponibles para agregar.")
        return
    
    n = st.selectbox("Seleccionar Materia", opciones_disponibles)
    colores = {
        "Celeste": "#365b77", "Verde": "#22c55e", "Amarillo": "#eab308", 
        "Violeta": "#a855f7", "Naranja": "#f97316", "Rosa": "#ec4899", "Gris": "#7498b6"
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
            "TIEMPO (min)": tiempo_neto, "EFIC.": f"{eficiencia}%", "INTERRUPCIONES": []
        }
        st.session_state['historial'].append(nueva_sesion)
        
        # XP LOGIC PARA SESION MANUAL
        xp_ganada = int(tiempo_neto * 10 * multiplicador_xp)
        if eficiencia == 100:
            xp_ganada = int(xp_ganada * 1.2)
        st.session_state['xp_total'] += xp_ganada
        
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
    st.markdown("### Navegación")
    menu_opcion = st.radio("Navegación", ["Página Principal", "Resumen", "Organización", "Carrera", "Plan de Estudios", "Perfil & Recompensas"], label_visibility="collapsed")
    
    # --- FRASES MOTIVACIONALES (FONDO DEL MENÚ) ---
    st.markdown("<br>", unsafe_allow_html=True)
    frases = [
        '"El éxito es la suma de pequeños esfuerzos repetidos día tras día."<br>- Robert Collier',
        '"No te detengas hasta que te sientas orgulloso."<br>- Anónimo',
        '"Estudia no para saber una cosa más, sino para saberla mejor."<br>- Séneca',
        '"La disciplina es el puente entre tus metas y tus logros."<br>- Jim Rohn',
        '"No es fácil, no es rápido, pero vale la pena"<br>- Anónimo',
        '"La educación es el arma más poderosa que puedes usar para cambiar el mundo"<br>- Nelson Mandela',
        '"Dime y lo olvido, enséñame y lo recuerdo, involúcrame y lo aprendo."<br>- Benjamin Franklin',
        '"Invertir en conocimientos produce los mejores intereses."<br>- Benjamin Franklin',
        '"La raíz de la educación es amarga, pero su fruto es dulce."<br>- Aristóteles',
        '"El objetivo principal de la educación es crear personas capaces de hacer cosas nuevas y no simplemente repetir lo que otras generaciones hicieron."<br>- Jean Piaget',
        '"El aprendizaje es un tesoro que seguirá a su dueño a todas partes."<br>- Proverbio Chino',
        '"Hay una fuerza motriz más poderosa que el vapor, la electricidad y la energía atómica: la voluntad."<br>- Albert Einstein',
        '"La curiosidad es más importante que el conocimiento."<br>- Albert Einstein',
        '"La educación consiste en enseñar a pensar por uno mismo y no en memorizar datos."<br>- Noam Chomsky',
        '"El hombre no es nada más que lo que la educación hace de él."<br>- Immanuel Kant',
        '"Los científicos investigan lo que ya es; los ingenieros crean lo que nunca ha existido."<br>- Theodore von Kármán',
        '"En las matemáticas no hay caminos reales; y los caminos polvorientos y empinados son los que llevan a la cima."<br>- Euclides',
        '"La física es la poesía de la naturaleza."<br>- Richard Feynman',
        '"Hay que demostrar nuestras equivocaciones lo más rápido posible, es la única manera de avanzar."<br>- Richard Feynman',
        '"No confundas educación con inteligencia, puedes tener un doctorado y seguir siendo un idiota."<br>- Richard Feynman',
        '"La vida es y seguirá siendo una ecuación sin solución, pero contiene algunos factores conocidos."<br>- Nikola Tesla',
        '"La educación es el pasaporte hacia el futuro."<br>- Malcolm X'
    ]
    frase_diaria = random.choice(frases)
    st.markdown(f"<div style='background-color: #02152b; padding: 10px; border-radius: 8px; border: 1px solid #153f59; font-size: 11px; color: #94b8d7; font-style: italic; text-align: center; line-height: 1.4;'>{frase_diaria}</div>", unsafe_allow_html=True)
    
    # --- NUEVA FUNCIÓN: PROGRESO DIARIO (MÁS COMPACTO Y ARRIBA) ---
    st.markdown("<hr class='custom-hr' style='margin: 10px 0;'>", unsafe_allow_html=True)
    st.markdown("<div style='font-size: 11px; color: #7498b6; font-weight: bold; text-transform: uppercase; margin-bottom: 5px;'>Progreso Diario</div>", unsafe_allow_html=True)
    
    hoy_str = date.today().strftime("%d/%m/%Y")
    mins_hoy = sum([h['TIEMPO (min)'] for h in st.session_state['historial'] if h['FECHA'] == hoy_str])
    meta_diaria = 120 # Meta de 2 horas
    progreso = min(mins_hoy / meta_diaria, 1.0)
    
    st.markdown(f"<div style='font-size: 13px; color: #f8fafc; font-weight: bold; margin-bottom: 5px;'>Estudiado: {mins_hoy} min</div>", unsafe_allow_html=True)
    st.progress(progreso)
    st.caption(f"Meta: {meta_diaria} min")

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
            <div style="width: 100%; height: 20px; border-radius: 10px; display: flex; overflow: hidden; margin-bottom: 25px; border: 1px solid #153f59;">
                <div style="width: {p_apr}%; background-color: #22c55e;" title="Aprobadas: {p_apr:.1f}%"></div>
                <div style="width: {p_reg}%; background-color: #eab308;" title="Regulares: {p_reg:.1f}%"></div>
                <div style="width: {p_curs}%; background-color: #3b82f6;" title="Cursando: {p_curs:.1f}%"></div>
                <div style="width: {p_lib}%; background-color: #ef4444;" title="Libres: {p_lib:.1f}%"></div>
                <div style="width: {p_pend}%; background-color: #7498b6;" title="Pendientes: {p_pend:.1f}%"></div>
            </div>
            """, unsafe_allow_html=True)
            
            c1, c2, c3, c4, c5 = st.columns(5)
            c1.markdown(f"<div style='text-align:center;'><div style='font-size:24px; font-weight:bold; color:#22c55e;'>{p_apr:.1f}%</div><div style='color:#7498b6; font-size:11px; font-weight:bold;'>APROBADAS ({aprobadas})</div></div>", unsafe_allow_html=True)
            c2.markdown(f"<div style='text-align:center;'><div style='font-size:24px; font-weight:bold; color:#eab308;'>{p_reg:.1f}%</div><div style='color:#7498b6; font-size:11px; font-weight:bold;'>REGULARES ({regulares})</div></div>", unsafe_allow_html=True)
            c3.markdown(f"<div style='text-align:center;'><div style='font-size:24px; font-weight:bold; color:#3b82f6;'>{p_curs:.1f}%</div><div style='color:#7498b6; font-size:11px; font-weight:bold;'>CURSANDO ({cursando})</div></div>", unsafe_allow_html=True)
            c4.markdown(f"<div style='text-align:center;'><div style='font-size:24px; font-weight:bold; color:#ef4444;'>{p_lib:.1f}%</div><div style='color:#7498b6; font-size:11px; font-weight:bold;'>LIBRES ({libres})</div></div>", unsafe_allow_html=True)
            c5.markdown(f"<div style='text-align:center;'><div style='font-size:24px; font-weight:bold; color:#94b8d7;'>{p_pend:.1f}%</div><div style='color:#7498b6; font-size:11px; font-weight:bold;'>PENDIENTES ({pendientes})</div></div>", unsafe_allow_html=True)
            
            st.divider()
            col_izq, col_der = st.columns(2, gap="large")
            
            def calcular_prioridad(nombre_mat):
                count = 0
                for m in st.session_state['plan_carrera']:
                    if nombre_mat in m.get('req_regulares', []): count += 1
                    if nombre_mat in m.get('req_aprobadas', []): count += 1
                return count

            with col_izq:
                st.markdown("### Cursando y Regulares")
                mat_cursando = [m for m in st.session_state['plan_carrera'] if m['estado'] in ["Cursando", "Regular"]]
                mat_cursando.sort(key=lambda x: calcular_prioridad(x['nombre']), reverse=True)
                
                if not mat_cursando: st.info("No tenés materias en estado 'Cursando' o 'Regular'.")
                else:
                    for m in mat_cursando:
                        color_border = "#eab308" if m['estado'] == "Regular" else "#3b82f6"
                        st.markdown(f"""
                        <style>
                            div[data-testid="stButton"] button[key="btn_carr_curs_{m['id']}"] {{
                                background-color: transparent; color: #f8fafc; text-align: left;
                                border: none; border-left: 4px solid {color_border}; justify-content: flex-start;
                                padding-left: 15px; font-size: 14px;
                            }}
                        </style>
                        """, unsafe_allow_html=True)
                        if st.button(f"{m['nombre']} ({m['estado']})", key=f"btn_carr_curs_{m['id']}", use_container_width=True):
                            dialog_detalle_materia(m['id'])
            
            with col_der:
                st.markdown("### Puedo Cursar")
                def is_met_carr(m_name, req_type):
                    target = next((m for m in st.session_state['plan_carrera'] if m['nombre'] == m_name), None)
                    if not target: return False
                    if req_type == 'reg': return target['estado'] in ["Regular", "Aprobada/Promocionada"]
                    return target['estado'] == "Aprobada/Promocionada"
                    
                puedo_cursar = []
                for m in st.session_state['plan_carrera']:
                    if m['estado'] in ["Pendiente", "Libre/Recursado"]:
                        req_reg_ok = all(is_met_carr(r, 'reg') for r in m.get('req_regulares', []))
                        req_apr_ok = all(is_met_carr(r, 'apr') for r in m.get('req_aprobadas', []))
                        if req_reg_ok and req_apr_ok: puedo_cursar.append(m)
                            
                puedo_cursar.sort(key=lambda x: calcular_prioridad(x['nombre']), reverse=True)
                            
                if not puedo_cursar: st.info("No hay materias nuevas habilitadas.")
                else:
                    for m in puedo_cursar:
                        color_border = "#7498b6" if m['estado'] == "Pendiente" else "#ef4444"
                        st.markdown(f"""
                        <style>
                            div[data-testid="stButton"] button[key="btn_carr_puedo_{m['id']}"] {{
                                background-color: transparent; color: #f8fafc; text-align: left;
                                border: none; border-left: 4px solid {color_border}; justify-content: flex-start;
                                padding-left: 15px; font-size: 14px;
                            }}
                        </style>
                        """, unsafe_allow_html=True)
                        if st.button(m['nombre'], key=f"btn_carr_puedo_{m['id']}", use_container_width=True):
                            dialog_detalle_materia(m['id'])

            st.divider()
            
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
            <div style="background-color: transparent; border-radius: 12px; padding: 20px; text-align: center; margin-top: 10px; border: 1px solid #153f59;">
                <div style="color: #7498b6; font-size: 14px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px;">PROMEDIO GENERAL</div>
                <div style="color: #10b981; font-size: 38px; font-weight: 800; line-height: 1;">{promedio:.2f}</div>
            </div>
            """, unsafe_allow_html=True)
            
            st.write("<br>", unsafe_allow_html=True)
            if st.button("Histórico de Notas", use_container_width=True):
                dialog_historico_notas()

            st.markdown("<hr class='custom-hr'>", unsafe_allow_html=True)
            st.markdown("### Calendario de Eventos")
            
            with st.expander("Ver / Editar Eventos Manuales"):
                st.info("Pegá acá las fechas de la facu. Usá un guion (-) para separar la fecha del evento. Ej: '15/12 al 20/12 - Inscripciones'. Las fechas pasadas se van a ocultar solas.")
                texto_cal = st.text_area("Eventos manuales", value=st.session_state.get('calendario_manual', ''), height=120, label_visibility="collapsed")
                if st.button("Guardar Eventos", type="primary", use_container_width=True):
                    st.session_state['calendario_manual'] = texto_cal
                    if guardar_datos(): st.rerun()

            eventos = []
            hoy = date.today()
            
            # --- 1. PROCESAR AUTOMÁTICOS (METAS) ---
            for m in st.session_state['metas']:
                if m.get('fecha_examen'):
                    try:
                        f_obj = date.fromisoformat(m['fecha_examen'])
                        if f_obj >= hoy:
                            eventos.append({
                                'inicio': f_obj,
                                'fin': f_obj,
                                'texto': m['nombre'],
                                'materia': m['materia']
                            })
                    except: pass
                    
            # --- 2. PROCESAR MANUALES (CON INICIO Y FIN) ---
            manual_lines = [line.strip() for line in st.session_state.get('calendario_manual', '').split('\n') if line.strip()]
            for line in manual_lines:
                match_all = re.findall(r'(\d{1,2})[/-](\d{1,2})(?:[/-](\d{2,4}))?', line)
                if not match_all:
                    continue 
                
                d1, m1, y1 = match_all[0]
                y1 = int(y1) if y1 else hoy.year
                if y1 < 100: y1 += 2000
                
                d2, m2, y2 = match_all[-1]
                y2 = int(y2) if y2 else hoy.year
                if y2 < 100: y2 += 2000
                
                try:
                    f_obj = date(y1, int(m1), int(d1))
                    f_fin = date(y2, int(m2), int(d2))
                    if f_fin < hoy: 
                        continue 
                except:
                    continue
                    
                partes = line.split('-', 1)
                texto = partes[1].strip() if len(partes) > 1 else line
                    
                eventos.append({
                    'inicio': f_obj,
                    'fin': f_fin,
                    'texto': texto,
                    'materia': None
                })
                
            # --- 3. DIBUJAR CALENDARIO CON BARRAS CONTINUAS ---
            if not eventos:
                st.info("No hay eventos próximos.")
            else:
                import calendar
                min_date = min(e['inicio'] for e in eventos)
                max_date = max(e['fin'] for e in eventos)
                
                def get_color(materia):
                    if not materia: return "#365b77"
                    return next((m.get('color', '#10b981') for m in st.session_state.get('materias', []) if m['nombre'] == materia), "#10b981")

                meses = ["", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
                
                html_cal = ""
                y, m = min_date.year, min_date.month
                
                while (y, m) <= (max_date.year, max_date.month):
                    _, days_in_month = calendar.monthrange(y, m)
                    start_of_month = date(y, m, 1)
                    end_of_month = date(y, m, days_in_month)
                    
                    eventos_mes = [e for e in eventos if e['inicio'] <= end_of_month and e['fin'] >= start_of_month]
                    
                    if eventos_mes:
                        html_cal += f"<h4 style='color: #94b8d7; margin-top: 20px; text-transform: uppercase;'>{meses[m]} {y}</h4>"
                        html_cal += "<table style='width: 100%; border-collapse: collapse; table-layout: fixed; margin-bottom: 20px;'>"
                        html_cal += "<tr style='color: #7498b6; font-size: 11px; text-align: center; background-color: transparent;'><th>LUN</th><th>MAR</th><th>MIE</th><th>JUE</th><th>VIE</th><th>SAB</th><th>DOM</th></tr>"
                        
                        cal_weeks = calendar.monthcalendar(y, m)
                        for week in cal_weeks:
                            week_dates = [date(y, m, d) if d != 0 else None for d in week]
                            
                            week_events = []
                            for e in eventos_mes:
                                valid_dates = [wd for wd in week_dates if wd is not None]
                                if valid_dates and e['inicio'] <= valid_dates[-1] and e['fin'] >= valid_dates[0]:
                                    week_events.append(e)
                                    
                            week_events.sort(key=lambda e: (-(e['fin'] - e['inicio']).days, e['inicio']))
                            
                            slots = []
                            event_slots = {}
                            for e in week_events:
                                assigned = False
                                for s_idx, s in enumerate(slots):
                                    overlap = False
                                    for wd in week_dates:
                                        if wd and e['inicio'] <= wd <= e['fin'] and wd in s:
                                            overlap = True
                                            break
                                    if not overlap:
                                        for wd in week_dates:
                                            if wd and e['inicio'] <= wd <= e['fin']:
                                                s.append(wd)
                                        event_slots[id(e)] = s_idx
                                        assigned = True
                                        break
                                if not assigned:
                                    new_slot = []
                                    for wd in week_dates:
                                        if wd and e['inicio'] <= wd <= e['fin']:
                                            new_slot.append(wd)
                                    slots.append(new_slot)
                                    event_slots[id(e)] = len(slots) - 1

                            html_cal += "<tr>"
                            for i, d in enumerate(week):
                                if d == 0:
                                    html_cal += "<td style='border: 1px solid #153f59; background-color: rgba(2, 21, 43, 0.3); height: 85px;'></td>"
                                else:
                                    wd = date(y, m, d)
                                    is_today = wd == hoy
                                    bg_color = "transparent"
                                    circle_style = "background-color: #10b981; color: #02152b; border-radius: 50%; width: 20px; height: 20px; display: inline-flex; justify-content: center; align-items: center;" if is_today else ""
                                    day_num_html = f"<div style='color: #f8fafc; font-weight: bold; font-size: 12px; margin: 4px 4px 2px 4px;'><span style='{circle_style}'>{d}</span></div>"
                                    
                                    html_cal += f"<td style='border: 1px solid #153f59; background-color: {bg_color}; padding: 0; vertical-align: top; height: 85px; position: relative;'>"
                                    html_cal += day_num_html
                                    
                                    for s_idx in range(len(slots)):
                                        ev = next((e for e in week_events if event_slots[id(e)] == s_idx and e['inicio'] <= wd <= e['fin']), None)
                                        if ev:
                                            color = get_color(ev['materia'])
                                            is_start = wd == ev['inicio'] or i == 0 or week_dates[i-1] is None
                                            text = ev['texto'] if is_start else "&nbsp;"
                                            radius = ""
                                            if wd == ev['inicio']: radius += "border-top-left-radius: 4px; border-bottom-left-radius: 4px; "
                                            if wd == ev['fin']: radius += "border-top-right-radius: 4px; border-bottom-right-radius: 4px; "
                                            m_left = "4px" if wd == ev['inicio'] else "0"
                                            m_right = "4px" if wd == ev['fin'] else "0"
                                            html_cal += f"<div style='background-color: {color}E6; color: #02152b; font-size: 10px; padding: 2px 4px; margin-top: 2px; margin-left: {m_left}; margin-right: {m_right}; {radius} overflow: hidden; white-space: nowrap; text-overflow: ellipsis; height: 18px; line-height: 14px;' title='{ev['texto']}'><b>{text}</b></div>"
                                        else:
                                            html_cal += "<div style='height: 20px; margin-top: 2px;'></div>"
                                            
                                    html_cal += "</td>"
                            html_cal += "</tr>"
                        html_cal += "</table>"
                    
                    m += 1
                    if m > 12:
                        m = 1
                        y += 1
                        
                st.markdown(html_cal, unsafe_allow_html=True)

    elif menu_opcion == "Plan de Estudios":
        c_head1, c_head2 = st.columns([4, 1])
        with c_head1:
            st.header("Plan de Estudios")
        with c_head2:
            if st.button("Añadir Materia", type="primary", use_container_width=True):
                dialog_nueva_materia_plan()
                
        st.divider()
        
        if not st.session_state['plan_carrera']:
            st.info("Todavía no agregaste ninguna materia a tu plan de estudios.")
        else:
            df_plan = pd.DataFrame(st.session_state['plan_carrera'])
            anios = sorted(df_plan['año'].unique().tolist(), key=lambda x: int(x) if str(x).isdigit() else 999)
            
            for anio in anios:
                st.markdown(f"### Año {anio}" if str(anio).isdigit() else f"### {anio}")
                materias_anio = df_plan[df_plan['año'] == anio]
                cols = st.columns(4)
                for i, row in materias_anio.reset_index().iterrows():
                    with cols[i % 4]:
                        with st.container():
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
                            
                            cuatri_html = f"<span style='float:right; font-size: 10px; color: #7498b6; font-weight: bold;'>{cuatri_abrev}</span>" if cuatri_abrev else ""

                            html_badges = f"""
                            <div style="margin-bottom: 5px;">
                                <span class='{color_clase}'>{row['estado']}</span>
                                {cuatri_html}
                            </div>
                            """
                            st.markdown(html_badges, unsafe_allow_html=True)
                            
                            if st.button(row['nombre'], key=f"btn_info_{row['id']}", use_container_width=True):
                                dialog_detalle_materia(row['id'])
                                
                            html_reqs = ""
                            if isinstance(row.get('req_regulares'), list) and len(row['req_regulares']) > 0: 
                                html_reqs += f"<div style='font-size: 10px; color: #7498b6; margin-bottom: 1px;'><b>Reg:</b> {', '.join(row['req_regulares'])}</div>"
                            if isinstance(row.get('req_aprobadas'), list) and len(row['req_aprobadas']) > 0: 
                                html_reqs += f"<div style='font-size: 10px; color: #7498b6;'><b>Apr:</b> {', '.join(row['req_aprobadas'])}</div>"
                            
                            if html_reqs: st.markdown(html_reqs, unsafe_allow_html=True)

    elif menu_opcion == "Resumen":
        renderizar_analitica()

    elif menu_opcion == "Organización":
        with st.container(border=True):
            c_head1, c_head2 = st.columns([4, 1])
            with c_head1: st.markdown("### Materias Activas (Cronómetro)")
            with c_head2:
                if st.button("Nueva Materia", type="secondary", use_container_width=True):
                    dialog_nueva_materia_activa()
                    
            cols_mat = st.columns(3)
            for i, mat in enumerate(st.session_state['materias']):
                estado_badge = ""
                for plan_mat in st.session_state['plan_carrera']:
                    if plan_mat['nombre'] == mat['nombre']:
                        if plan_mat['estado'] == "Cursando":
                            estado_badge = "<div style='margin-top: 5px;'><span class='badge-cursando'>Cursando</span></div>"
                        elif plan_mat['estado'] == "Regular":
                            estado_badge = "<div style='margin-top: 5px;'><span class='badge-regular'>Regular</span></div>"
                        break

                with cols_mat[i % 3]:
                    st.markdown(f"""
                    <div style="border: 1px solid #153f59; border-radius: 12px; padding: 15px; text-align: center; background-color: transparent; margin-bottom: 10px;">
                        <div class="color-circle" style="background-color: {mat['color']};"></div>
                        <div style="font-size: 15px; font-weight: 600;">{mat['nombre']}</div>
                        {estado_badge}
                    </div>
                    """, unsafe_allow_html=True)
                    if st.button("Eliminar", key=f"del_mat_{i}", use_container_width=True):
                        st.session_state['materias'].pop(i)
                        if guardar_datos(): st.rerun()
                        
        st.write("<br>", unsafe_allow_html=True)
        with st.container(border=True):
            c_dist1, c_dist2 = st.columns([4, 1])
            with c_dist1: st.markdown("### Gestionar Distracciones")
            with c_dist2:
                nueva_dist = st.text_input("Nueva Distracción", label_visibility="collapsed", placeholder="Ej: Baño...")
                if st.button("Añadir", type="secondary", key="btn_dist", use_container_width=True):
                    if nueva_dist and nueva_dist not in st.session_state['distracciones']:
                        st.session_state['distracciones'].append(nueva_dist)
                        if guardar_datos(): st.rerun()

            cols_dist = st.columns(4)
            for i, dist in enumerate(st.session_state['distracciones']):
                with cols_dist[i % 4]:
                    st.markdown(f"""
                    <div style="border: 1px solid #153f59; border-radius: 10px; padding: 10px; text-align: center; background-color: transparent; margin-bottom: 5px;">
                        <div style="font-weight: 600; font-size: 14px;">{dist}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    if st.button("Eliminar", key=f"del_dist_{i}", use_container_width=True):
                        st.session_state['distracciones'].pop(i)
                        if guardar_datos(): st.rerun()

        st.write("<br>", unsafe_allow_html=True)
        with st.container(border=True):
            c_met1, c_met2 = st.columns([4, 1])
            with c_met1: st.markdown("### Gestionar Métodos")
            with c_met2:
                nuevo_met = st.text_input("Nuevo Método", label_visibility="collapsed", placeholder="Ej: Mapa mental...")
                if st.button("Añadir", type="secondary", key="btn_met", use_container_width=True):
                    if nuevo_met and nuevo_met not in st.session_state['metodos']:
                        st.session_state['metodos'].append(nuevo_met)
                        if guardar_datos(): st.rerun()

            cols_met = st.columns(4)
            for i, met in enumerate(st.session_state['metodos']):
                with cols_met[i % 4]:
                    st.markdown(f"""
                    <div style="border: 1px solid #153f59; border-radius: 10px; padding: 10px; text-align: center; background-color: transparent; margin-bottom: 5px;">
                        <div style="font-weight: 600; font-size: 14px;">{met}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    if st.button("Eliminar", key=f"del_met_{i}", use_container_width=True):
                        st.session_state['metodos'].pop(i)
                        if guardar_datos(): st.rerun()

    elif menu_opcion == "Perfil & Recompensas":
        st.header("Perfil del Estudiante")
        
        xp_actual = st.session_state.get('xp_total', 0)
        rangos = [
            (0, "Material: Cobre"), 
            (5000, "Material: Hierro"), 
            (15000, "Material: Acero"), 
            (30000, "Material: Titanio"), 
            (50000, "Material: Wolframio")
        ]
        rango_actual = rangos[0][1]
        prox_meta = 5000
        for limite, nombre in rangos:
            if xp_actual >= limite:
                rango_actual = nombre
            else:
                prox_meta = limite
                break
                
        progreso_rango = min(xp_actual / prox_meta, 1.0)
        
        c_r1, c_r2 = st.columns([1, 3])
        with c_r1:
            st.markdown(f"""
            <div style="background-color: transparent; border: 1px solid #153f59; padding: 20px; text-align: center;">
                <div style="font-size: 14px; color: #7498b6;">RANGO ACTUAL</div>
                <div style="font-size: 24px; font-weight: bold; color: #f8fafc;">{rango_actual}</div>
            </div>
            """, unsafe_allow_html=True)
        with c_r2:
            st.write(f"Progreso hacia el siguiente rango ({xp_actual} / {prox_meta} XP)")
            st.progress(progreso_rango)

        st.divider()
        
        st.subheader("Tienda de Recompensas")
        st.write(f"Saldo disponible: {xp_actual} XP")
        
        cols_tienda = st.columns(3)
        for i, rec in enumerate(st.session_state['recompensas']):
            with cols_tienda[i % 3]:
                with st.container(border=True):
                    st.write(f"**{rec['nombre']}**")
                    st.write(f"Costo: {rec['costo']} XP")
                    if st.button("Canjear", key=f"canjear_{i}", disabled=xp_actual < rec['costo']):
                        st.session_state['xp_total'] -= rec['costo']
                        if guardar_datos(): st.rerun()
                        
        with st.expander("Crear nueva recompensa"):
            n_nombre = st.text_input("Premio")
            n_costo = st.number_input("Costo (XP)", min_value=100, step=100)
            if st.button("Agregar a la tienda"):
                st.session_state['recompensas'].append({"nombre": n_nombre, "costo": n_costo})
                if guardar_datos(): st.rerun()

        st.divider()
        
        st.subheader("Logros Desbloqueados")
        logros_html = "<div style='display: flex; gap: 10px; flex-wrap: wrap;'>"
        
        if racha_actual >= 14:
            logros_html += "<div style='border: 1px solid #10b981; color: #10b981; padding: 5px 15px; border-radius: 20px;'>Inmortal (Racha 14d)</div>"
            
        sesiones_largas = [h for h in st.session_state['historial'] if int(h['TIEMPO (min)']) >= 180]
        if sesiones_largas:
            logros_html += "<div style='border: 1px solid #eab308; color: #eab308; padding: 5px 15px; border-radius: 20px;'>Maquina (3h de corrido)</div>"
            
        if not (racha_actual >= 14 or sesiones_largas):
            logros_html += "<div style='color: #7498b6; font-size: 14px;'>Segui estudiando para desbloquear logros.</div>"
            
        logros_html += "</div>"
        st.markdown(logros_html, unsafe_allow_html=True)


    elif menu_opcion == "Página Principal":
        
        # --- ALINEACIÓN BOTÓN DE RACHA (FLOTANTE JUNTO A PESTAÑAS) ---
        c_empty, c_racha = st.columns([6, 1])
        with c_racha:
            if st.button(f"Racha: {racha_actual} días", help="Ver detalles", use_container_width=True):
                st.session_state['show_racha_modal'] = True
                
        # Subimos las pestañas para que queden en la misma línea visual que el botón
        st.markdown("<style>div[data-testid='stTabs'] { margin-top: -45px; }</style>", unsafe_allow_html=True)
        
        tabs = st.tabs(["Cronómetro", "Temario", "Analítica", "Metas", "Historial"])

        def render_meta_card(meta, original_idx, is_pasada, hoy, prefijo_key):
            try: fecha_str = date.fromisoformat(meta['fecha_examen']).strftime('%d/%m/%Y')
            except: fecha_str = ""
            
            dias_sel = meta.get('dias_estudio', ["L", "M", "X", "J", "V", "S", "D"])
            dias_map = {"L":0, "M":1, "X":2, "J":3, "V":4, "S":5, "D":6}
            selected_ints = [dias_map[d] for d in dias_sel if d in dias_map]
            
            dias_restantes = 0
            if not is_pasada:
                exam_date = date.fromisoformat(meta['fecha_examen'])
                delta = (exam_date - hoy).days
                for j in range(delta):
                    if (hoy + pd.Timedelta(days=j)).weekday() in selected_ints:
                        dias_restantes += 1
            
            etiqueta_estado = f"<span style='color: #10b981; font-weight:800; float:right;'>{dias_restantes} días</span>" if not is_pasada else "<span style='color: #ef4444; float:right;'>Examen pasado</span>"
            
            c_title, c_dots = st.columns([6, 1])
            with c_title:
                pass 
            with c_dots:
                st.markdown(f"""
                <style>
                    div[data-testid="stButton"] button[key="btn_edit_meta_{prefijo_key}_{original_idx}"] {{
                        background: transparent; border: none; padding: 0; color: #7498b6; font-size: 18px; margin-top: -5px; box-shadow: none;
                    }}
                    div[data-testid="stButton"] button[key="btn_edit_meta_{prefijo_key}_{original_idx}"]:hover {{
                        color: #f8fafc; background: transparent;
                    }}
                </style>
                """, unsafe_allow_html=True)
                if st.button("⋮", key=f"btn_edit_meta_{prefijo_key}_{original_idx}", help="Editar o eliminar meta"):
                    dialog_editar_meta(original_idx)
            
            progreso = min(meta['horas_acumuladas'] / meta['meta_horas'], 1.0)
            pct = int(progreso * 100)
            
            color_materia = next((m.get('color', '#7498b6') for m in st.session_state.get('materias', []) if isinstance(m, dict) and m.get('nombre') == meta['materia']), "#7498b6")
            
            st.markdown(f"""
            <div style='display:flex; justify-content:space-between; align-items:center;'>
                <h4 style='margin-bottom: 0px;'>{meta['nombre']}</h4>
                <h4 style='margin-bottom: 0px;'>{pct}%</h4>
            </div>
            <div style='font-size: 12px; font-weight: bold; margin-bottom: 10px;'><span style='color: {color_materia};'>{meta['materia']}</span> {etiqueta_estado}</div>
            """, unsafe_allow_html=True)
            
            st.progress(progreso)
            
            if not is_pasada:
                horas_faltantes = max(0.0, meta['meta_horas'] - meta['horas_acumuladas'])
                if dias_restantes > 0:
                    h_pd = horas_faltantes / dias_restantes
                    h_pd_int = int(h_pd)
                    m_pd_int = int((h_pd - h_pd_int) * 60)
                    txt_diario = f"{h_pd_int}h {m_pd_int:02d}m / día"
                else:
                    if horas_faltantes > 0:
                        txt_diario = "¡Último día!"
                    else:
                        txt_diario = "0h 00m / día"
                
                st.markdown(f"<div style='text-align:right; font-size: 11px; color: #7498b6; font-weight:bold;'>Estudiar: {txt_diario} (Total: {meta['meta_horas']}h)</div>", unsafe_allow_html=True)
            
            if is_pasada:
                if meta.get('nota'):
                    st.markdown(f"<div class='nota-box'><b>NOTA FINAL</b>&nbsp;&nbsp;&nbsp;&nbsp; <span style='font-size: 18px; font-weight: 800; color: #10b981;'>{meta['nota']}</span></div>", unsafe_allow_html=True)
                else:
                    st.write("<br>", unsafe_allow_html=True)
                    if st.button("Asignar Nota", key=f"nota_{prefijo_key}_{original_idx}", use_container_width=True):
                        dialog_asignar_nota(original_idx)

        with tabs[0]:
            if st.session_state['timer']['state'] == 'IDLE':
                col_izq, col_der = st.columns([1, 2], gap="large")
                
                with col_izq:
                    hoy = date.today()
                    metas_actuales = []
                    for i, m in enumerate(st.session_state['metas']):
                        try:
                            if date.fromisoformat(m['fecha_examen']) >= hoy:
                                metas_actuales.append((i, m))
                        except: pass
                        
                    if not metas_actuales:
                        with st.container(border=True):
                            st.info("No tenés metas próximas. ¡Todo al día!")
                    else:
                        idx, meta_priority = metas_actuales[0]
                        with st.container(border=True):
                            render_meta_card(meta_priority, idx, False, hoy, "tab0")

                with col_der:
                    with st.container(border=True):
                        st.write("<br>", unsafe_allow_html=True)
                        modo_sel = st.radio("Modo", ["Libre", "Pomodoro"], horizontal=True, label_visibility="collapsed")
                        st.session_state['timer']['mode'] = modo_sel
                        
                        if modo_sel == "Pomodoro":
                            cp1, cp2 = st.columns(2)
                            f_time = cp1.number_input("Minutos de Enfoque", min_value=1, value=st.session_state['timer']['focus_time'])
                            b_time = cp2.number_input("Minutos de Pausa", min_value=1, value=st.session_state['timer']['break_time'])
                            st.session_state['timer']['focus_time'] = f_time
                            st.session_state['timer']['break_time'] = b_time
                            
                        st.write("<br>", unsafe_allow_html=True)
                        if st.button("Iniciar Estudio", type="primary", use_container_width=True):
                            st.session_state['timer']['start'] = time.time()
                            st.session_state['timer']['state'] = 'RUNNING'
                            st.rerun()
                        st.write("<br>", unsafe_allow_html=True)

            elif st.session_state['timer']['state'] == 'RUNNING':
                st.markdown("""
                    <style>
                    [data-testid="stSidebarNav"], [data-testid="stSidebar"] { display: none !important; }
                    </style>
                """, unsafe_allow_html=True)
                
                titulo = "Cronómetro Libre" if st.session_state['timer']['mode'] == "Libre" else "Modo Pomodoro (Enfoque)"
                st.markdown(f"<p style='text-align: center; color: #7498b6; font-size: 1.2rem;'>{titulo}</p>", unsafe_allow_html=True)
                current_elapsed = st.session_state['timer']['elapsed'] + (time.time() - st.session_state['timer']['start'])
                render_live_timer(current_elapsed, True)
                
                if st.session_state['timer']['mode'] == "Pomodoro":
                    remaining_seconds = (st.session_state['timer']['focus_time'] * 60) - current_elapsed
                    if remaining_seconds > 0:
                        eta_time = datetime.fromtimestamp(time.time() + remaining_seconds).strftime("%H:%M")
                        st.markdown(f"<p style='text-align: center; color: #94b8d7; font-size: 13px; margin-top: -10px;'>Hora de liberación: {eta_time}</p>", unsafe_allow_html=True)
                
                c1, c2, c3 = st.columns([1, 2, 2])
                with c1:
                    if st.button("Cancelar", use_container_width=True):
                        st.session_state['timer']['state'] = 'IDLE'
                        st.session_state['timer']['elapsed'] = 0.0
                        st.rerun()
                with c2:
                    if st.button("Pausar", use_container_width=True):
                        st.session_state['timer']['elapsed'] += time.time() - st.session_state['timer']['start']
                        st.session_state['timer']['state'] = 'INTERRUPT'
                        st.rerun()
                with c3:
                    if st.button("Terminar", type="primary", use_container_width=True):
                        st.session_state['timer']['elapsed'] += time.time() - st.session_state['timer']['start']
                        st.session_state['timer']['state'] = 'FINISHED'
                        st.rerun()

            elif st.session_state['timer']['state'] == 'INTERRUPT':
                st.markdown("<h2 style='text-align: center;'>Interrupción</h2>", unsafe_allow_html=True)
                st.markdown("<p style='text-align: center; color: #7498b6;'>¿Cuál fue el motivo?</p>", unsafe_allow_html=True)
                st.write("<br>", unsafe_allow_html=True)
                c1, c2 = st.columns(2)
                for i, motivo in enumerate(st.session_state['distracciones']):
                    col = c1 if i % 2 == 0 else c2
                    if col.button(motivo, use_container_width=True):
                        st.session_state['timer']['interruption_reason'] = motivo
                        st.session_state['timer']['interruptions'].append(motivo)
                        st.session_state['timer']['pause_start'] = time.time()
                        st.session_state['timer']['pause_elapsed'] = 0.0
                        st.session_state['timer']['state'] = 'PAUSED'
                        st.rerun()
                st.markdown("<hr class='custom-hr'>", unsafe_allow_html=True)
                if st.button("Volver al Cronómetro", use_container_width=True):
                    st.session_state['timer']['state'] = 'RUNNING'
                    st.session_state['timer']['start'] = time.time()
                    st.rerun()

            elif st.session_state['timer']['state'] == 'PAUSED':
                st.markdown("<h1 style='text-align: center; color: #10b981; margin-bottom: 0;'>PAUSA</h1>", unsafe_allow_html=True)
                motivo = st.session_state['timer'].get('interruption_reason', '')
                
                current_pause = st.session_state['timer']['pause_elapsed'] + (time.time() - st.session_state['timer']['pause_start'])
                
                html_pause = f"""
                <div id="pause_msg" style="text-align: center; color: #7498b6; font-size: 1.2rem; margin-top: 0;">Motivo: {motivo}</div>
                <div id="pause_clock" style="font-size: 85px; font-weight: 700; text-align: center; color: #7498b6; font-family: 'Courier New', Courier, monospace; letter-spacing: 2px; margin: 20px 0;">00:00:00</div>
                <script>
                    var elapsedMs = {current_pause * 1000};
                    var start = Date.now() - elapsedMs;
                    function updateClock() {{
                        var delta = Date.now() - start;
                        
                        if (delta >= 2700000) {{
                            document.getElementById("pause_clock").style.color = "#ef4444";
                            document.getElementById("pause_msg").innerHTML = "¡Tiempo de pausa muy largo, volver al estudio!";
                            document.getElementById("pause_msg").style.color = "#ef4444";
                            document.getElementById("pause_msg").style.fontWeight = "bold";
                        }}
                        
                        var hrs = Math.floor(delta / 3600000).toString().padStart(2, '0');
                        var mins = Math.floor((delta % 3600000) / 60000).toString().padStart(2, '0');
                        var secs = Math.floor((delta % 60000) / 1000).toString().padStart(2, '0');
                        document.getElementById("pause_clock").innerHTML = hrs + ":" + mins + ":" + secs;
                    }}
                    updateClock();
                    setInterval(updateClock, 1000);
                </script>
                """
                components.html(html_pause, height=140)

                c1, c2, c3 = st.columns([1, 2, 1])
                with c2:
                    if st.button("REANUDAR", type="primary", use_container_width=True):
                        st.session_state['timer']['start'] = time.time()
                        st.session_state['timer']['state'] = 'RUNNING'
                        st.rerun()

            elif st.session_state['timer']['state'] == 'FINISHED':
                c_back, c_title, c_empty = st.columns([1, 10, 1])
                with c_back:
                    if st.button("Volver", help="Regresar a Pausa"):
                        st.session_state['timer']['state'] = 'PAUSED'
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
                        st.markdown("<hr class='custom-hr'>", unsafe_allow_html=True)
                        
                        st.caption("VINCULAR OBJETIVO")
                        metas_filtradas = [m for m in st.session_state['metas'] if m['materia'] == materia_sel]
                        opciones_meta = {"-- Sin vincular --": None}
                        for m in metas_filtradas: opciones_meta[m['nombre']] = m['id']
                        meta_sel = st.selectbox("VINCULAR OBJETIVO", list(opciones_meta.keys()), label_visibility="collapsed")
                        st.markdown("<hr class='custom-hr'>", unsafe_allow_html=True)
                        
                        st.caption("MÉTODO")
                        metodo_sel = st.radio("MÉTODO", st.session_state['metodos'], horizontal=True, label_visibility="collapsed")
                        
                        # --- EVALUACIÓN DE LA CURVA DEL OLVIDO ---
                        temas_disponibles = st.session_state.get('temarios', {}).get(materia_sel, [])
                        opciones_temas = ["-- Repaso general / Ninguno --"] + [t['tema'] for t in temas_disponibles]
                        
                        st.markdown("<hr class='custom-hr'>", unsafe_allow_html=True)
                        st.caption("EVALUAR TEMA (Curva del Olvido)")
                        tema_sel = st.selectbox("¿Qué tema estudiaste hoy?", opciones_temas)
                        
                        confianza = 3
                        if tema_sel != "-- Repaso general / Ninguno --":
                            st.write("¿Qué tan bien lo entendiste?")
                            confianza = st.slider("1 = Me costó un montón, 5 = Lo doy en un final oral", 1, 5, 3)
                        
                    st.write("")
                    if st.button("Guardar Sesión", type="primary", use_container_width=True):
                        minutos_estudio = round(st.session_state['timer']['elapsed'] / 60)
                        nueva_sesion = {
                            "FECHA": datetime.now().strftime("%d/%m/%Y"),
                            "MATERIA": materia_sel, "MÉTODO": metodo_sel,
                            "TIEMPO (min)": minutos_estudio, "EFIC.": "100%",
                            "INTERRUPCIONES": st.session_state['timer']['interruptions']
                        }
                        st.session_state['historial'].append(nueva_sesion)
                        
                        # XP LOGIC PARA SESION CON TIMER
                        xp_ganada = int(minutos_estudio * 10 * multiplicador_xp)
                        if not st.session_state['timer']['interruptions']:
                            xp_ganada = int(xp_ganada * 1.2)
                        st.session_state['xp_total'] += xp_ganada
                        
                        st.session_state['timer']['interruptions'] = []
                        
                        id_meta = opciones_meta[meta_sel]
                        if id_meta:
                            for m in st.session_state['metas']:
                                if m['id'] == id_meta:
                                    m['horas_acumuladas'] += (minutos_estudio / 60)
                                    break
                                    
                        # Aplicar la curva al guardar
                        if tema_sel != "-- Repaso general / Ninguno --":
                            metas_materia = [m for m in st.session_state['metas'] if m['materia'] == materia_sel and date.fromisoformat(m['fecha_examen']) >= date.today()]
                            fecha_prox_examen = None
                            if metas_materia:
                                metas_materia.sort(key=lambda x: date.fromisoformat(x['fecha_examen']))
                                if not metas_materia[0].get('temas_examen') or tema_sel in metas_materia[0]['temas_examen']:
                                    fecha_prox_examen = metas_materia[0]['fecha_examen']
                                    
                            for t in st.session_state['temarios'][materia_sel]:
                                if t['tema'] == tema_sel:
                                    nivel_actual = t.get('nivel', 0)
                                    nuevo_nivel, prox_fecha = calcular_proximo_repaso(confianza, nivel_actual, fecha_prox_examen)
                                    t['nivel'] = nuevo_nivel
                                    t['proximo_repaso'] = prox_fecha
                                    break
                        
                        if guardar_datos():
                            st.session_state['timer']['state'] = 'IDLE'
                            st.session_state['timer']['elapsed'] = 0.0
                            st.session_state['timer']['pause_elapsed'] = 0.0
                            time.sleep(1)
                            st.rerun()

            if st.session_state['timer']['state'] == 'IDLE':
                st.markdown("<hr class='custom-hr'>", unsafe_allow_html=True)
                st.markdown("### Mi Horario de Cursado")
                horarios_completos = []
                for m in st.session_state['plan_carrera']:
                    if m['estado'] == "Cursando" and 'horarios_clase' in m:
                        for hc in m['horarios_clase']:
                            if hc.get('dia') != "---" and hc.get('inicio'):
                                ini_c = hc['inicio'].strip()
                                if ":" not in ini_c: ini_c += ":00"
                                if len(ini_c.split(":")[0]) == 1: ini_c = "0" + ini_c
                                
                                fin_c = hc.get('fin', '').strip()
                                if fin_c:
                                    if ":" not in fin_c: fin_c += ":00"
                                    if len(fin_c.split(":")[0]) == 1: fin_c = "0" + fin_c
                                
                                horarios_completos.append({
                                    "materia": m['nombre'], "dia": hc['dia'],
                                    "inicio": ini_c, "fin": fin_c,
                                    "inicio_orig": hc['inicio'], "fin_orig": hc.get('fin', '')
                                })
                
                def get_sortable_time(t_str):
                    try: return datetime.strptime(t_str, "%H:%M").time()
                    except: return datetime.strptime("23:59", "%H:%M").time()

                time_points = set()
                for hc in horarios_completos:
                    time_points.add(hc['inicio'])
                    if hc['fin']: time_points.add(hc['fin'])

                sorted_times = sorted(list(time_points), key=get_sortable_time)
                
                if not sorted_times:
                    st.info("No tenés horarios cargados.")
                else:
                    dias_semana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado"]
                    matriz = {t: {d: [] for d in dias_semana} for t in sorted_times}
                    
                    for hc in horarios_completos:
                        if hc['dia'] in dias_semana:
                            t_ini = get_sortable_time(hc['inicio'])
                            t_fin = get_sortable_time(hc['fin']) if hc['fin'] else get_sortable_time("23:59")
                            
                            for t_row in sorted_times:
                                t_actual = get_sortable_time(t_row)
                                if t_ini <= t_actual < t_fin:
                                    matriz[t_row][hc['dia']].append(hc)
                                    
                    html_tabla = "<table class='tabla-horario'>"
                    html_tabla += "<tr><th>HORARIO</th>"
                    for d in dias_semana: html_tabla += f"<th>{d.upper()}</th>"
                    html_tabla += "</tr>"
                    
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
                                for j in range(i + 1, len(sorted_times)):
                                    next_t = sorted_times[j]
                                    next_items = matriz[next_t][d]
                                    if next_items and next_items[0]['materia'] == mat['materia']: span += 1
                                    else: break
                                
                                skip_cells[d] = span - 1
                                
                                texto = f"<span style='font-size: 10px; font-weight: normal; opacity: 0.8;'>{mat['inicio_orig']}</span><br>"
                                texto += f"{mat['materia']}"
                                if mat['fin_orig']: 
                                    texto += f"<br><span style='font-size: 10px; font-weight: normal; opacity: 0.8;'>{mat['fin_orig']}</span>"
                                
                                html_tabla += f"<td rowspan='{span}'><div class='materia-bloque' style='height: 100%; min-height: 55px; display: flex; flex-direction: column; justify-content: center;'>{texto}</div></td>"
                            else:
                                html_tabla += "<td></td>"
                        html_tabla += "</tr>"
                    html_tabla += "</table>"
                    st.markdown(html_tabla, unsafe_allow_html=True)

        with tabs[1]:
            st.markdown("### Mi Temario y Repasos")
            st.caption("Elegí una materia para ver qué temas te tocan repasar hoy según la curva del olvido.")
            
            materias_con_temario = [m for m, t in st.session_state.get('temarios', {}).items() if len(t) > 0]
            
            if not materias_con_temario:
                st.info("No tenés materias con temario cargado. Andá a 'Plan de Estudios', editá una materia y pegá la lista de temas en 'Ver / Editar Temario'.")
            else:
                mat_sel_temario = st.selectbox("Seleccionar Materia", materias_con_temario, label_visibility="collapsed")
                temas = st.session_state['temarios'][mat_sel_temario]
                
                solo_examen = st.toggle("Mostrar solo temas del próximo examen")
                
                if solo_examen:
                    metas_activas = [m for m in st.session_state['metas'] if m['materia'] == mat_sel_temario and date.fromisoformat(m['fecha_examen']) >= date.today()]
                    if metas_activas:
                        metas_activas.sort(key=lambda x: date.fromisoformat(x['fecha_examen']))
                        temas_del_examen = metas_activas[0].get('temas_examen', [])
                        if temas_del_examen:
                            temas = [t for t in temas if t['tema'] in temas_del_examen]
                    else:
                        st.warning("No tenés exámenes próximos cargados para esta materia.")
                        temas = []
                
                hoy_str = date.today().isoformat()
                vencidos, al_dia, nuevos = [], [], []
                
                for t in temas:
                    if not t.get('proximo_repaso'): nuevos.append(t)
                    elif t['proximo_repaso'] <= hoy_str: vencidos.append(t)
                    else: al_dia.append(t)
                
                if vencidos:
                    st.markdown("<h4 style='color: #ef4444; margin-top: 15px;'>Para Repasar Hoy (Urgente)</h4>", unsafe_allow_html=True)
                    for t in vencidos:
                        try: fecha_rep = date.fromisoformat(t['proximo_repaso']).strftime('%d/%m')
                        except: fecha_rep = "Hoy"
                        st.markdown(f"<div style='background-color: #450a0a; border-left: 4px solid #ef4444; padding: 10px; margin-bottom: 5px; border-radius: 4px;'><b>{t['tema']}</b> <span style='float:right; font-size: 12px; opacity:0.8;'>Venció: {fecha_rep} | Nivel {t.get('nivel', 0)}</span></div>", unsafe_allow_html=True)
                
                if nuevos:
                    st.markdown("<h4 style='color: #7498b6; margin-top: 15px;'>Nuevos (Aún no estudiados)</h4>", unsafe_allow_html=True)
                    for t in nuevos:
                        st.markdown(f"<div style='background-color: transparent; border-left: 4px solid #7498b6; padding: 10px; margin-bottom: 5px; border-radius: 4px;'>{t['tema']}</div>", unsafe_allow_html=True)
                        
                if al_dia:
                    st.markdown("<h4 style='color: #10b981; margin-top: 15px;'>Al Día (Ya estudiados)</h4>", unsafe_allow_html=True)
                    for t in al_dia:
                        try: fecha_rep = date.fromisoformat(t['proximo_repaso']).strftime('%d/%m')
                        except: fecha_rep = ""
                        st.markdown(f"<div style='background-color: #064e3b; border-left: 4px solid #10b981; padding: 10px; margin-bottom: 5px; border-radius: 4px;'><b>{t['tema']}</b> <span style='float:right; font-size: 12px; opacity:0.8;'>Próx. repaso: {fecha_rep} | Nivel {t.get('nivel', 0)}</span></div>", unsafe_allow_html=True)

        with tabs[2]:
            renderizar_analitica()

        with tabs[3]:
            materias_con_metas = list(set([m['materia'] for m in st.session_state['metas']]))
            c_filt1, c_filt2, c_filt3, c_btn3 = st.columns([1, 2.5, 2.5, 2])
            with c_filt1: st.markdown("<div style='padding-top: 8px; color:#7498b6; font-weight:bold;'>Filtros</div>", unsafe_allow_html=True)
            f_mat_metas = c_filt2.selectbox("Materias", ["Todas las materias"] + materias_con_metas, key="filtro_materias_metas", label_visibility="collapsed")
            f_est_metas = c_filt3.selectbox("Estado", ["Todas", "Actuales", "Pasadas"], index=1, key="filtro_estado_metas", label_visibility="collapsed")
            
            with c_btn3:
                if st.button("Nueva Meta", type="primary", use_container_width=True):
                    dialog_nueva_meta()
                    
            st.markdown("<hr class='custom-hr'>", unsafe_allow_html=True)
                    
            if not st.session_state['metas']:
                st.info("No tenés metas creadas. Tocá 'Nueva Meta' para armar tu plan de examen.")
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
                        is_pasada = True
                        try:
                            if date.fromisoformat(meta['fecha_examen']) >= hoy: is_pasada = False
                        except: pass
                        
                        with cols[i % 3]:
                            with st.container(border=True):
                                render_meta_card(meta, original_idx, is_pasada, hoy, "tab2")

        with tabs[4]:
            c_f1, c_f2, c_f3, c_f4, c_space, c_btn = st.columns([1, 2.5, 2.5, 2.5, 0.5, 2])
            with c_f1: 
                st.markdown("<div style='padding-top: 8px; color:#7498b6; font-weight:bold;'>Filtros</div>", unsafe_allow_html=True)
                
            nombres_materias = list(set([h['MATERIA'] for h in st.session_state['historial']]))
            nombres_metodos = list(set([h['MÉTODO'] for h in st.session_state['historial']]))
            
            f_mat_hist = c_f2.selectbox("Materias", ["Todas las materias"] + nombres_materias, key="filtro_mat_hist", label_visibility="collapsed")
            f_tiempo_hist = c_f3.selectbox("Tiempo", ["Hoy", "Última Semana", "Último Mes", "Todo el Historial", "Personalizado..."], index=3, key="filtro_tiempo_hist", label_visibility="collapsed")
            f_met_hist = c_f4.selectbox("Métodos", ["Todos los métodos"] + nombres_metodos, key="filtro_met_hist", label_visibility="collapsed")
            
            with c_btn:
                if st.button("Agregar Sesión", type="primary", use_container_width=True):
                    dialog_agregar_sesion()
                    
            if not st.session_state['historial']:
                st.markdown("<hr class='custom-hr'>", unsafe_allow_html=True)
                st.info("Tu historial está vacío.")
            else:
                st.markdown("<hr class='custom-hr'>", unsafe_allow_html=True)
                df_hist_view = pd.DataFrame(st.session_state['historial']).iloc[::-1]
                
                if f_mat_hist != "Todas las materias": 
                    df_hist_view = df_hist_view[df_hist_view['MATERIA'] == f_mat_hist]
                if f_met_hist != "Todos los métodos": 
                    df_hist_view = df_hist_view[df_hist_view['MÉTODO'] == f_met_hist]
                
                df_hist_view['FECHA_OBJ'] = pd.to_datetime(df_hist_view['FECHA'], format='%d/%m/%Y', errors='coerce')
                hoy = pd.Timestamp.now().normalize()
                
                if f_tiempo_hist == "Hoy":
                    df_hist_view = df_hist_view[df_hist_view['FECHA_OBJ'] == hoy]
                elif f_tiempo_hist == "Última Semana":
                    df_hist_view = df_hist_view[df_hist_view['FECHA_OBJ'] >= (hoy - pd.Timedelta(days=7))]
                elif f_tiempo_hist == "Último Mes":
                    df_hist_view = df_hist_view[df_hist_view['FECHA_OBJ'] >= (hoy - pd.Timedelta(days=30))]

                if df_hist_view.empty:
                    st.warning("No hay sesiones que coincidan con los filtros.")
                else:
                    with st.container(border=True):
                        html_hist = "<table class='tabla-historial' style='width: 100%;'>"
                        html_hist += "<tr><th>FECHA</th><th></th><th>TIEMPO</th><th>EFIC.</th></tr>"
                        for _, row in df_hist_view.iterrows():
                            fecha_str = row.get('FECHA', '')
                            fecha_disp = f"<div style='font-weight:900; font-size:14px; color:#f8fafc;'>{fecha_str}</div><div style='font-size:11px; font-weight:600; color:#7498b6; margin-top:2px;'>--:--</div>"
                            mat_str = row.get('MATERIA', '')
                            tiempo_str = f"<span style='color:#7498b6; font-weight:700; font-size:13px;'>{row.get('TIEMPO (min)', '')} min</span>"
                            efic_str = row.get('EFIC.', '')
                            html_hist += f"<tr><td>{fecha_disp}</td><td><div class='materia-pill'>{mat_str}</div></td><td>{tiempo_str}</td><td><span class='efic-green'>{efic_str}</span></td></tr>"
                        html_hist += "</table>"
                        
                        st.markdown(html_hist, unsafe_allow_html=True)
