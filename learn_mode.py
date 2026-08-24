import streamlit as st
import random
import time
import unicodedata
import re
from datetime import datetime
from db import cargar_flashcards, guardar_todas_flashcards, guardar_datos

def safe_int(val, default=0):
    try:
        if str(val).strip() == "": return default
        return int(val)
    except (ValueError, TypeError):
        return default

def normalizar_texto(texto):
    if not texto: return ""
    texto = unicodedata.normalize('NFD', str(texto)).encode('ascii', 'ignore').decode('utf-8')
    texto = texto.lower()
    texto = re.sub(r'[.,;¿?¡!()"\'\-]', '', texto)
    texto = re.sub(r'\s+', ' ', texto).strip()
    return texto

def init_learn_state():
    if 'learn_activa' not in st.session_state: st.session_state['learn_activa'] = None
    if 'learn_opciones' not in st.session_state: st.session_state['learn_opciones'] = []
    if 'learn_estado_resp' not in st.session_state: st.session_state['learn_estado_resp'] = None
    if 'learn_respuesta_elegida' not in st.session_state: st.session_state['learn_respuesta_elegida'] = None
    if 'learn_modo_pregunta' not in st.session_state: st.session_state['learn_modo_pregunta'] = '4_opciones'
    if 'learn_target_write' not in st.session_state: st.session_state['learn_target_write'] = None
    if 'learn_start_time' not in st.session_state: st.session_state['learn_start_time'] = None
    if 'learn_last_activity' not in st.session_state: st.session_state['learn_last_activity'] = None
    if 'flashcards_data' not in st.session_state:
        st.session_state['flashcards_data'] = cargar_flashcards()

def cargar_nueva_tarjeta(flashcards, materia):
    pendientes = [f for f in flashcards if f['materia'] == materia and f['estado'] != 'Dominada']
    if not pendientes:
        st.session_state['learn_activa'] = None
        return False
        
    elegida = random.choice(pendientes)
    st.session_state['learn_activa'] = elegida
    
    racha = safe_int(elegida.get('racha_correctas', 0))
    
    if racha == 0:
        modo = '4_opciones'
        num_distractores = 3
    elif racha == 1:
        modo = '2_opciones'
        num_distractores = 1
    else:
        modo = 'escribir'
        num_distractores = 0
        
    st.session_state['learn_modo_pregunta'] = modo

    if num_distractores > 0:
        todas_materia = [f['definicion'] for f in flashcards if f['materia'] == materia and f['definicion'] != elegida['definicion']]
        todas_materia = list(set(todas_materia))
        
        if len(todas_materia) < num_distractores:
            otras = [f['definicion'] for f in flashcards if f['materia'] != materia and f['definicion'] != elegida['definicion']]
            otras = list(set(otras))
            faltan = num_distractores - len(todas_materia)
            todas_materia.extend(random.sample(otras, min(faltan, len(otras))))
            
        while len(todas_materia) < num_distractores:
            todas_materia.append(f"Respuesta incorrecta de relleno {len(todas_materia)}")

        distractores = random.sample(todas_materia, num_distractores)
        opciones = distractores + [elegida['definicion']]
        random.shuffle(opciones)
        st.session_state['learn_opciones'] = opciones
    else:
        st.session_state['learn_opciones'] = []
        
    st.session_state['learn_estado_resp'] = None
    st.session_state['learn_respuesta_elegida'] = None
    return True

def evaluar_respuesta(opcion_usuario):
    if st.session_state.get('learn_start_time') is None:
        st.session_state['learn_start_time'] = time.time()
    st.session_state['learn_last_activity'] = time.time()

    activa = st.session_state['learn_activa']
    modo = st.session_state['learn_modo_pregunta']
    target = st.session_state.get('learn_target_write', activa['definicion'])
    
    if modo == 'escribir':
        resp_norm = normalizar_texto(opcion_usuario)
        def_norm = normalizar_texto(target)
        es_correcta = (resp_norm == def_norm)
    else:
        es_correcta = (opcion_usuario == target)
    
    flashcards = st.session_state['flashcards_data']
    for f in flashcards:
        if str(f['id_tarjeta']) == str(activa['id_tarjeta']):
            if es_correcta:
                f['racha_correctas'] = safe_int(f.get('racha_correctas', 0)) + 1
                if f['racha_correctas'] >= 3:
                    f['estado'] = 'Dominada'
                else:
                    f['estado'] = 'Aprendiendo'
            else:
                f['racha_correctas'] = 0
                f['estado'] = 'Aprendiendo'
            break
            
    if es_correcta:
        st.toast("Correcto")
        st.session_state['learn_activa'] = None
        st.session_state['learn_estado_resp'] = None
        st.rerun()
    else:
        st.session_state['learn_estado_resp'] = "Incorrecta"
        st.session_state['learn_respuesta_elegida'] = opcion_usuario
        st.rerun()

