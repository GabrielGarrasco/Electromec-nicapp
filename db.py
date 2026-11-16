import streamlit as st
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials

MAX_CHARS = 45000

def get_gspread_client():
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    secret_str = st.secrets["google_credentials"]
    try:
        creds_dict = json.loads(secret_str)
    except:
        creds_dict = json.loads(secret_str, strict=False)
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    return gspread.authorize(creds)

def _dividir_en_celdas(texto):
    if not texto:
        return [""]
    return [texto[i:i + MAX_CHARS] for i in range(0, len(texto), MAX_CHARS)]

@st.cache_data(ttl=600)
def cargar_datos_sheet():
    try:
        client = get_gspread_client()
        sheet = client.open('StudyMeterDB').worksheet('database')
        
        # Leemos toda la fila 2 (datos generales, incluso si está dividida en varias columnas) y fila 3 (temarios)
        fila_datos = sheet.row_values(2)
        fila_temarios = sheet.row_values(3)
        
        datos_generales = None
        temarios = {}
        
        # Unimos todas las celdas consecutivas con texto de la fila 2 (ignorando la columna Z = índice 25)
        if fila_datos:
            partes_datos = [c for c in fila_datos[:24] if c and c.strip()]
            if partes_datos:
                texto_datos = "".join(partes_datos)
                datos_generales = json.loads(texto_datos)
                
        if fila_temarios:
            partes_temarios = [c for c in fila_temarios[:24] if c and c.strip()]
            if partes_temarios:
                texto_temarios = "".join(partes_temarios)
                temarios = json.loads(texto_temarios)
                
        # Traemos el calendario manual de la columna Z
        try:
            calendario_vals = sheet.get('Z2:Z1000')
            if calendario_vals:
                calendario_str = "\n".join([row[0] for row in calendario_vals if row])
                if datos_generales is not None:
                    datos_generales['calendario_manual'] = calendario_str
        except:
            pass
            
        return datos_generales, temarios
    except Exception as e:
        st.error(f"Detalle técnico del error al leer Google Sheets: {e}")
        return None, {}

def guardar_datos(silencioso=False):
    # Seguro extra: jamás permitir guardar si los datos iniciales no cargaron correctamente
    if not st.session_state.get('datos_cargados', False):
        st.error("Bloqueo de seguridad: no se guardaron cambios porque los datos iniciales no estaban cargados.")
        return False

    try:
        datos = {
            'materias': st.session_state.get('materias', []), 
            'metodos': st.session_state.get('metodos', []),
            'distracciones': st.session_state.get('distracciones', []), 
            'historial': st.session_state.get('historial', []),
            'metas': st.session_state.get('metas', []), 
            'plan_carrera': st.session_state.get('plan_carrera', []),
            'horarios': st.session_state.get('horarios', []),
            'actividades_fijas': st.session_state.get('actividades_fijas', []),
            'xp_total': st.session_state.get('xp_total', 0),
            'recompensas': st.session_state.get('recompensas', []),
            'logros_desbloqueados': st.session_state.get('logros_desbloqueados', []),
            'timer': st.session_state.get('timer', {})
        }
        temarios = st.session_state.get('temarios', {})
        
        client = get_gspread_client()
        sheet = client.open('StudyMeterDB').worksheet('database')
        
        # Dividimos en bloques de 45.000 caracteres para nunca chocar con el límite de 50.000 por celda
        bloques_datos = _dividir_en_celdas(json.dumps(datos))
        bloques_temarios = _dividir_en_celdas(json.dumps(temarios))
        
        # Limpiamos A2:X3 antes de escribir para no dejar restos viejos si antes ocupaba más columnas
        sheet.batch_clear(["A2:X3"])
        sheet.update("A2", [bloques_datos])
        sheet.update("A3", [bloques_temarios])
        
        # Guardamos el calendario separado por filas en la columna Z para que no desborde
        eventos_lista = st.session_state.get('calendario_manual', '').split('\n')
        eventos_formateados = [[e] for e in eventos_lista if e.strip()]
        
        sheet.batch_clear(["Z2:Z1000"])
        if eventos_formateados:
            sheet.update("Z2", eventos_formateados)
        
        cargar_datos_sheet.clear()
        
        if not silencioso:
            st.toast("Datos guardados correctamente.")
            
        return True
    except Exception as e:
        st.error(f"Error al guardar: {e}")
        st.stop()

@st.cache_data(ttl=600)
def cargar_flashcards():
    try:
        client = get_gspread_client()
        sheet = client.open('StudyMeterDB').worksheet('aprender')
        return sheet.get_all_records()
    except:
        return []

def guardar_todas_flashcards(lista_dict):
    try:
        client = get_gspread_client()
        sheet = client.open('StudyMeterDB').worksheet('aprender')
        sheet.clear()
        if lista_dict:
            headers = list(lista_dict[0].keys())
            valores = [list(d.values()) for d in lista_dict]
            sheet.update("A1", [headers] + valores)
        cargar_flashcards.clear()
    except Exception as e:
        st.error(f"Error al guardar flashcards: {e}")
