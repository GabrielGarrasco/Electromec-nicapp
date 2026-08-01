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
        valor = sheet.acell('A2').value
        if valor: return json.loads(valor)
    except: return None
    return None

def guardar_datos():
    try:
        datos = {
            'materias': st.session_state['materias'], 'metodos': st.session_state['metodos'],
            'distracciones': st.session_state['distracciones'], 'historial': st.session_state['historial'],
            'metas': st.session_state['metas'], 'plan_carrera': st.session_state['plan_carrera'],
            'horarios': st.session_state.get('horarios', [])
        }
        client = get_gspread_client()
        sheet = client.open('StudyMeterDB').worksheet('database')
        sheet.update_acell('A2', json.dumps(datos))
        
        cargar_datos_sheet.clear()
        st.toast("Datos guardados correctamente.")
        return True
    except Exception as e:
        st.error(f"Error al guardar: {e}")
        st.stop()
