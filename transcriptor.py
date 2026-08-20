import streamlit as st
import os
from PIL import Image
from google import genai
from google.genai import types

def renderizar_transcriptor():
    st.header("Digitalizar Apuntes")

    # Conectar con la API Key guardada en los Secrets
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
        client = genai.Client(api_key=api_key)
    except Exception as e:
        st.error("⚠️ No se encontró la API Key. Revisá los Secrets en Streamlit Cloud.")
        return
        
    if 'dicc_abreviaturas' not in st.session_state:
        st.session_state['dicc_abreviaturas'] = "Ej: q = que, cto = circuito, tmb = también"

    # Diccionario manual opcional
    with st.expander("Mis Abreviaturas (Opcional)"):
        st.info("Anotá acá tus abreviaturas si querés forzar a la IA a que las lea de una manera específica.")
        st.session_state['dicc_abreviaturas'] = st.text_area("Diccionario", st.session_state['dicc_abreviaturas'], height=100, label_visibility="collapsed")

    # Subir archivos
    archivos_subidos = st.file_uploader("Subí las fotos de tus apuntes acá", type=["png", "jpg", "jpeg"], accept_multiple_files=True)

    if archivos_subidos:
        st.subheader("Ordená tus páginas")
        
        cols = st.columns(len(archivos_subidos))
        imagenes_ordenadas = []
        
        for i, archivo in enumerate(archivos_subidos):
            img = Image.open(archivo)
            with cols[i]:
                st.image(img, use_container_width=True)
                orden = st.number_input("Página", min_value=1, value=i+1, key=f"orden_{archivo.name}")
                imagenes_ordenadas.append({"orden": orden, "img": img})

        imagenes_ordenadas.sort(key=lambda x: x["orden"])
        imagenes_pil_final = [item["img"] for item in imagenes_ordenadas]

        st.divider()

        # Botón único de proceso
        if st.button("🧠 Procesar y Transcribir Todo", type="primary", use_container_width=True):
            with st.spinner("Escaneando documentos..."):
                try:
                    prompt_maestro = f"""
                    Actúa como un transcriptor universitario experto. Transcribe TODO el texto de estas imágenes manteniendo la estructura original.
                    
                    REGLAS ESTRICTAS:
                    1. ESTRUCTURA: Respeta los títulos, subtítulos, listas y sangrías. Todo debe estar formateado estrictamente en Markdown.
                    2. SÍMBOLOS: Usa caracteres normales para flechas (→) y grados (°). ESTÁ TOTALMENTE PROHIBIDO usar LaTeX (como $\\rightarrow$) para texto normal. Reserva el formato LaTeX EXCLUSIVAMENTE para ecuaciones matemáticas complejas.
                    3. ESQUEMAS/CUADROS: Transcribe su contenido de forma lógica y estructurada. ESTÁ PROHIBIDO dejar marcas indicando que falta una imagen o esquema.
                    4. NOTAS: Si hay post-its o notas al margen, transcríbelas agregando "[NOTA]: " al inicio.
                    5. ABREVIATURAS: Usa este diccionario provisto para reemplazar las abreviaturas: {st.session_state['dicc_abreviaturas']}.
                    6. Devuelve la transcripción directa en texto crudo Markdown.
                    7. IMPORTANTE - NOMBRE DE ARCHIVO: Al final de toda la transcripción, en una nueva y última línea, escribe obligatoriamente el nombre del archivo siguiendo este formato exacto:
                    NOMBRE_ARCHIVO: Unidad/tema xx - Materia - Fecha.md
                    (Extrae el número/nombre de unidad o tema, la materia y la fecha del texto que acabas de transcribir. Dale prioridad al título de la Unidad o Tema que aparezca primero).
                    """

                    response = client.models.generate_content(
                        model='gemini-3.6-flash',
                        contents=[prompt_maestro] + imagenes_pil_final,
                        config=types.GenerateContentConfig(
                            temperature=0.2,
                        )
                    )

                    texto_completo = response.text
                    nombre_archivo = "Apuntes_Digitalizados.md"
                    texto_limpio = texto_completo
                    
                    # Separamos el nombre del archivo del resto del texto
                    if "NOMBRE_ARCHIVO:" in texto_completo:
                        partes = texto_completo.split("NOMBRE_ARCHIVO:")
                        texto_limpio = partes[0].strip()
                        nombre_archivo = partes[1].strip()
                        # Por las dudas que la IA se olvide la extensión
                        if not nombre_archivo.endswith(".md"):
                            nombre_archivo += ".md"

                    st.session_state['ultima_transcripcion'] = texto_limpio
                    st.session_state['ultimo_nombre_archivo'] = nombre_archivo

                except Exception as e:
                    st.error(f"Hubo un error al procesar las imágenes: {e}")

        # Mostrar y Exportar
        if 'ultima_transcripcion' in st.session_state:
            st.success("¡Transcripción completada!")
            st.markdown("### Resultado:")
            st.container(border=True).markdown(st.session_state['ultima_transcripcion'])

            st.divider()
            st.subheader("📥 Exportar a Notion")
            
            c_down1, c_down2 = st.columns(2)
            with c_down1:
                st.download_button(
                    label="Descargar .md (Para Notion)", 
                    data=st.session_state['ultima_transcripcion'], 
                    file_name=st.session_state.get('ultimo_nombre_archivo', 'Apuntes_Digitalizados.md'), 
                    mime="text/markdown", 
                    use_container_width=True
                )
            with c_down2:
                st.info("💡 Arrastrá el archivo .md adentro de una página vacía de Notion, o andá a 'Importar' en Notion y elegí 'Text & Markdown'. Se renderiza todo solo.")
