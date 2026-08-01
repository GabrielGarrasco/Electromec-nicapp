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
        
        # Traemos A2 (datos generales) y A3 (temarios) en hilera
        valores = sheet.get('A2:A3')
        
        datos_generales = None
        temarios = {}
        
        if valores:
            if len(valores) > 0 and len(valores[0]) > 0 and valores[0][0].strip(): 
                datos_generales = json.loads(valores[0][0])
            if len(valores) > 1 and len(valores[1]) > 0 and valores[1][0].strip(): 
                temarios = json.loads(valores[1][0])
                
        return datos_generales, temarios
    except: 
        return None, {}

def guardar_datos():
    try:
        datos = {
            'materias': st.session_state['materias'], 'metodos': st.session_state['metodos'],
            'distracciones': st.session_state['distracciones'], 'historial': st.session_state['historial'],
            'metas': st.session_state['metas'], 'plan_carrera': st.session_state['plan_carrera'],
            'horarios': st.session_state.get('horarios', [])
        }
        temarios = st.session_state.get('temarios', {})
        
        client = get_gspread_client()
        sheet = client.open('StudyMeterDB').worksheet('database')
        
        # Guardamos en la misma hilera
        sheet.update_acell('A2', json.dumps(datos))
        sheet.update_acell('A3', json.dumps(temarios))
        sheet.update_acell('B2', '') # Limpiamos B2 por las dudas
        
        cargar_datos_sheet.clear()
        st.toast("Datos guardados correctamente.")
        return True
    except Exception as e:
        st.error(f"Error al guardar: {e}")
        st.stop()
