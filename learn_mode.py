import streamlit as st
import random
import time
import unicodedata
import re
from db import cargar_flashcards, guardar_todas_flashcards

def normalizar_texto(texto):
    if not texto: return ""
    # Normaliza a NFD para remover tildes y acentos
    texto = unicodedata.normalize('NFD', str(texto)).encode('ascii', 'ignore').decode('utf-8')
    texto = texto.lower()
    # Removemos puntuación típica para que no te rebote por un punto o coma
    texto = re.sub(r'[.,;¿?¡!()"\'\-]', '', texto)
    # Limpiamos los espacios extra
    texto = re.sub(r'\s+', ' ', texto).strip()
    return texto

def init_learn_state():
    if 'learn_activa' not in st.session_state:
        st.session_state['learn_activa'] = None
    if 'learn_opciones' not in st.session_state:
        st.session_state['learn_opciones'] = []
    if 'learn_estado_resp' not in st.session_state:
        st.session_state['learn_estado_resp'] = None
    if 'learn_respuesta_elegida' not in st.session_state:
        st.session_state['learn_respuesta_elegida'] = None
    if 'learn_modo_pregunta' not in st.session_state:
        st.session_state['learn_modo_pregunta'] = '4_opciones'

def cargar_nueva_tarjeta(flashcards, materia):
    pendientes = [f for f in flashcards if f['materia'] == materia and f['estado'] != 'Dominada']
    if not pendientes:
        st.session_state['learn_activa'] = None
        return False
        
    elegida = random.choice(pendientes)
    st.session_state['learn_activa'] = elegida
    racha = int(elegida.get('racha_correctas', 0))
    
    # Curva de dificultad en 3 Fases
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

def evaluar_respuesta(opcion_usuario, flashcards):
    activa = st.session_state['learn_activa']
    modo = st.session_state['learn_modo_pregunta']
    
    if modo == 'escribir':
        # Pasamos las dos respuestas por el filtro flexible antes de comparar
        resp_norm = normalizar_texto(opcion_usuario)
        def_norm = normalizar_texto(activa['definicion'])
        es_correcta = (resp_norm == def_norm)
    else:
        es_correcta = (opcion_usuario == activa['definicion'])
    
    st.session_state['learn_estado_resp'] = "Correcta" if es_correcta else "Incorrecta"
    st.session_state['learn_respuesta_elegida'] = opcion_usuario
    
    for f in flashcards:
        if str(f['id_tarjeta']) == str(activa['id_tarjeta']):
            if es_correcta:
                f['racha_correctas'] = int(f.get('racha_correctas', 0)) + 1
                # A las 3 correctas seguidas pasa a dominada definitivamente
                if f['racha_correctas'] >= 3:
                    f['estado'] = 'Dominada'
                else:
                    f['estado'] = 'Aprendiendo'
            else:
                f['racha_correctas'] = 0
                f['estado'] = 'Aprendiendo'
            break
            
    guardar_todas_flashcards(flashcards)

