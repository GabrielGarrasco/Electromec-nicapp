import streamlit as st
import os
import requests
from PIL import Image
from google import genai
from google.genai import types

# --- DICCIONARIO DE MATERIAS A NOTION ---
# Reemplazá los números raros por los IDs reales de tus páginas de Notion.
# El nombre de la materia tiene que coincidir exacto con los que tenés en la app.
MATERIAS_NOTION = {
    "FÍSICA 1": "pega_el_id_de_32_caracteres_aca",
    "PROBABILIDAD Y ESTADÍSTICA": "pega_el_id_de_32_caracteres_aca",
    "MATEMÁTICA SUPERIOR": "pega_el_id_de_32_caracteres_aca"
}

def mandar_a_notion(texto, page_id, token):
    url = f"https://api.notion.com/v1/blocks/{page_id}/children"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    
    # Separamos el texto por renglones para mandarlo como párrafos a Notion
    bloques = []
    for parrafo in texto.split('\n'):
        if parrafo.strip():
            bloques.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": parrafo[:2000]}}]
                }
            })
            
    data = {"children": bloques}
    respuesta = requests.patch(url, headers=headers, json=data)
    return respuesta

def renderizar_transcriptor():
    st.header("Digitalizar Apuntes")

    try:
        api_key = st.secrets["GEMINI_API_KEY"]
        client = genai.Client(api_key=api_key)
        notion_token = st.secrets.get("NOTION_TOKEN", "")
    except Exception as e:
        st.error("⚠️ Faltan las API Keys en los Secrets de Streamlit.")
        return
        
    if 'dicc_abreviaturas' not in st.session_state:
        st.session_state['dicc_abreviaturas'] = "Ej: q = que, cto = circuito, tmb = también"

    with st.expander("Mis Abreviaturas (Opcional)"):
        st.info("Anotá acá tus abreviaturas si querés forzar a la IA a que las lea de una manera específica.")
        st.session_state['dicc_abreviaturas'] = st.text_area("Diccionario", st.session_state['dicc_abreviaturas'], height=100, label_visibility="collapsed")

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

        if st.button("🧠 Procesar y Transcribir Todo", type="primary", use_container_width=True):
            with st.spinner("Escaneando documentos..."):
                try:
                    prompt_maestro = f"""
                    Actúa como un transcriptor universitario experto. Transcribe TODO el texto de estas imágenes manteniendo la estructura original.
                    
                    REGLAS ESTRICTAS:
                    1. ESTRUCTURA: Respeta los títulos, subtítulos, listas y sangrías en formato Markdown.
                    2. SÍMBOLOS: Usa caracteres normales para flechas (→) y grados (°). Prohibido usar LaTeX para texto normal. Reserva LaTeX solo para ecuaciones.
                    3. ESQUEMAS/CUADROS: Transcribe su contenido de forma lógica.
                    4. NOTAS: Si hay post-its, transcríbelas agregando "[NOTA]: " al inicio.
                    5. ABREVIATURAS: Usa este diccionario provisto: {st.session_state['dicc_abreviaturas']}.
                    6. IMPORTANTE - NOMBRE DE ARCHIVO: Al final, en una nueva línea, escribe obligatoriamente:
                    NOMBRE_ARCHIVO: Unidad/tema xx - Materia - Fecha.md
                    (Saca los datos del texto. Prioriza el título de la Unidad/Tema).
                    """

                    response = client.models.generate_content(
                        model='gemini-3.6-flash',
                        contents=[prompt_maestro] + imagenes_pil_final,
                        config=types.GenerateContentConfig(temperature=0.2)
                    )

                    texto_completo = response.text
                    nombre_archivo = "Apuntes_Digitalizados.md"
                    texto_limpio = texto_completo
                    materia_detectada = ""
                    
                    if "NOMBRE_ARCHIVO:" in texto_completo:
                        partes = texto_completo.split("NOMBRE_ARCHIVO:")
                        texto_limpio = partes[0].strip()
                        nombre_archivo = partes[1].strip()
                        if not nombre_archivo.endswith(".md"): nombre_archivo += ".md"
                        
                        # Intentamos adivinar la materia buscando los nombres conocidos en el título
                        for mat in MATERIAS_NOTION.keys():
                            if mat.lower() in nombre_archivo.lower():
                                materia_detectada = mat
                                break

                    st.session_state['ultima_transcripcion'] = texto_limpio
                    st.session_state['ultimo_nombre_archivo'] = nombre_archivo
                    st.session_state['materia_detectada'] = materia_detectada

                except Exception as e:
                    st.error(f"Hubo un error al procesar las imágenes: {e}")

        # --- SECCIÓN DE EDICIÓN Y EXPORTACIÓN ---
        if 'ultima_transcripcion' in st.session_state:
            st.success("¡Transcripción completada!")
            st.markdown("### Editar Transcripción:")
            
            # Acá podés editar el texto a mano
            texto_editado = st.text_area("Revisá y corregí si hay algún error:", st.session_state['ultima_transcripcion'], height=350, label_visibility="collapsed")
            
            st.divider()
            st.subheader("📥 Guardar Apunte")
            
            # Selector de materia (por si la IA no la detectó bien)
            lista_materias = list(MATERIAS_NOTION.keys())
            idx_mat = lista_materias.index(st.session_state['materia_detectada']) if st.session_state['materia_detectada'] in lista_materias else 0
            materia_elegida = st.selectbox("¿A qué materia de Notion lo mandamos?", lista_materias, index=idx_mat)
            
            c_down1, c_down2 = st.columns(2)
            with c_down1:
                if st.button("🚀 Transferir a Notion", type="primary", use_container_width=True):
                    if not notion_token:
                        st.error("No configuraste el NOTION_TOKEN en los Secrets.")
                    else:
                        page_id = MATERIAS_NOTION[materia_elegida]
                        if page_id == "pega_el_id_de_32_caracteres_aca":
                            st.warning("Te falta poner el ID real de la materia en el código de transcriptor.py")
                        else:
                            with st.spinner("Enviando a Notion..."):
                                res = mandar_a_notion(texto_editado, page_id, notion_token)
                                if res.status_code == 200:
                                    st.toast("¡Apunte transferido con éxito! 🎉")
                                else:
                                    st.error(f"Error de Notion: {res.text}")

            with c_down2:
                st.download_button(
                    label="Descargar .md (Backup)", 
                    data=texto_editado, 
                    file_name=st.session_state.get('ultimo_nombre_archivo', 'Apuntes.md'), 
                    mime="text/markdown", 
                    use_container_width=True
                )
