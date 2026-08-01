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
