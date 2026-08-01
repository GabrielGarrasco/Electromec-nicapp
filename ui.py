import streamlit as st

def cargar_css():
    st.markdown("""
        <style>
        /* Fondo general oscuro: #000a23 */
        .stApp { background-color: #000a23; color: #f8fafc; font-family: 'Inter', sans-serif; }
        
        /* Ajuste de margen superior para que respire */
        .block-container { padding-top: 3rem !important; padding-bottom: 1rem !important; }
        header { display: none !important; }
        
        [data-testid="collapsedControl"] { display: none; }
        
        /* Pestañas (Tabs) */
        .stTabs [data-baseweb="tab-list"] { justify-content: center; background-color: transparent; gap: 30px; border-bottom: 1px solid #153f59; }
        .stTabs [data-baseweb="tab"] { color: #7498b6; font-weight: 700; font-size: 16px; padding-bottom: 10px; }
        .stTabs [aria-selected="true"] { color: #94b8d7 !important; border-bottom: 3px solid #10b981 !important; }
        
        /* Contenedores (Tarjetas) - Más compactas */
        [data-testid="stVerticalBlock"] > [style*="flex-direction: column;"] > [data-testid="stVerticalBlock"] { 
            background-color: #02152b; border-radius: 12px; padding: 12px; border: 1px solid #153f59; 
        }
        
        /* Divisores ultra finos para ahorrar espacio */
        .custom-hr { margin: 12px 0; border: none; border-top: 1px solid #153f59; }
        
        /* Botones primarios (Forzamos Verde Menta contra el rojo de Streamlit) */
        button[kind="primary"] { 
            background-color: #10b981 !important; border-color: #10b981 !important; color: #000a23 !important; border-radius: 8px !important; font-weight: bold !important; padding: 8px !important;
        }
        button[kind="primary"]:hover { background-color: #059669 !important; border-color: #059669 !important; color: white !important;}
        
        /* Botones secundarios */
        button[kind="secondary"] { 
            background-color: #021d34 !important; border-color: #153f59 !important; color: #94b8d7 !important; border-radius: 8px !important; font-weight: 600 !important; padding: 8px !important;
        }
        button[kind="secondary"]:hover { border-color: #365b77 !important; color: white !important; }
        
        /* Métricas */
        [data-testid="stMetricValue"] { color: #f8fafc; font-size: 2rem; font-weight: 800; }
        [data-testid="stMetricLabel"] { color: #7498b6; font-size: 0.85rem; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; }
        
        /* Badges */
        .color-circle { width: 16px; height: 16px; border-radius: 50%; margin: 0 auto 5px auto; border: 2px solid #153f59; display: inline-block; vertical-align: middle;}
        .badge-regular { background-color: #eab308; color: #713f12; padding: 2px 6px; border-radius: 6px; font-size: 9px; font-weight: bold; }
        .badge-aprobada { background-color: #22c55e; color: #14532d; padding: 2px 6px; border-radius: 6px; font-size: 9px; font-weight: bold; }
        .badge-cursando { background-color: #3b82f6; color: #1e3a8a; padding: 2px 6px; border-radius: 6px; font-size: 9px; font-weight: bold; }
        .badge-pendiente { background-color: #64748b; color: #0f172a; padding: 2px 6px; border-radius: 6px; font-size: 9px; font-weight: bold; }
        .badge-libre { background-color: #ef4444; color: #450a0a; padding: 2px 6px; border-radius: 6px; font-size: 9px; font-weight: bold; }
        .nota-box { background-color: #021d34; border: 1px solid #153f59; border-radius: 8px; padding: 10px; text-align: center; margin-top: 10px; }
        
        /* Horario Automático */
        .tabla-horario { width: 100%; border-collapse: collapse; text-align: center; color: #f8fafc; font-family: sans-serif; font-size: 13px; margin-top: 10px; background-color: #000a23; table-layout: fixed; }
        .tabla-horario th { background-color: #02152b; color: #94b8d7; padding: 10px 5px; border: 1px solid #153f59; font-weight: 800; text-transform: uppercase; letter-spacing: 1px; }
        .tabla-horario th:first-child { color: #7498b6; width: 10%; }
        .tabla-horario td { padding: 0; border: 1px solid #153f59; vertical-align: top; height: 60px; }
        .tabla-horario td:first-child { font-weight: 700; color: #7498b6; background-color: #02152b; padding-top: 10px; text-align: center; }
        .materia-bloque { background-color: #365b77; color: #ffffff; padding: 4px; font-weight: 800; line-height: 1.1; width: 100%; height: 100%; min-height: 60px; display: flex; flex-direction: column; justify-content: space-between; align-items: center; box-sizing: border-box; border: 1px solid #557996; border-radius: 4px; }
        
        /* Historial Mejorado */
        .tabla-historial { width: 100%; border-collapse: collapse; text-align: left; color: #f8fafc; font-family: sans-serif; background-color: transparent; }
        .tabla-historial th { background-color: #02152b; color: #7498b6; padding: 12px 15px; border-bottom: 1px solid #153f59; font-weight: 800; font-size: 11px; text-transform: uppercase; letter-spacing: 1px; }
        .tabla-historial td { padding: 15px; border-bottom: 1px solid #021d34; vertical-align: middle; }
        .tabla-historial tr:last-child td { border-bottom: none; }
        .tabla-historial tr:hover td { background-color: #02152b; }
        .materia-pill { background-color: #365b77; color: white; padding: 4px 10px; border-radius: 6px; font-weight: 700; font-size: 11px; display: inline-block; text-transform: uppercase;}
        .efic-green { color: #10b981; font-weight: 900; font-size: 18px; }
        
        /* Textos Analitica */
        .analitica-title { font-size: 11px; font-weight: 800; color: #7498b6; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 10px; }
        .analitica-big-number { font-size: 28px; font-weight: 900; color: #f8fafc; text-align: center; margin: 10px 0; }
        .historico-box { text-align: center; }
        .historico-title { font-size: 10px; font-weight: 800; color: #7498b6; text-transform: uppercase; margin-bottom: 5px; }
        .historico-val { font-size: 20px; font-weight: 900; color: #f8fafc; }
        </style>
    """, unsafe_allow_html=True)
