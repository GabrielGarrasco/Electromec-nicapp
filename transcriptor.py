import streamlit as st
import os
from PIL import Image
from google import genai
from google.genai import types

def renderizar_transcriptor():
    st.header("🤖 Transcriptor de Apuntes con IA")
    st.markdown("Subí las fotos de tus apuntes. La IA va a identificar títulos, viñetas, fórmulas matemáticas, letras griegas y hasta los comentarios en post-its amarillos.")

    # Conectar con la API Key guardada en los Secrets de Streamlit
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
        client = genai.Client(api_key=api_key)
    except Exception as e:
        st.error("⚠️ No se encontró la API Key. Revisá los Secrets en Streamlit Cloud.")
        return

    # Subir múltiples archivos
    archivos_subidos = st.file_uploader("Subí las fotos de tus apuntes acá", type=["png", "jpg", "jpeg"], accept_multiple_files=True)

    if archivos_subidos:
        st.subheader("Imágenes cargadas")
        
        # Mostramos las imágenes para que veas que se cargaron bien (el orden de subida)
        cols = st.columns(len(archivos_subidos))
        imagenes_pil = []
        
        for i, archivo in enumerate(archivos_subidos):
            img = Image.open(archivo)
            imagenes_pil.append(img)
            with cols[i]:
                st.image(img, caption=f"Pág {i+1}", use_container_width=True)

        st.divider()

        if st.button("🧠 Procesar y Transcribir Todo", type="primary", use_container_width=True):
            with st.spinner("La IA está leyendo tu letra de médico... Bancá un toque."):
                try:
                    # El prompt maestro (lo que le ordenamos a la IA que haga)
                    prompt_maestro = """
                    Actúa como un transcriptor universitario experto. Voy a pasarte fotos de mis apuntes. 
                    Tu objetivo es transcribir TODO el texto manteniendo estrictamente la estructura original.
                    
                    REGLAS OBLIGATORIAS:
                    1. ESTRUCTURA: Respeta los títulos, subtítulos, listas con viñetas y sangrías.
                    2. MATEMÁTICA Y CONJUNTOS: Toda fórmula matemática, letras griegas (alfa, beta, omega, etc.) y teoría de conjuntos (unión, intersección, vacío, subconjuntos) DEBE estar escrita en formato LaTeX delimitado por $ o $$.
                    3. POST-ITS: Si ves notas escritas en papeles amarillos (post-its) o recuadros aislados, transcríbelos y ponles el prefijo "[NOTA AL MARGEN]: ".
                    4. ABREVIATURAS: Intenta deducir mis abreviaturas por contexto.
                    5. DIRECTO AL GRANO: Devuélveme SOLO la transcripción, sin saludos ni introducciones.
                    """

                    # Le mandamos el texto + todas las imágenes juntas
                    contenido_a_enviar = [prompt_maestro] + imagenes_pil
                    
                    # Llamada a Gemini 2.5 Flash (ideal para visión y rapidez)
                    response = client.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=contenido_a_enviar,
                        config=types.GenerateContentConfig(
                            temperature=0.2, # Temperatura baja para que no invente cosas
                        )
                    )

                    st.success("¡Transcripción completada!")
                    
                    # Mostramos el resultado en pantalla
                    st.markdown("### Resultado:")
                    st.container(border=True).markdown(response.text)

                    # Guardamos el resultado en la sesión temporal por si lo queremos procesar después
                    st.session_state['ultima_transcripcion'] = response.text

                except Exception as e:
                    st.error(f"Hubo un error al procesar las imágenes: {e}")
