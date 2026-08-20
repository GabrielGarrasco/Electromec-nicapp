import pandas as pd
from datetime import datetime, date

def parse_float_nota(val_str):
    try: return float(str(val_str).replace(',', '.'))
    except: return None

def calcular_datos_racha(historial):
    if not historial: return 0, 0, 0, 5
    
    # Limpieza absoluta de fechas para evitar duplicados "fantasmas"
    fechas_obj = set()
    for h in historial:
        f_str = str(h.get('FECHA', '')).strip()
        if f_str:
            try:
                fechas_obj.add(datetime.strptime(f_str, "%d/%m/%Y").date())
            except:
                pass
                
    fechas_obj = sorted(list(fechas_obj))
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

def calcular_proximo_repaso(confianza, nivel_actual, fecha_examen_str=None):
    # Lógica base SM-2 (Repetición Espaciada)
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
        
    hoy = date.today()
    prox_fecha_obj = hoy + pd.Timedelta(days=dias)
    
    # MODO PÁNICO: Si el examen es antes de la fecha recomendada por la curva
    if fecha_examen_str:
        try:
            fecha_examen_obj = date.fromisoformat(fecha_examen_str)
            dias_hasta_examen = (fecha_examen_obj - hoy).days
            
            # Si el examen es pronto y el repaso caía después del examen
            if dias_hasta_examen > 0 and prox_fecha_obj >= fecha_examen_obj:
                dias_comprimidos = max(1, dias_hasta_examen // 2)
                prox_fecha_obj = hoy + pd.Timedelta(days=dias_comprimidos)
        except:
            pass
            
    return nuevo_nivel, prox_fecha_obj.isoformat()
