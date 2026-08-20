import streamlit as st
import os
import io
from PIL import Image
from google import genai
from google.genai import types
from docx import Document
from docx.shared import Inches

def generar_docx(texto, imagenes):
    doc = Document()
    doc.add_heading("Apuntes Digitalizados", 0)
    
    # Añadimos la transcripción
    doc.add_paragraph(texto)
    
    # Añadimos las imágenes ordenadas al final del documento
    if imagenes:
        doc.add_page_break()
        doc.add_heading("Imágenes de Referencia", 1)
        for img_dict in imagenes:
            img = img_dict['img']
            # Convertimos la imagen de PIL a bytes para que Word la entienda
            img_byte_arr = io.BytesIO()
            # Convertimos a RGB por si hay PNGs con transparencia que rompen el DOCX
            if img.mode in ("RGBA", "P"): 
                img = img.convert("RGB")
            img.save(img_byte_arr, format='JPEG')
            img_byte_arr.seek(0)
            doc.add_picture(img_byte_arr, width=Inches(6.0))
            doc.add_paragraph(f"Página {img_dict['orden']}")
    
    bio = io.BytesIO()
    doc.save(bio)
    return bio.getvalue()

def renderizar_transcriptor():
    st.header("Digitalizar Apuntes")

    # Conectar con la API Key guardada en los Secrets de Streamlit
    try:
        api_key = st.secrets["GEMINI_API_KEY"]
        client = genai.Client(api_key=api_key)
    except Exception as e:
        st.error("⚠️ No se encontró la API Key. Revisá los Secrets en Streamlit Cloud.")
        return
        
    if 'dicc_abreviaturas' not in st.session_state:
        st.session_state['dicc_abreviaturas'] = ""

    # Subir múltiples archivos
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

        # PASO 1: Detectar abreviaturas automáticamente
        if st.button("🔍 Escanear Abreviaturas", use_container_width=True):
            with st.spinner("Buscando abreviaturas en los documentos..."):
                try:
                    prompt_abrev = "Lee estas imágenes y haz una lista de todas las abreviaturas o símbolos no estándar que encuentres con su probable significado. Usa un formato estricto: abreviatura = significado. No agregues texto extra ni explicaciones."
                    response_abrev = client.models.generate_content(
                        model='gemini-3.6-flash',
                        contents=[prompt_abrev] + imagenes_pil_final
                    )
                    st.session_state['dicc_abreviaturas'] = response_abrev.text
                    st.rerun()
                except Exception as e:
                    st.error(f"Error al buscar abreviaturas: {e}")

        with st.expander("Mis Abreviaturas (Configuración)", expanded=True):
            st.info("Revisá y modificá lo que encontró la IA antes de transcribir todo el texto.")
            st.session_state['dicc_abreviaturas'] = st.text_area("Diccionario", st.session_state['dicc_abreviaturas'], height=150, label_visibility="collapsed")

        # PASO 2: Transcripción Final
        if st.button("🧠 Procesar y Transcribir Todo", type="primary", use_container_width=True):
            with st.spinner("Escaneando documentos..."):
                try:
                    prompt_maestro = f"""
                    Actúa como un transcriptor universitario experto. Voy a pasarte fotos de mis apuntes. 
                    Tu objetivo es transcribir TODO el texto manteniendo estrictamente la estructura original.
                    
                    REGLAS OBLIGATORIAS:
                    1. ESTRUCTURA: Respeta los títulos, subtítulos, listas con viñetas y sangrías. Reproduce cuadros o tablas usando formato Markdown.
                    2. MATEMÁTICA Y CONJUNTOS: Toda fórmula matemática, letras griegas y teoría de conjuntos DEBE estar escrita en formato LaTeX delimitado por $ o $$.
                    3. POST-ITS y ESQUEMAS: Si ves notas escritas en papeles amarillos al margen, transcríbelos con el prefijo "[NOTA AL MARGEN]: ". Si detectas un diagrama, dibujo o mapa mental que no se pueda escribir con texto, indica explícitamente "[ACÁ VA IMAGEN DEL ESQUEMA]".
                    4. ABREVIATURAS: Usa este diccionario provisto para reemplazar las abreviaturas directamente por su palabra completa en el texto final: {st.session_state['dicc_abreviaturas']}
                    5. DIRECTO AL GRANO: Devuélveme SOLO la transcripción, sin saludos ni introducciones.
                    """

                    response = client.models.generate_content(
                        model='gemini-3.6-flash',
                        contents=[prompt_maestro] + imagenes_pil_final,
                        config=types.GenerateContentConfig(
                            temperature=0.2,
                        )
                    )

                    st.session_state['ultima_transcripcion'] = response.text

                except Exception as e:
                    st.error(f"Hubo un error al procesar las imágenes: {e}")

        # PASO 3: Mostrar y Exportar
        if 'ultima_transcripcion' in st.session_state:
            st.success("¡Transcripción completada!")
            st.markdown("### Resultado:")
            st.container(border=True).markdown(st.session_state['ultima_transcripcion'])

            st.divider()
            st.subheader("📥 Exportar Documento")
            
            c_down1, c_down2 = st.columns(2)
            with c_down1:
                docx_bytes = generar_docx(st.session_state['ultima_transcripcion'], imagenes_ordenadas)
                st.download_button(
                    label="Descargar .docx (Word)", 
                    data=docx_bytes, 
                    file_name="Apuntes_Digitalizados.docx", 
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document", 
                    use_container_width=True
                )
            with c_down2:
                st.info("💡 Para tenerlo en PDF con las fórmulas perfectas, abrí el .docx que descargaste y dale a 'Guardar como PDF'.")
