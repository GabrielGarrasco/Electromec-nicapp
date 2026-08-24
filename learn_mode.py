import streamlit as st
import random
import time
from db import cargar_flashcards, guardar_todas_flashcards

def renderizar_modo_aprender():
    st.header("Modo Aprender")
    
    flashcards = cargar_flashcards()
    
    # --- SECCIÓN: AGREGAR TARJETAS ---
    with st.expander("Agregar nuevas flashcards"):
        with st.form("form_nueva_carta"):
            # Traemos las materias activas para no tipear a mano
            materias_activas = [m['nombre'] for m in st.session_state.get('materias', [])]
            if not materias_activas:
                st.warning("Agregá materias en 'Organización' primero.")
            
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
                    st.success("¡Tarjeta agregada!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Completá Término y Definición para guardar.")

    if not flashcards:
        st.info("No hay tarjetas todavía. ¡Cargá un par arriba para empezar a estudiar!")
        return

    # --- SECCIÓN: CONFIGURACIÓN DEL JUEGO ---
    st.divider()
    materias_disponibles = list(set([f['materia'] for f in flashcards]))
    materia_sel = st.selectbox("Elegí la materia para estudiar", materias_disponibles)
    
    cartas_materia = [f for f in flashcards if f['materia'] == materia_sel]
    
    if not cartas_materia:
        st.warning("No tenés flashcards guardadas para esta materia.")
        return

    # Lógica de progreso (Barra estilo Quizlet)
    dominadas = len([c for c in cartas_materia if c['estado'] == 'Dominada'])
    total = len(cartas_materia)
    progreso_pct = dominadas / total if total > 0 else 0
    
    st.progress(progreso_pct)
    st.caption(f"Progreso: {dominadas} / {total} conceptos dominados")
    
    # --- ACÁ ABAJO VA A IR LA LÓGICA DEL MULTIPLE CHOICE ---
