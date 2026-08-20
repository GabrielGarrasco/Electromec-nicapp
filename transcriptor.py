import streamlit as st
import os
import requests
import re
from PIL import Image
from google import genai
from google.genai import types

# --- DICCIONARIO DE MATERIAS A NOTION ---
MATERIAS_NOTION = {
    "FÍSICA 1": "pega_el_id_de_32_caracteres_aca",
    "PROBABILIDAD Y ESTADÍSTICA": "3c2f8087b7d18038959cd4ee3c84cfc7",
    "MATEMÁTICA SUPERIOR": "pega_el_id_de_32_caracteres_aca"
}

def parse_rich_text(text):
    """Traduce negritas y fórmulas inline al formato nativo de Notion"""
    tokens = re.split(r'(\$\$.*?\$\$|\$.*?\$|\*\*.*?\*\*)', text)
    rich_text_array = []
    for token in tokens:
        if not token: continue
        if token.startswith('$$') and token.endswith('$$'):
            rich_text_array.append({"type": "equation", "equation": {"expression": token[2:-2].strip()}})
        elif token.startswith('$') and token.endswith('$'):
            rich_text_array.append({"type": "equation", "equation": {"expression": token[1:-1].strip()}})
        elif token.startswith('**') and token.endswith('**'):
            rich_text_array.append({"type": "text", "text": {"content": token[2:-2]}, "annotations": {"bold": True}})
        else:
            rich_text_array.append({"type": "text", "text": {"content": token}})
    return rich_text_array

def markdown_to_notion_blocks(markdown_text):
    """Convierte el texto Markdown crudo en bloques puros de Notion"""
    bloques = []
    lineas = markdown_text.split('\n')
    i = 0
    
    while i < len(lineas):
        linea = lineas[i].strip()
        if not linea:
            i += 1
            continue
            
        # 1. Títulos
        if linea.startswith('### '):
            bloques.append({"object": "block", "type": "heading_3", "heading_3": {"rich_text": parse_rich_text(linea[4:])}})
        elif linea.startswith('## '):
            bloques.append({"object": "block", "type": "heading_2", "heading_2": {"rich_text": parse_rich_text(linea[3:])}})
        elif linea.startswith('# '):
            bloques.append({"object": "block", "type": "heading_1", "heading_1": {"rich_text": parse_rich_text(linea[2:])}})
            
        # 2. Listas y Viñetas
        elif linea.startswith('* ') or linea.startswith('- '):
            bloques.append({"object": "block", "type": "bulleted_list_item", "bulleted_list_item": {"rich_text": parse_rich_text(linea[2:])}})
            
        # 3. Citas / Quotes
        elif linea.startswith('> '):
            bloques.append({"object": "block", "type": "quote", "quote": {"rich_text": parse_rich_text(linea[2:])}})
            
        # 4. Separador
        elif linea == '---':
            bloques.append({"object": "block", "type": "divider", "divider": {}})
            
        # 5. Ecuaciones en bloque grande
        elif linea.startswith('$$') and linea.endswith('$$') and len(linea) > 4:
            bloques.append({"object": "block", "type": "equation", "equation": {"expression": linea[2:-2].strip()}})
            
        # 6. Tablas Mágicas
        elif linea.startswith('|'):
            table_rows = []
            while i < len(lineas) and lineas[i].strip().startswith('|'):
                row_line = lineas[i].strip()
                if re.match(r'^\|[\s\-\|:]+\|$', row_line):
                    i += 1
                    continue
                
                cells = [cell.strip() for cell in row_line.split('|')[1:-1]]
                row_cells = [parse_rich_text(cell) for cell in cells]
                table_rows.append({"object": "block", "type": "table_row", "table_row": {"cells": row_cells}})
                i += 1
                
            if table_rows:
                bloques.append({
                    "object": "block", "type": "table",
                    "table": {
                        "table_width": len(table_rows[0]["table_row"]["cells"]),
                        "has_column_header": True, "has_row_header": False,
                        "children": table_rows
                    }
                })
            continue 
            
        # 7. POST-ITS (Callout Amarillo)
        elif linea.startswith('[NOTA]:'):
            texto_nota = linea.replace('[NOTA]:', '').strip()
            bloques.append({
                "object": "block",
                "type": "callout",
                "callout": {
                    "rich_text": parse_rich_text(texto_nota),
                    "icon": {"type": "emoji", "emoji": "📌"},
                    "color": "yellow_background"
                }
            })
            
        # 8. HUECO PARA IMÁGENES (Callout Azul)
        elif '[IMAGEN_ESQUEMA]' in linea:
            bloques.append({
                "object": "block",
                "type": "callout",
                "callout": {
                    "rich_text": [{"type": "text", "text": {"content": "Arrastrá la foto del esquema o diagrama acá."}}],
                    "icon": {"type": "emoji", "emoji": "🖼️"},
                    "color": "blue_background"
                }
            })
            
        # 9. EJEMPLOS (Párrafo con texto verde)
        elif linea.startswith('[EJEMPLO]:'):
            texto_ejemplo = linea.replace('[EJEMPLO]:', '').strip()
            bloques.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": parse_rich_text(texto_ejemplo),
                    "color": "green"
                }
            })
            
        # 10. Párrafos normales
        else:
            bloques.append({"object": "block", "type": "paragraph", "paragraph": {"rich_text": parse_rich_text(linea)}})
            
        i += 1
    return bloques

