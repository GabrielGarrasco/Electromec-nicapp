
import streamlit as st
import random
import time
from db import cargar_flashcards, guardar_todas_flashcards

def init_learn_state():
    if 'learn_activa' not in st.session_state:
        st.session_state['learn_activa'] = None
    if 'learn_opciones' not in st.session_state:
        st.session_state['learn_opciones'] = []
    if 'learn_estado_resp' not in st.session_state:
        st.session_state['learn_estado_resp'] = None
    if 'learn_respuesta_elegida' not in st.session_state:
        st.session_state['learn_respuesta_elegida'] = None

def cargar_nueva_tarjeta(flashcards, materia):
    # Filtramos las cartas que todavía no están dominadas
    pendientes = [f for f in flashcards if f['materia'] == materia and f['estado'] != 'Dominada']
    if not pendientes:
        st.session_state['learn_activa'] = None
        return False
        
    # Elegimos una al azar
    elegida = random.choice(pendientes)
    st.session_state['learn_activa'] = elegida
    
    # Buscamos distractores (respuestas falsas) de la MISMA materia
    todas_materia = [f['definicion'] for f in flashcards if f['materia'] == materia and f['definicion'] != elegida['definicion']]
    todas_materia = list(set(todas_materia)) # Sacamos duplicados por las dudas
    
    # Salvavidas: si hay menos de 3 respuestas falsas en esta materia, rellenamos con otras para no romper la app
    if len(todas_materia) < 3:
        otras = [f['definicion'] for f in flashcards if f['materia'] != materia and f['definicion'] != elegida['definicion']]
        otras = list(set(otras))
        faltan = 3 - len(todas_materia)
        todas_materia.extend(random.sample(otras, min(faltan, len(otras))))
        
    # Si tu base de datos entera está casi vacía y no llegamos a 3 distractores, metemos texto de relleno
    while len(todas_materia) < 3:
        todas_materia.append(f"Respuesta incorrecta de relleno {len(todas_materia)}")

    distractores = random.sample(todas_materia, 3)
    opciones = distractores + [elegida['definicion']]
    random.shuffle(opciones)
    
    st.session_state['learn_opciones'] = opciones
    st.session_state['learn_estado_resp'] = None
    st.session_state['learn_respuesta_elegida'] = None
    return True

def evaluar_respuesta(opcion, flashcards):
    activa = st.session_state['learn_activa']
    es_correcta = (opcion == activa['definicion'])
    
    st.session_state['learn_estado_resp'] = "Correcta" if es_correcta else "Incorrecta"
    st.session_state['learn_respuesta_elegida'] = opcion
    
    # Actualizamos el estado en la base de datos
    for f in flashcards:
        if str(f['id_tarjeta']) == str(activa['id_tarjeta']):
            if es_correcta:
                f['racha_correctas'] = int(f.get('racha_correctas', 0)) + 1
                # Si la pega 2 veces seguidas, la dominó
                if f['racha_correctas'] >= 2:
                    f['estado'] = 'Dominada'
                else:
                    f['estado'] = 'Aprendiendo'
            else:
                f['racha_correctas'] = 0 # Castigo: vuelve a cero si le pifia
                f['estado'] = 'Aprendiendo'
            break
            
    guardar_todas_flashcards(flashcards)


def renderizar_modo_aprender():
    init_learn_state()
    st.header("Modo Aprender")
    
    flashcards = cargar_flashcards()
    
    # --- SECCIÓN: AGREGAR TARJETAS ---
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

    # --- SECCIÓN: FILTRO Y PROGRESO ---
    materias_disponibles = list(set([f['materia'] for f in flashcards]))
    
    # Guardamos la materia seleccionada en el estado para que no se resetee al jugar
    if 'learn_materia_filtro' not in st.session_state:
        st.session_state['learn_materia_filtro'] = materias_disponibles[0]
        
    materia_sel = st.selectbox(
        "Aprender por materia:", 
        materias_disponibles, 
        index=materias_disponibles.index(st.session_state['learn_materia_filtro']) if st.session_state['learn_materia_filtro'] in materias_disponibles else 0
    )
    
    # Si el usuario cambia de materia en el selectbox, reseteamos la carta actual
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

    # --- LÓGICA DEL JUEGO (MÚLTIPLE CHOICE) ---
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

    # Si no hay carta activa, cargamos una
    if st.session_state['learn_activa'] is None:
        cargó_bien = cargar_nueva_tarjeta(flashcards, materia_sel)
        if not cargó_bien:
            st.rerun()

    activa = st.session_state['learn_activa']
    
    # Mostramos la pregunta gigante al estilo Quizlet
    st.markdown(f"""
    <div style='background-color: #153f59; padding: 40px; border-radius: 12px; text-align: center; margin-bottom: 30px; border: 2px solid #365b77;'>
        <div style='color: #94b8d7; font-size: 12px; font-weight: bold; text-transform: uppercase; margin-bottom: 10px;'>Término</div>
        <div style='font-size: 28px; font-weight: bold; color: #f8fafc;'>{activa['termino']}</div>
    </div>
    """, unsafe_allow_html=True)

    # Panel de opciones o resultado
    if st.session_state['learn_estado_resp'] is None:
        st.caption("Seleccioná la definición correcta:")
        opciones = st.session_state['learn_opciones']
        
        c1, c2 = st.columns(2)
        c3, c4 = st.columns(2)
        
        if c1.button(opciones[0], key="btn_opc_0", use_container_width=True):
            evaluar_respuesta(opciones[0], flashcards)
            st.rerun()
        if c2.button(opciones[1], key="btn_opc_1", use_container_width=True):
            evaluar_respuesta(opciones[1], flashcards)
            st.rerun()
        if c3.button(opciones[2], key="btn_opc_2", use_container_width=True):
            evaluar_respuesta(opciones[2], flashcards)
            st.rerun()
        if c4.button(opciones[3], key="btn_opc_3", use_container_width=True):
            evaluar_respuesta(opciones[3], flashcards)
            st.rerun()
            
    else:
        # Mostramos si le pegó o le erró
        es_correcta = st.session_state['learn_estado_resp'] == "Correcta"
        color_msj = "#10b981" if es_correcta else "#ef4444"
        msj = "¡Correcto!" if es_correcta else "¡Incorrecto!"
        
        st.markdown(f"<h3 style='color: {color_msj}; text-align: center;'>{msj}</h3>", unsafe_allow_html=True)
        
        if not es_correcta:
            st.markdown(f"""
            <div style='background-color: rgba(239, 68, 68, 0.1); padding: 20px; border-radius: 8px; border: 1px solid #ef4444; margin-bottom: 20px;'>
                <p style='margin:0; color:#f8fafc;'><b>Elegiste:</b> {st.session_state['learn_respuesta_elegida']}</p>
                <hr style='border-color: #ef4444; opacity: 0.3;'>
                <p style='margin:0; color:#10b981;'><b>La correcta era:</b> {activa['definicion']}</p>
            </div>
            """, unsafe_allow_html=True)
            
        c_space1, c_btn, c_space2 = st.columns([1, 2, 1])
        if c_btn.button("Continuar", type="primary", use_container_width=True):
            st.session_state['learn_activa'] = None
            st.rerun()
            
