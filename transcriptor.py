import streamlit as st
import os
from PIL import Image
from google import genai
from google.genai import types

def renderizar_transcriptor():
    st.header("Digitalizar Apuntes")

    # Conectar con la API Key guardada en los Secrets de Streamlit
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
        client = genai.Client(api_key=api_key)
    except Exception as e:
        st.error("⚠️ No se encontró la API Key. Revisá los Secrets en Streamlit Cloud.")
        return
        
    # Diccionario de abreviaturas (memoria temporal de la sesión)
    if 'dicc_abreviaturas' not in st.session_state:
        st.session_state['dicc_abreviaturas'] = "Ej: q = que, cto = circuito, tmb = también"

    with st.expander("Mis Abreviaturas (Configuración)"):
        st.info("Anotá acá tus abreviaturas para que la IA sepa cómo leerlas. Se lo va a memorizar para esta sesión.")
        st.session_state['dicc_abreviaturas'] = st.text_area("Diccionario", st.session_state['dicc_abreviaturas'], label_visibility="collapsed")

    # Subir múltiples archivos
    archivos_subidos = st.file_uploader("Subí las fotos de tus apuntes acá", type=["png", "jpg", "jpeg"], accept_multiple_files=True)

    if archivos_subidos:
        st.subheader("Ordená tus páginas")
        
        # Mostramos las imágenes y dejamos que les asigne un número de orden
        cols = st.columns(len(archivos_subidos))
        imagenes_ordenadas = []
        
        for i, archivo in enumerate(archivos_subidos):
            img = Image.open(archivo)
            with cols[i]:
                st.image(img, use_container_width=True)
                # Input para ordenar cada foto
                orden = st.number_input("Página", min_value=1, value=i+1, key=f"orden_{archivo.name}")
                imagenes_ordenadas.append({"orden": orden, "img": img})

        # Ordenamos la lista de imágenes según los números que pusiste
        imagenes_ordenadas.sort(key=lambda x: x["orden"])
        imagenes_pil_final = [item["img"] for item in imagenes_ordenadas]

        st.divider()

        if st.button("🧠 Procesar y Transcribir Todo", type="primary", use_container_width=True):
            with st.spinner("La IA está leyendo tu letra... Bancá un toque."):
                try:
                    # El prompt maestro con tus abreviaturas inyectadas
                    prompt_maestro = f"""
                    Actúa como un transcriptor universitario experto. Voy a pasarte fotos de mis apuntes. 
                    Tu objetivo es transcribir TODO el texto manteniendo estrictamente la estructura original.
                    
                    REGLAS OBLIGATORIAS:
                    1. ESTRUCTURA: Respeta los títulos, subtítulos, listas con viñetas y sangrías.
                    2. MATEMÁTICA Y CONJUNTOS: Toda fórmula matemática, letras griegas y teoría de conjuntos DEBE estar escrita en formato LaTeX delimitado por $ o $$.
                    3. POST-ITS: Si ves notas escritas en papeles amarillos (post-its) o recuadros aislados, transcríbelos y ponles el prefijo "[NOTA AL MARGEN]: ".
                    4. ABREVIATURAS: Conoces mis abreviaturas habituales, úsalas para reemplazar el texto directamente sin preguntar: {st.session_state['dicc_abreviaturas']}
                    5. DIRECTO AL GRANO: Devuélveme SOLO la transcripción, sin saludos ni introducciones.
                    """

                    # Le mandamos el texto + todas las imágenes ordenadas
                    contenido_a_enviar = [prompt_maestro] + imagenes_pil_final
                    
                    # Llamada a la versión nueva que te pide el error
                    response = client.models.generate_content(
                        model='gemini-3.6-flash',
                        contents=contenido_a_enviar,
                        config=types.GenerateContentConfig(
                            temperature=0.2,
                        )
                    )

                    st.success("¡Transcripción completada!")
                    
                    # Mostramos el resultado
                    st.markdown("### Resultado:")
                    st.container(border=True).markdown(response.text)

                    # Guardamos por si a futuro agregás los botones de exportar a Word/PDF
                    st.session_state['ultima_transcripcion'] = response.text

                except Exception as e:
                    st.error(f"Hubo un error al procesar las imágenes: {e}")
