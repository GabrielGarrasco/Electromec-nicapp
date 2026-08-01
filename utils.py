import pandas as pd
from datetime import datetime, date

def parse_float_nota(val_str):
    try: return float(str(val_str).replace(',', '.'))
    except: return None

def calcular_datos_racha(historial):
    if not historial: return 0, 0, 0, 5
    fechas_str = set([h['FECHA'] for h in historial])
    fechas_obj = sorted([datetime.strptime(f, "%d/%m/%Y").date() for f in fechas_str])
    if not fechas_obj: return 0, 0, 0, 5
    
    fecha_inicio = fechas_obj[0]
    hoy = date.today()
    racha_actual, mejor_racha, protectores, dias_para_protector = 0, 0, 0, 5
    
    fecha_iter = fecha_inicio
    while fecha_iter <= hoy:
        if fecha_iter in fechas_obj:
            racha_actual += 1
            dias_para_protector -= 1
            if dias_para_protector <= 0:
                protectores = min(3, protectores + 1)
                dias_para_protector = 5
        else:
            if protectores > 0:
                protectores -= 1
                racha_actual += 1 
            else:
                racha_actual = 0
                dias_para_protector = 5
        if racha_actual > mejor_racha: mejor_racha = racha_actual
        fecha_iter += pd.Timedelta(days=1)
        
    return racha_actual, mejor_racha, protectores, dias_para_protector

def calcular_proximo_repaso(confianza, nivel_actual):
    # Lógica SM-2 simplificada para repetición espaciada
    if confianza <= 2:
        nuevo_nivel = 0
        dias = 1
    elif confianza == 3:
        nuevo_nivel = max(1, nivel_actual)
        dias = 2
    else: # 4 o 5
        nuevo_nivel = nivel_actual + 1
        if nuevo_nivel == 1: dias = 1
        elif nuevo_nivel == 2: dias = 3
        elif nuevo_nivel == 3: dias = 7
        elif nuevo_nivel == 4: dias = 15
        else: dias = 30
        
    prox_fecha = (date.today() + pd.Timedelta(days=dias)).isoformat()
    return nuevo_nivel, prox_fecha