def renderizar_modo_aprender():
    init_learn_state()
    
    if st.session_state.get('learn_start_time') is not None and st.session_state.get('learn_last_activity') is not None:
        inactividad = time.time() - st.session_state['learn_last_activity']
        if inactividad >= 300:
            tiempo_total = time.time() - st.session_state['learn_start_time'] - 300
            mins_reales = int(tiempo_total // 60)
            
            if mins_reales >= 1:
                st.session_state['historial'].append({
                    "FECHA": datetime.now().strftime("%d/%m/%Y"),
                    "MATERIA": st.session_state.get('learn_materia_filtro', 'Sin materia'), 
                    "MÉTODO": "Aprender (Flashcards)",
                    "TIEMPO (min)": mins_reales, 
                    "EFIC.": "100%", 
                    "INTERRUPCIONES": []
                })
                st.session_state['xp_total'] = st.session_state.get('xp_total', 0) + int(mins_reales * 10 * 1.2)
                guardar_datos(silencioso=True)
                guardar_todas_flashcards(st.session_state['flashcards_data'])
                st.warning(f"⚠️ Sesion cerrada por inactividad. Se guardaron {mins_reales} min reales descontando la pausa.")
            else:
                st.warning("⚠️ Sesion cerrada por inactividad. No se llego a 1 min de estudio.")
                
            st.session_state['learn_start_time'] = None
            st.session_state['learn_last_activity'] = None

    st.header("Modo Aprender")
    
    flashcards = st.session_state['flashcards_data']
    
    with st.expander("Crear nuevas tarjetas (Termino, Definicion e Imagen)"):
        with st.form("form_nueva_carta", clear_on_submit=True):
            materias_activas = [m['nombre'] for m in st.session_state.get('materias', [])]
            if not materias_activas:
                st.warning("⚠️ No tenes materias activas. Anda a Organizacion primero.")
            
            n_mat = st.selectbox("Materia", materias_activas if materias_activas else ["Sin materia"])
            n_term = st.text_input("Termino / Pregunta")
            n_def = st.text_area("Definicion / Respuesta")
            n_img = st.text_input("URL de la imagen (Opcional)", placeholder="https://ejemplo.com/imagen.png")
            
            if st.form_submit_button("Guardar Tarjeta"):
                if n_term and n_def:
                    nueva = {
                        "id_tarjeta": str(time.time()),
                        "materia": n_mat,
                        "termino": n_term.strip(),
                        "definicion": n_def.strip(),
                        "imagen": n_img.strip(),
                        "estado": "Nueva",
                        "racha_correctas": 0
                    }
                    st.session_state['flashcards_data'].append(nueva)
                    guardar_todas_flashcards(st.session_state['flashcards_data'])
                    st.success("Tarjeta guardada.")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("⚠️ Completa Termino y Definicion para guardar.")

    if not flashcards:
        st.info("No hay tarjetas todavia. Carga un par arriba para empezar.")
        return

    st.divider()

    materias_disponibles = list(set([f['materia'] for f in flashcards]))
    
    if 'learn_materia_filtro' not in st.session_state:
        st.session_state['learn_materia_filtro'] = materias_disponibles[0]
        
    materia_sel = st.selectbox(
        "Aprender por materia:", 
        materias_disponibles, 
        index=materias_disponibles.index(st.session_state['learn_materia_filtro']) if st.session_state['learn_materia_filtro'] in materias_disponibles else 0
    )
    
    if materia_sel != st.session_state['learn_materia_filtro']:
        st.session_state['learn_materia_filtro'] = materia_sel
        st.session_state['learn_activa'] = None
        st.session_state['learn_start_time'] = None 
        st.session_state['learn_last_activity'] = None
        st.rerun()

    cartas_materia = [f for f in flashcards if f['materia'] == materia_sel]
    
    dominadas = len([c for c in cartas_materia if c['estado'] == 'Dominada'])
    total = len(cartas_materia)
    progreso_pct = dominadas / total if total > 0 else 0
    
    mins_estudio = 0
    if st.session_state.get('learn_start_time'):
        mins_estudio = int((time.time() - st.session_state['learn_start_time']) // 60)

    c_prog, c_btn_time = st.columns([3, 1])
    with c_prog:
        st.progress(progreso_pct)
        st.caption(f"Progreso de {materia_sel}: {dominadas} / {total} conceptos dominados")
    with c_btn_time:
        if st.session_state.get('learn_start_time'):
            if st.button(f"Terminar y Guardar ({mins_estudio} min)", use_container_width=True):
                if mins_estudio >= 1:
                    st.session_state['historial'].append({
                        "FECHA": datetime.now().strftime("%d/%m/%Y"),
                        "MATERIA": materia_sel, 
                        "MÉTODO": "Aprender (Flashcards)",
                        "TIEMPO (min)": mins_estudio, 
                        "EFIC.": "100%", 
                        "INTERRUPCIONES": []
                    })
                    st.session_state['xp_total'] = st.session_state.get('xp_total', 0) + int(mins_estudio * 10 * 1.2)
                    guardar_datos(silencioso=True)
                    st.success(f"Se guardaron {mins_estudio} min en tu historial.")
                else:
                    st.warning("⚠️ Menos de 1 min. No se guardo en historial.")
                
                guardar_todas_flashcards(st.session_state['flashcards_data'])
                st.session_state['learn_start_time'] = None
                st.session_state['learn_last_activity'] = None
                time.sleep(1.5)
                st.rerun()
    
    st.markdown("<hr class='custom-hr'>", unsafe_allow_html=True)

    if dominadas == total and total > 0:
        st.success(f"Ya dominaste todos los conceptos de {materia_sel}.")
        if st.button("Reiniciar progreso de esta materia"):
            for f in flashcards:
                if f['materia'] == materia_sel:
                    f['estado'] = 'Nueva'
                    f['racha_correctas'] = 0
            guardar_todas_flashcards(st.session_state['flashcards_data'])
            st.session_state['learn_activa'] = None
            st.rerun()
        return

    if st.session_state['learn_activa'] is None:
        cargó_bien = cargar_nueva_tarjeta(flashcards, materia_sel)
        if not cargó_bien:
            st.rerun()

    activa = st.session_state['learn_activa']
    modo = st.session_state['learn_modo_pregunta']
    
    len_term = len(str(activa['termino']))
    len_def = len(str(activa['definicion']))
    
    if modo == 'escribir' and len_term < len_def:
        prompt_show = activa['definicion']
        target_write = activa['termino']
        label_show = "Definicion (Escribi el termino correspondiente)"
    else:
        prompt_show = activa['termino']
        target_write = activa['definicion']
        label_show = "Termino" if modo != 'escribir' else "Termino (Escribi la definicion)"
        
    st.session_state['learn_target_write'] = target_write

    url_img = str(activa.get('imagen', '')).strip()
    html_img = ""
    if url_img:
        # Si el link no es una foto real, te avisa en rojo en vez de desaparecer
        html_img = f"<img src='{url_img}' style='max-width: 100%; max-height: 250px; border-radius: 8px; margin-bottom: 20px; object-fit: contain;' onerror=\"this.outerHTML='<div style=\\'color:#ef4444; font-size:13px; margin-bottom:15px;\\'>⚠️ El link cargado no es de una imagen válida. Recordá hacer clic derecho -> Copiar dirección de la imagen.</div>'\"><br>"

    st.markdown(f"""
<div style='background-color: #153f59; padding: 40px; border-radius: 12px; text-align: center; margin-bottom: 20px; border: 2px solid #365b77;'>
<div style='color: #94b8d7; font-size: 12px; font-weight: bold; text-transform: uppercase; margin-bottom: 10px;'>{label_show}</div>
{html_img}
<div style='font-size: 28px; font-weight: bold; color: #f8fafc;'>{prompt_show}</div>
</div>
""", unsafe_allow_html=True)

    if st.session_state['learn_estado_resp'] is None:
        if modo == '4_opciones':
            st.caption("Fase 1/3: Selecciona la definicion correcta")
            opciones = st.session_state['learn_opciones']
            c1, c2 = st.columns(2)
            c3, c4 = st.columns(2)
            if c1.button(opciones[0], key="btn_opc_0", use_container_width=True): evaluar_respuesta(opciones[0])
            if c2.button(opciones[1], key="btn_opc_1", use_container_width=True): evaluar_respuesta(opciones[1])
            if c3.button(opciones[2], key="btn_opc_2", use_container_width=True): evaluar_respuesta(opciones[2])
            if c4.button(opciones[3], key="btn_opc_3", use_container_width=True): evaluar_respuesta(opciones[3])
            
        elif modo == '2_opciones':
            st.caption("Fase 2/3: Selecciona la correcta")
            opciones = st.session_state['learn_opciones']
            c1, c2 = st.columns(2)
            if c1.button(opciones[0], key="btn_opc_0", use_container_width=True): evaluar_respuesta(opciones[0])
            if c2.button(opciones[1], key="btn_opc_1", use_container_width=True): evaluar_respuesta(opciones[1])
            
        elif modo == 'escribir':
            st.caption("Fase 3/3: Escribi la respuesta")
            with st.form("form_escribir_resp", clear_on_submit=True):
                resp_usuario = st.text_input("Tu respuesta", placeholder="Escribi aca...")
                if st.form_submit_button("Responder", type="primary", use_container_width=True):
                    evaluar_respuesta(resp_usuario)
            
    else:
        st.markdown("<h3 style='color: #ef4444; text-align: center;'>Incorrecto</h3>", unsafe_allow_html=True)
        st.markdown(f"""
        <div style='background-color: rgba(239, 68, 68, 0.1); padding: 20px; border-radius: 8px; border: 1px solid #ef4444; margin-bottom: 20px;'>
            <p style='margin:0; color:#f8fafc;'><b>Elegiste / Escribiste:</b> {st.session_state['learn_respuesta_elegida']}</p>
            <hr style='border-color: #ef4444; opacity: 0.3;'>
            <p style='margin:0; color:#10b981;'><b>La correcta era:</b> {target_write}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Streamlit va a pausar acá para que leas y después avanza solo
        time.sleep(3.5)
        st.session_state['learn_activa'] = None
        st.session_state['learn_estado_resp'] = None
        st.rerun()
