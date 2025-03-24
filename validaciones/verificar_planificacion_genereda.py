import json
import csv
from datetime import datetime
import os
from collections import defaultdict


def cargar_datos_usuarios(ruta_json):
    """Carga los datos de usuarios desde un archivo JSON."""
    try:
        with open(ruta_json, 'r', encoding='utf-8') as archivo:
            return json.load(archivo)
    except FileNotFoundError:
        print(f"Error: No se encontró el archivo de usuarios en {ruta_json}")
        exit(1)
    except json.JSONDecodeError:
        print(f"Error: El archivo {ruta_json} no contiene un JSON válido")
        exit(1)


def cargar_planificacion_desde_csv(ruta_csv):
    """Carga la planificación desde un archivo CSV."""
    try:
        planificacion = []
        with open(ruta_csv, 'r', encoding='utf-8') as archivo_csv:
            reader = csv.reader(archivo_csv)
            next(reader, None)  # Saltar encabezados si existen

            for fila in reader:
                if len(fila) < 4:  # Verificar que la fila tenga los 4 campos necesarios
                    continue

                fecha, dia, turno, trabajadores = fila
                trabajadores_lista = [t.strip() for t in trabajadores.split(',')]

                fecha_obj = parsear_fecha(fecha)
                dia_semana = obtener_dia_semana(fecha_obj)

                planificacion.append({
                    'fecha': fecha,
                    'fecha_obj': fecha_obj,
                    'dia_semana': dia_semana,
                    'turno': turno,
                    'trabajadores': trabajadores_lista
                })

        return planificacion
    except FileNotFoundError:
        print(f"Error: No se encontró el archivo de planificación en {ruta_csv}")
        exit(1)


def parsear_fecha(fecha_str):
    """Convierte una fecha en formato dd/mm/yyyy a un objeto datetime."""
    try:
        return datetime.strptime(fecha_str, '%d/%m/%Y')
    except ValueError:
        print(f"Error: Formato de fecha incorrecto: {fecha_str}. Debe ser dd/mm/yyyy")
        exit(1)


def obtener_dia_semana(fecha):
    """Obtiene el nombre del día de la semana en español."""
    dias = {
        0: 'lunes',
        1: 'martes',
        2: 'miércoles',
        3: 'jueves',
        4: 'viernes',
        5: 'sábado',
        6: 'domingo'
    }
    return dias[fecha.weekday()]


def usuario_disponible(usuario, dia_semana, fecha_obj):
    """Verifica si un usuario está disponible en un día específico."""
    # Verificar estado del usuario
    if usuario['estado'] != 'activo':
        if usuario['estado'] == 'vacaciones':
            # Verificar si la fecha está dentro del periodo de vacaciones
            if usuario['excepciones']['vacaciones']:
                inicio = datetime.fromisoformat(usuario['excepciones']['vacaciones']['inicio'])
                fin = datetime.fromisoformat(usuario['excepciones']['vacaciones']['fin'])
                if inicio <= fecha_obj <= fin:
                    return False
        elif usuario['estado'] == 'baja':
            # Verificar si hay fecha de reincorporación
            if usuario['excepciones']['reincorporacion']:
                reincorporacion = datetime.fromisoformat(usuario['excepciones']['reincorporacion'])
                if fecha_obj < reincorporacion:
                    return False
            else:
                return False

    # Verificar disponibilidad por día de la semana (solo para no incendio)
    return dia_semana in usuario['disponibilidad']


def usuario_disponible_incendio(usuario, fecha_obj):
    """Verifica si un usuario está disponible en caso de incendio (solo verifica no estar de baja o vacaciones)."""
    # Verificar estado del usuario
    if usuario['estado'] != 'activo':
        if usuario['estado'] == 'vacaciones':
            # Verificar si la fecha está dentro del periodo de vacaciones
            if usuario['excepciones']['vacaciones']:
                inicio = datetime.fromisoformat(usuario['excepciones']['vacaciones']['inicio'])
                fin = datetime.fromisoformat(usuario['excepciones']['vacaciones']['fin'])
                if inicio <= fecha_obj <= fin:
                    return False
        elif usuario['estado'] == 'baja':
            # Verificar si hay fecha de reincorporación
            if usuario['excepciones']['reincorporacion']:
                reincorporacion = datetime.fromisoformat(usuario['excepciones']['reincorporacion'])
                if fecha_obj < reincorporacion:
                    return False
            else:
                return False

    # En caso de incendio, si no está de baja o vacaciones, está disponible
    return True


