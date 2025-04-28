import pandas as pd
from datetime import datetime, timedelta
import re


def convertir_a_tabla(planificacion, fecha_inicio_str=None):
    """
    Convierte una planificación de texto a formato tabular (DataFrame)

    Args:
        planificacion (str): Texto de la planificación
        fecha_inicio_str (str, optional): Fecha de inicio en formato 'YYYY-MM-DD'

    Returns:
        pd.DataFrame: DataFrame con las columnas Fecha, Día, Turno, Trabajadores
    """
    if not planificacion or len(planificacion.strip()) == 0:
        print("⚠ Planificación vacía")
        return pd.DataFrame(columns=['Fecha', 'Día', 'Turno', 'Trabajadores'])

    turnos_data = []

    fecha_inicio = None
    if fecha_inicio_str:
        try:
            fecha_inicio = datetime.strptime(fecha_inicio_str, '%Y-%m-%d')
            print(f"📅 Usando fecha de inicio proporcionada: {fecha_inicio.strftime('%d/%m/%Y')}")
        except ValueError:
            print(f"⚠ Formato de fecha inválido: {fecha_inicio_str}. Se usará detección automática.")

    dia_a_numero = {
        "Lunes": 0, "Martes": 1, "Miércoles": 2, "Jueves": 3,
        "Viernes": 4, "Sábado": 5, "Domingo": 6
    }

    lineas = planificacion.split('\n')
    dia_actual = None
    dia_nombre = None

    print(f"📋 Procesando {len(lineas)} líneas de planificación...")

    for i, linea in enumerate(lineas):
        linea = linea.strip()
        if not linea:
            continue

        dia_match = re.search(r'Día\s+(\d+)\s*\(([^)]+)\)', linea)
        if dia_match:
            dia_num = int(dia_match.group(1))
            dia_nombre = dia_match.group(2).strip()
            print(f"✅ Encontrado: Día {dia_num} - {dia_nombre}")

            if fecha_inicio is None and dia_num == 1:
                if dia_nombre.capitalize() in dia_a_numero:
                    dia_actual = dia_a_numero[dia_nombre.capitalize()]
                    hoy = datetime.now()
                    diferencia_dias = (dia_actual - hoy.weekday()) % 7
                    fecha_inicio = hoy + timedelta(days=diferencia_dias)
                    print(
                        f"📅 Fecha inicial determinada automáticamente: {fecha_inicio.strftime('%d/%m/%Y')} ({dia_nombre})")

            continue

        turno_match = re.search(r'-?\s*Turno\s+([\w\s]+)\s*\((\d{2}:\d{2}-\d{2}:\d{2})\):\s*(.+)', linea)
        if turno_match and fecha_inicio:
            tipo_turno = f"{turno_match.group(1).strip()} ({turno_match.group(2).strip()})"
            trabajadores = turno_match.group(3).strip()

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