def renderizar_modo_aprender():
    init_learn_state()
    st.header("Modo Aprender 🧠")
    
    flashcards = cargar_flashcards()
    
    with st.expander("Crear nuevas tarjetas (Término y Definición)"):
        with st.form("form_nueva_carta"):
            materias_activas = [m['nombre'] for m in st.session_state.get('materias', [])]
            if not materias_activas:
                st.warning("No tenés materias activas. Anda a 'Organización' primero.")
            
            n_mat = st.selectbox("Materia", materias_activas if materias_activas else ["Sin materia"])
            n_term = st.text_input("Término / Pregunta")
            n_def = st.text_area("Definición / Respuesta")
            
            if st.form_submit_button("Guardar Tarjeta"):
                if n_term and n_def:
                    nueva = {
                        "id_tarjeta": str(time.time()),
                        "materia": n_mat,
                        "termino": n_term.strip(),
                        "definicion": n_def.strip(),
                        "estado": "Nueva",
                        "racha_correctas": 0
                    }
                    flashcards.append(nueva)
                    guardar_todas_flashcards(flashcards)
                    st.success("¡Tarjeta agregada a la base de datos!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Completá ambos campos para guardar.")

    if not flashcards:
        st.info("No hay tarjetas todavía. ¡Cargá un par arriba para empezar!")
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
        st.rerun()

    cartas_materia = [f for f in flashcards if f['materia'] == materia_sel]
    
    dominadas = len([c for c in cartas_materia if c['estado'] == 'Dominada'])
    total = len(cartas_materia)
    progreso_pct = dominadas / total if total > 0 else 0
    
    st.progress(progreso_pct)
    st.caption(f"Progreso de {materia_sel}: {dominadas} / {total} conceptos dominados")
    
    st.markdown("<hr class='custom-hr'>", unsafe_allow_html=True)

    if dominadas == total and total > 0:
        st.success(f"¡Felicitaciones! Ya dominaste todos los conceptos de {materia_sel}.")
        if st.button("Reiniciar progreso de esta materia"):
            for f in flashcards:
                if f['materia'] == materia_sel:
                    f['estado'] = 'Nueva'
                    f['racha_correctas'] = 0
            guardar_todas_flashcards(flashcards)
            st.session_state['learn_activa'] = None
            st.rerun()
        return

    if st.session_state['learn_activa'] is None:
        cargó_bien = cargar_nueva_tarjeta(flashcards, materia_sel)
        if not cargó_bien:
            st.rerun()

    activa = st.session_state['learn_activa']
    modo = st.session_state['learn_modo_pregunta']
    
    st.markdown(f"""
    <div style='background-color: #153f59; padding: 40px; border-radius: 12px; text-align: center; margin-bottom: 30px; border: 2px solid #365b77;'>
        <div style='color: #94b8d7; font-size: 12px; font-weight: bold; text-transform: uppercase; margin-bottom: 10px;'>Término</div>
        <div style='font-size: 28px; font-weight: bold; color: #f8fafc;'>{activa['termino']}</div>
    </div>
    """, unsafe_allow_html=True)

    if st.session_state['learn_estado_resp'] is None:
        if modo == '4_opciones':
            st.caption("Fase 1/3: Seleccioná la definición correcta")
            opciones = st.session_state['learn_opciones']
            c1, c2 = st.columns(2)
            c3, c4 = st.columns(2)
            if c1.button(opciones[0], key="btn_opc_0", use_container_width=True): evaluar_respuesta(opciones[0], flashcards); st.rerun()
            if c2.button(opciones[1], key="btn_opc_1", use_container_width=True): evaluar_respuesta(opciones[1], flashcards); st.rerun()
            if c3.button(opciones[2], key="btn_opc_2", use_container_width=True): evaluar_respuesta(opciones[2], flashcards); st.rerun()
            if c4.button(opciones[3], key="btn_opc_3", use_container_width=True): evaluar_respuesta(opciones[3], flashcards); st.rerun()
            
        elif modo == '2_opciones':
            st.caption("Fase 2/3: Ya casi. Seleccioná la correcta")
            opciones = st.session_state['learn_opciones']
            c1, c2 = st.columns(2)
            if c1.button(opciones[0], key="btn_opc_0", use_container_width=True): evaluar_respuesta(opciones[0], flashcards); st.rerun()
            if c2.button(opciones[1], key="btn_opc_1", use_container_width=True): evaluar_respuesta(opciones[1], flashcards); st.rerun()
            
        elif modo == 'escribir':
            st.caption("Fase 3/3: Escribí la definición (no importa mayúsculas ni tildes)")
            with st.form("form_escribir_resp"):
                resp_usuario = st.text_input("Tu respuesta", placeholder="Escribí acá...")
                if st.form_submit_button("Responder", type="primary", use_container_width=True):
                    evaluar_respuesta(resp_usuario, flashcards)
                    st.rerun()
            
    else:
        es_correcta = st.session_state['learn_estado_resp'] == "Correcta"
        color_msj = "#10b981" if es_correcta else "#ef4444"
        msj = "¡Correcto!" if es_correcta else "¡Incorrecto!"
        
        st.markdown(f"<h3 style='color: {color_msj}; text-align: center;'>{msj}</h3>", unsafe_allow_html=True)
        
        if not es_correcta:
            st.markdown(f"""
            <div style='background-color: rgba(239, 68, 68, 0.1); padding: 20px; border-radius: 8px; border: 1px solid #ef4444; margin-bottom: 20px;'>
                <p style='margin:0; color:#f8fafc;'><b>Elegiste / Escribiste:</b> {st.session_state['learn_respuesta_elegida']}</p>
                <hr style='border-color: #ef4444; opacity: 0.3;'>
                <p style='margin:0; color:#10b981;'><b>La correcta era:</b> {activa['definicion']}</p>
            </div>
            """, unsafe_allow_html=True)
            
        c_space1, c_btn, c_space2 = st.columns([1, 2, 1])
        if c_btn.button("Continuar", type="primary", use_container_width=True):
            st.session_state['learn_activa'] = None
            st.rerun()