def validar_planificacion(usuarios, planificacion, es_incendio=False):
    """Valida la planificación contra la disponibilidad de los usuarios.

    Si es_incendio es True, solo se valida que no estén de baja o vacaciones.
    """
    resultados = {
        'errores': [],
        'usuarios_no_asignados': [],
        'dias_trabajados': defaultdict(int),
        'respeto_disponibilidad': True
    }

    # Mapear nombres completos a IDs para facilitar búsqueda
    mapa_usuarios = {}
    for usuario in usuarios:
        nombre_completo = f"{usuario['nombre']} {usuario['apellidos']}"
        mapa_usuarios[nombre_completo] = usuario

    # Contar asignaciones y verificar disponibilidad
    usuarios_asignados = set()

    # Fechas únicas para verificaciones
    fechas_unicas = set(turno['fecha_obj'] for turno in planificacion)

    for turno in planificacion:
        for nombre_trabajador in turno['trabajadores']:
            if nombre_trabajador in mapa_usuarios:
                usuario = mapa_usuarios[nombre_trabajador]
                usuarios_asignados.add(nombre_trabajador)

                # Contar días trabajados
                resultados['dias_trabajados'][nombre_trabajador] += 1

                # Verificación según tipo de planificación
                if es_incendio:
                    # En caso de incendio, solo verificar que no esté de baja o vacaciones
                    if not usuario_disponible_incendio(usuario, turno['fecha_obj']):
                        resultados['errores'].append(
                            f"ERROR: {nombre_trabajador} asignado el {turno['fecha']} en planificación de INCENDIO, "
                            f"pero está de baja o vacaciones."
                        )
                        resultados['respeto_disponibilidad'] = False
                else:
                    # Verificación normal de disponibilidad para no incendio
                    if not usuario_disponible(usuario, turno['dia_semana'], turno['fecha_obj']):
                        resultados['errores'].append(
                            f"ERROR: {nombre_trabajador} asignado el {turno['fecha']} ({turno['dia_semana']}), "
                            f"pero no está disponible ese día."
                        )
                        resultados['respeto_disponibilidad'] = False
            else:
                resultados['errores'].append(
                    f"ADVERTENCIA: No se encontró información de disponibilidad para {nombre_trabajador}"
                )

    # Calcular usuarios no asignados según el tipo de planificación
    usuarios_disponibles = set()

    for usuario in usuarios:
        nombre_completo = f"{usuario['nombre']} {usuario['apellidos']}"
        disponible_algun_dia = False

        for fecha in fechas_unicas:
            if es_incendio:
                # Para incendio, solo verificar que no esté de baja o vacaciones
                if usuario_disponible_incendio(usuario, fecha):
                    disponible_algun_dia = True
                    usuarios_disponibles.add(nombre_completo)
                    break
            else:
                # Para no incendio, verificar disponibilidad normal
                dia_semana = obtener_dia_semana(fecha)
                if usuario_disponible(usuario, dia_semana, fecha):
                    disponible_algun_dia = True
                    usuarios_disponibles.add(nombre_completo)
                    break

    resultados['usuarios_no_asignados'] = list(usuarios_disponibles - usuarios_asignados)

    return resultados


def imprimir_informe(resultados, tipo_planificacion):
    """Imprime un informe detallado de los resultados de la validación."""
    print(f"\n=== INFORME DE VALIDACIÓN DE PLANIFICACIÓN ({tipo_planificacion}) ===\n")

    if resultados['errores']:
        print(f"ERRORES ENCONTRADOS ({tipo_planificacion}):")
        for error in resultados['errores']:
            print(f"- {error}")
        print()

    if resultados['usuarios_no_asignados']:
        if tipo_planificacion == 'INCENDIO':
            print(f"USUARIOS ACTIVOS NO ASIGNADOS ({tipo_planificacion}):")
        else:
            print(f"USUARIOS DISPONIBLES NO ASIGNADOS ({tipo_planificacion}):")
        for usuario in resultados['usuarios_no_asignados']:
            print(f"- {usuario}")
        print()
    else:
        if tipo_planificacion == 'INCENDIO':
            print(f"Todos los usuarios activos han sido asignados en la planificación de {tipo_planificacion}.\n")
        else:
            print(f"Todos los usuarios disponibles han sido asignados en la planificación de {tipo_planificacion}.\n")

    print(f"DÍAS TRABAJADOS POR USUARIO ({tipo_planificacion}):")
    for usuario, dias in sorted(resultados['dias_trabajados'].items()):
        print(f"- {usuario}: {dias} día(s)")
    print()

    print(f"RESUMEN FINAL ({tipo_planificacion}):")
    print(f"- Usuarios asignados: {len(resultados['dias_trabajados'])}")

    if tipo_planificacion == 'INCENDIO':
        print(f"- Usuarios activos no asignados: {len(resultados['usuarios_no_asignados'])}")
        if resultados['respeto_disponibilidad']:
            print(f"- No hay usuarios de baja o vacaciones asignados.")
        else:
            print(f"- ADVERTENCIA: Hay usuarios de baja o vacaciones asignados. Revisar errores arriba.")
    else:
        print(f"- Usuarios disponibles no asignados: {len(resultados['usuarios_no_asignados'])}")
        if resultados['respeto_disponibilidad']:
            print(f"- Se respetaron todas las disponibilidades de los usuarios.")
        else:
            print(f"- NO se respetaron todas las disponibilidades. Revisar errores arriba.")


