import streamlit as st
import random
from db import cargar_flashcards, guardar_todas_flashcards

def renderizar_modo_aprender():
    st.header("Modo Aprender")
    
    flashcards = cargar_flashcards()
    if not flashcards:
        st.info("No hay tarjetas todavía. ¡Agregá algunas para empezar!")
        # Acá a futuro podés sumar un form para agregar tarjetas
        return

    materias_disponibles = list(set([f['materia'] for f in flashcards]))
    materia_sel = st.selectbox("Elegí la materia", materias_disponibles)
    
    # Filtramos las cartas
    cartas_materia = [f for f in flashcards if f['materia'] == materia_sel]
    
    if not cartas_materia:
        st.warning("No hay flashcards para esta materia.")
        return

    # Lógica de progreso
    dominadas = len([c for c in cartas_materia if c['estado'] == 'Dominada'])
    total = len(cartas_materia)
    st.progress(dominadas / total if total > 0 else 0)
    st.caption(f"Progreso: {dominadas} / {total} dominadas")
    
    st.divider()
    
    # --- ACÁ VA A IR LA LÓGICA DEL JUEGO ---
    st.write("Acá vamos a renderizar la pregunta y los botones...")
