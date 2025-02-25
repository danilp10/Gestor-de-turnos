import pandas as pd
from datetime import datetime, timedelta
import re


def convertir_a_tabla(planificacion):
    if not planificacion:
        return pd.DataFrame(columns=['Fecha', 'Día', 'Turno', 'Trabajadores'])

    turnos_data = []
    hoy = datetime.now()
    fechas = [(hoy + timedelta(days=x)).strftime('%d/%m/%Y') for x in range(7)]

    lineas = planificacion.split('\n')
    dia_actual = None

    print("Procesando planificación con", len(lineas), "líneas")

    for i, linea in enumerate(lineas):
        linea = linea.strip()
        if not linea:
            continue

        dia_match = re.search(r'[Dd]ía\s+(\d+):', linea)
        if dia_match:
            dia_num = int(dia_match.group(1))
            print(f"  Encontrado día: {dia_num}")
            if 1 <= dia_num <= 7:
                dia_actual = dia_num - 1
            continue

        turno_match = re.search(r'-\s*Turno\s+(.*?):\s+(.*)', linea)
        if turno_match and dia_actual is not None:
            try:
                tipo_turno = turno_match.group(1).strip()
                trabajadores = turno_match.group(2).strip()

                print(f"  Encontrado turno: {tipo_turno} con trabajadores: {trabajadores}")

                turnos_data.append({
                    'Fecha': fechas[dia_actual],
                    'Día': f'Día {dia_actual + 1}',
                    'Turno': tipo_turno,
                    'Trabajadores': trabajadores
                })
            except Exception as e:
                print(f"Error procesando línea {i + 1}: {linea}")
                print(f"Error: {e}")

    print(f"Datos procesados: {len(turnos_data)} turnos")
    return pd.DataFrame(turnos_data)