def exportar_resultados_json(resultados_no_incendio, resultados_incendio, ruta_salida):
    """Exporta los resultados de validación a un archivo JSON para consumo por GPT-4."""

    # Convertir objetos datetime a strings para que sean serializables
    resultados_serializables_no_incendio = {
        "errores": resultados_no_incendio["errores"],
        "usuarios_no_asignados": resultados_no_incendio["usuarios_no_asignados"],
        "dias_trabajados": dict(resultados_no_incendio["dias_trabajados"]),  # Convertir defaultdict a dict
        "respeto_disponibilidad": resultados_no_incendio["respeto_disponibilidad"],
        "total_usuarios_asignados": len(resultados_no_incendio["dias_trabajados"]),
        "total_usuarios_no_asignados": len(resultados_no_incendio["usuarios_no_asignados"]),
        "total_errores": len(resultados_no_incendio["errores"])
    }

    resultados_serializables_incendio = {
        "errores": resultados_incendio["errores"],
        "usuarios_no_asignados": resultados_incendio["usuarios_no_asignados"],
        "dias_trabajados": dict(resultados_incendio["dias_trabajados"]),  # Convertir defaultdict a dict
        "respeto_disponibilidad": resultados_incendio["respeto_disponibilidad"],
        "total_usuarios_asignados": len(resultados_incendio["dias_trabajados"]),
        "total_usuarios_no_asignados": len(resultados_incendio["usuarios_no_asignados"]),
        "total_errores": len(resultados_incendio["errores"])
    }

    # Estructurar datos para GPT-4
    datos_para_gpt = {
        "planificacion_no_incendio": resultados_serializables_no_incendio,
        "planificacion_incendio": resultados_serializables_incendio,
        "metadatos": {
            "fecha_generacion": datetime.now().isoformat(),
            "version": "1.0",
            "descripcion": "Validación de planificaciones para ser analizada por GPT-4"
        }
    }

    # Guardar en archivo JSON
    try:
        with open(ruta_salida, 'w', encoding='utf-8') as archivo_json:
            json.dump(datos_para_gpt, archivo_json, ensure_ascii=False, indent=2)
        print(f"\nResultados exportados exitosamente a: {ruta_salida}")
    except Exception as e:
        print(f"\nError al exportar resultados a JSON: {str(e)}")


def main():
    disponibilidades = '../trabajadores/disponibilidades.json'
    planificacion_no_incendio = "../planificaciones_generadas/temp_planificacion_no_incendio.csv"
    planificacion_incendio = "../planificaciones_generadas/temp_planificacion_incendio.csv"

    # Ruta para guardar resultados en formato JSON para GPT-4
    ruta_resultados_json = "../validaciones/resultados_validacion.json"

    # Asegurar que el directorio de salida existe
    os.makedirs(os.path.dirname(ruta_resultados_json), exist_ok=True)

    usuarios = cargar_datos_usuarios(disponibilidades)

    # Validar planificación de no incendio
    print("\n" + "=" * 50)
    print("VALIDACIÓN DE PLANIFICACIÓN SIN INCENDIO")
    print("=" * 50)
    plan_no_incendio = cargar_planificacion_desde_csv(planificacion_no_incendio)
    resultados_no_incendio = validar_planificacion(usuarios, plan_no_incendio, es_incendio=False)
    imprimir_informe(resultados_no_incendio, "NO INCENDIO")

    # Validar planificación de incendio
    print("\n" + "=" * 50)
    print("VALIDACIÓN DE PLANIFICACIÓN CON INCENDIO")
    print("=" * 50)
    plan_incendio = cargar_planificacion_desde_csv(planificacion_incendio)
    resultados_incendio = validar_planificacion(usuarios, plan_incendio, es_incendio=True)
    imprimir_informe(resultados_incendio, "INCENDIO")

    # Resumen comparativo
    print("\n" + "=" * 50)
    print("RESUMEN COMPARATIVO DE AMBAS PLANIFICACIONES")
    print("=" * 50)
    print(f"Planificación NO INCENDIO:")
    print(f"- Total de usuarios asignados: {len(resultados_no_incendio['dias_trabajados'])}")
    print(f"- Usuarios disponibles no asignados: {len(resultados_no_incendio['usuarios_no_asignados'])}")
    print(f"- Errores de disponibilidad: {len(resultados_no_incendio['errores'])}")
    print(f"- Cumplimiento de disponibilidad: {'SÍ' if resultados_no_incendio['respeto_disponibilidad'] else 'NO'}")

    print(f"\nPlanificación INCENDIO:")
    print(f"- Total de usuarios asignados: {len(resultados_incendio['dias_trabajados'])}")
    print(f"- Usuarios activos no asignados: {len(resultados_incendio['usuarios_no_asignados'])}")
    print(f"- Errores (usuarios de baja/vacaciones): {len(resultados_incendio['errores'])}")
    print(f"- Nota: En caso de incendio no se validan las disponibilidades por día")

    # Exportar resultados a JSON para consumo por GPT-4
    exportar_resultados_json(resultados_no_incendio, resultados_incendio, ruta_resultados_json)


if __name__ == "__main__":
    main()
