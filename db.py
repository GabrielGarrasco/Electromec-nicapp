import streamlit as st
import json
import gspread
from oauth2client.service_account import ServiceAccountCredentials

def get_gspread_client():
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    secret_str = st.secrets["google_credentials"]
    try: creds_dict = json.loads(secret_str)
    except: creds_dict = json.loads(secret_str, strict=False)
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    return gspread.authorize(creds)

@st.cache_data(ttl=600)
def cargar_datos_sheet():
    try:
        client = get_gspread_client()
        sheet = client.open('StudyMeterDB').worksheet('database')
        
        # Traemos A2 (datos generales) y A3 (temarios)
        valores = sheet.get('A2:A3')
        
        datos_generales = None
        temarios = {}
        
        if valores:
            if len(valores) > 0 and len(valores[0]) > 0 and valores[0][0].strip(): 
                datos_generales = json.loads(valores[0][0])
            if len(valores) > 1 and len(valores[1]) > 0 and valores[1][0].strip(): 
                temarios = json.loads(valores[1][0])
                
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
    except: 
        return None, {}

def guardar_datos():
    try:
        datos = {
            'materias': st.session_state['materias'], 'metodos': st.session_state['metodos'],
            'distracciones': st.session_state['distracciones'], 'historial': st.session_state['historial'],
            'metas': st.session_state['metas'], 'plan_carrera': st.session_state['plan_carrera'],
            'horarios': st.session_state.get('horarios', []),
            'xp_total': st.session_state.get('xp_total', 0),
            'recompensas': st.session_state.get('recompensas', [])
        }
        temarios = st.session_state.get('temarios', {})
        
        client = get_gspread_client()
        sheet = client.open('StudyMeterDB').worksheet('database')
        
        sheet.update_acell('A2', json.dumps(datos))
        sheet.update_acell('A3', json.dumps(temarios))
        sheet.update_acell('B2', '') 
        
        # Guardamos el calendario separado por filas en la columna Z para que no desborde
        eventos_lista = st.session_state.get('calendario_manual', '').split('\n')
        eventos_formateados = [[e] for e in eventos_lista if e.strip()]
        
        sheet.batch_clear(["Z2:Z1000"])
        if eventos_formateados:
            sheet.update("Z2", eventos_formateados)
        
        cargar_datos_sheet.clear()
        st.toast("Datos guardados correctamente.")
        return True
    except Exception as e:
        st.error(f"Error al guardar: {e}")
        st.stop()
