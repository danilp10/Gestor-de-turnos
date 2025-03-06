import pandas as pd
from datetime import datetime, timedelta
import re


def convertir_a_tabla(planificacion):
    """
    Convierte una planificación de texto a formato tabular (DataFrame)

    Args:
        planificacion (str): Texto de la planificación

    Returns:
        pd.DataFrame: DataFrame con las columnas Fecha, Día, Turno, Trabajadores
    """
    if not planificacion or len(planificacion.strip()) == 0:
        print("⚠ Planificación vacía")
        return pd.DataFrame(columns=['Fecha', 'Día', 'Turno', 'Trabajadores'])

    turnos_data = []

    # Obtener la fecha real de hoy
    hoy = datetime.now()

    # Diccionario de mapeo de días de la semana
    dia_a_numero = {
        "Lunes": 0, "Martes": 1, "Miércoles": 2, "Jueves": 3,
        "Viernes": 4, "Sábado": 5, "Domingo": 6
    }

    lineas = planificacion.split('\n')
    dia_actual = None
    dia_nombre = None
    fecha_inicio = None

    print(f"📋 Procesando {len(lineas)} líneas de planificación...")

    for i, linea in enumerate(lineas):
        linea = linea.strip()
        if not linea:
            continue

        # Capturar "Día N (Nombre del día):"
        dia_match = re.search(r'Día\s+(\d+)\s*\(([^)]+)\)', linea)
        if dia_match:
            dia_num = int(dia_match.group(1))
            dia_nombre = dia_match.group(2).strip()
            print(f"✅ Encontrado: Día {dia_num} - {dia_nombre}")

            if dia_nombre.capitalize() in dia_a_numero:
                dia_actual = dia_a_numero[dia_nombre.capitalize()]

                # Calcular la fecha del "Día 1" según el día de la semana que OpenAI ha generado
                if dia_num == 1:
                    diferencia_dias = (dia_actual - hoy.weekday()) % 7
                    fecha_inicio = hoy + timedelta(days=diferencia_dias)
                    print(f"📅 Fecha inicial ajustada a: {fecha_inicio.strftime('%d/%m/%Y')} ({dia_nombre})")

            continue

        # Capturar turnos con formato "Turno X (HH:MM-HH:MM): Trabajador1, Trabajador2..."
        turno_match = re.search(r'-?\s*Turno\s+([\w\s]+)\s*\((\d{2}:\d{2}-\d{2}:\d{2})\):\s*(.+)', linea)
        if turno_match and fecha_inicio:
            tipo_turno = f"{turno_match.group(1).strip()} ({turno_match.group(2).strip()})"
            trabajadores = turno_match.group(3).strip()

            # Calcular la fecha correcta para este turno sumando los días correspondientes
            fecha_turno = fecha_inicio + timedelta(days=(dia_num - 1))

            print(
                f"  ➡ Turno detectado: '{tipo_turno}' para {fecha_turno.strftime('%d/%m/%Y')} con trabajadores: '{trabajadores}'")

            turnos_data.append({
                'Fecha': fecha_turno.strftime('%d/%m/%Y'),
                'Día': dia_nombre,
                'Turno': tipo_turno,
                'Trabajadores': trabajadores
            })
            continue

    if not turnos_data:
        print("❌ No se encontraron datos de turnos en la planificación.")
        return pd.DataFrame(columns=['Fecha', 'Día', 'Turno', 'Trabajadores'])

    print(f"✅ Datos procesados correctamente: {len(turnos_data)} turnos.")
    return pd.DataFrame(turnos_data)