def mandar_a_notion(texto, page_id, token):
    url = f"https://api.notion.com/v1/blocks/{page_id}/children"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    
    bloques_procesados = markdown_to_notion_blocks(texto)
    
    chunk_size = 90
    respuesta = None
    for i in range(0, len(bloques_procesados), chunk_size):
        chunk = bloques_procesados[i:i + chunk_size]
        data = {"children": chunk}
        respuesta = requests.patch(url, headers=headers, json=data)
        if respuesta.status_code != 200:
            return respuesta
            
    return respuesta

@st.dialog("✏️ Editar Transcripción", width="large")
def dialog_editar_texto():
    st.info("Acá podés corregir la versión cruda. Lo que guardes acá es lo que se envía a Notion.")
    texto_editado = st.text_area("Texto", st.session_state['ultima_transcripcion'], height=450, label_visibility="collapsed")
    if st.button("Guardar Cambios", type="primary"):
        st.session_state['ultima_transcripcion'] = texto_editado
        st.rerun()

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
                    1. ESTRUCTURA: Respeta los títulos, subtítulos y sangrías. 
                    2. LISTAS: Si hay viñetas, usa siempre un asterisco y un espacio (* ) al inicio del renglón.
                    3. SÍMBOLOS: Usa caracteres normales para flechas (→) y grados (°). Reserva LaTeX ($) EXCLUSIVAMENTE para ecuaciones.
                    4. CUADROS: Genera una tabla en formato Markdown puro (separada con |).
                    5. ESQUEMAS: Si hay un mapa mental o dibujo que no se puede transcribir, escribe en un renglón nuevo exactamente: [IMAGEN_ESQUEMA]
                    6. NOTAS: Si hay post-its o anotaciones sueltas, escribe en un renglón nuevo empezando exactamente con: [NOTA]: seguido del texto.
                    7. ABREVIATURAS Y TEXTO LITERAL: Usa este diccionario provisto: {st.session_state['dicc_abreviaturas']}. IMPORTANTE: NO omitas abreviaturas que no estén en el diccionario (como "coef."), transcríbelas tal cual, letra por letra, sin saltearte nada.
                    8. EJEMPLOS (LÁPIZ): Los ejemplos y ejercicios (que muchas veces están escritos en lápiz) escríbelos en un renglón nuevo empezando exactamente con la etiqueta: [EJEMPLO]: seguido del texto.
                    9. NOMBRE DE ARCHIVO: Al final, en una nueva línea, escribe obligatoriamente:
                    NOMBRE_ARCHIVO: Unidad/tema xx - Materia - Fecha
                    """

                    response = client.models.generate_content(
                        model='gemini-3.6-flash',
                        contents=[prompt_maestro] + imagenes_pil_final,
                        config=types.GenerateContentConfig(temperature=0.2)
                    )

                    texto_completo = response.text
                    texto_limpio = texto_completo
                    materia_detectada = ""
                    
                    if "NOMBRE_ARCHIVO:" in texto_completo:
                        partes = texto_completo.split("NOMBRE_ARCHIVO:")
                        texto_limpio = partes[0].strip()
                        nombre_archivo = partes[1].strip()
                        
                        for mat in MATERIAS_NOTION.keys():
                            if mat.lower() in nombre_archivo.lower():
                                materia_detectada = mat
                                break

                    st.session_state['ultima_transcripcion'] = texto_limpio
                    st.session_state['materia_detectada'] = materia_detectada

                except Exception as e:
                    st.error(f"Hubo un error al procesar las imágenes: {e}")

        # --- SECCIÓN DE PREVISUALIZACIÓN Y EXPORTACIÓN ---
        if 'ultima_transcripcion' in st.session_state:
            st.success("¡Transcripción completada!")
            
            st.markdown("### Previsualización:")
            
            # Reemplazo visual para Streamlit (renderiza el verde en la previsualización)
            texto_preview = st.session_state['ultima_transcripcion'].replace('[EJEMPLO]:', '<span style="color: green; font-weight: bold;">[EJEMPLO]:</span>')
            st.container(border=True).markdown(texto_preview, unsafe_allow_html=True)

            st.divider()
            
            lista_materias = list(MATERIAS_NOTION.keys())
            idx_mat = lista_materias.index(st.session_state['materia_detectada']) if st.session_state.get('materia_detectada') in lista_materias else 0
            materia_elegida = st.selectbox("¿A qué materia de Notion lo mandamos?", lista_materias, index=idx_mat)
            
            c_btn1, c_btn2 = st.columns(2)
            
            with c_btn1:
                if st.button("✏️ Editar Texto", use_container_width=True):
                    dialog_editar_texto()
                    
            with c_btn2:
                if st.button("🚀 Transferir a Notion", type="primary", use_container_width=True):
                    if not notion_token:
                        st.error("No configuraste el NOTION_TOKEN en los Secrets.")
                    else:
                        page_id = MATERIAS_NOTION[materia_elegida]
                        if page_id == "pega_el_id_de_32_caracteres_aca":
                            st.warning("Te falta poner el ID real de la materia en el código.")
                        else:
                            with st.spinner("Enviando a Notion con formato nativo..."):
                                res = mandar_a_notion(st.session_state['ultima_transcripcion'], page_id, notion_token)
                                if res.status_code == 200:
                                    st.toast("¡Apunte transferido con éxito! 🎉")
                                else:
                                    st.error(f"Error de Notion: {res.text}")

if __name__ == "__main__":
    renderizar_transcriptor()
