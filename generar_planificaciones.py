import json
from openai import OpenAI
from datetime import datetime, timedelta


def generar_planificacion_trabajos_openai(datos_trabajadores, token_openai, archivo_configuracion):
    try:
        with open(archivo_configuracion, 'r', encoding='utf-8') as f:
            config_planificacion = json.load(f)
    except FileNotFoundError:
        print(f"Error: No se encontró el archivo de configuración {archivo_configuracion}")
        return None
    except json.JSONDecodeError:
        print(f"Error: El archivo {archivo_configuracion} no contiene un JSON válido")
        return None

    client = OpenAI(api_key=token_openai)

    incendio_config = config_planificacion.get('incendio', {})
    no_incendio_config = config_planificacion.get('noIncendio', {})

    fecha_inicio_incendio = datetime.strptime(
        incendio_config.get('fechaInicio', datetime.now().strftime('%Y-%m-%d')),
        '%Y-%m-%d'
    )
    fecha_inicio_no_incendio = datetime.strptime(
        no_incendio_config.get('fechaInicio', datetime.now().strftime('%Y-%m-%d')),
        '%Y-%m-%d'
    )

    def calcular_horarios_turnos(cantidad_turnos):
        horas_totales = 20
        inicio_minutos = 21 * 60 + 30
        horarios = {}
        duracion_turno_minutos = (horas_totales * 60) // cantidad_turnos

        for turno in range(1, cantidad_turnos + 1):
            inicio_turno_minutos = inicio_minutos + (turno - 1) * duracion_turno_minutos
            fin_turno_minutos = inicio_turno_minutos + duracion_turno_minutos
            inicio_horas = (inicio_turno_minutos // 60) % 24
            inicio_mins = inicio_turno_minutos % 60
            fin_horas = (fin_turno_minutos // 60) % 24
            fin_mins = fin_turno_minutos % 60
            inicio_str = f"{inicio_horas:02d}:{inicio_mins:02d}"
            fin_str = f"{fin_horas:02d}:{fin_mins:02d}"
            horarios[turno] = f"{inicio_str}-{fin_str}"

        return horarios

    # Generate day names
    def generar_dias_semana(fecha_inicio, num_dias):
        dias_semana = []
        traduccion = {
            "Monday": "Lunes",
            "Tuesday": "Martes",
            "Wednesday": "Miércoles",
            "Thursday": "Jueves",
            "Friday": "Viernes",
            "Saturday": "Sábado",
            "Sunday": "Domingo"
        }

        for i in range(num_dias):
            dia_actual = fecha_inicio + timedelta(days=i)
            nombre_dia = dia_actual.strftime("%A")  # Nombre del día en inglés
            nombre_dia_es = traduccion.get(nombre_dia, nombre_dia)  # Traducir al español

            dias_semana.append((dia_actual.strftime("%Y-%m-%d"), nombre_dia_es))  # Formato (Fecha, Día)

        return dias_semana

    dias_incendio = generar_dias_semana(fecha_inicio_incendio, incendio_config.get('dias'))
    dias_no_incendio = generar_dias_semana(fecha_inicio_no_incendio, no_incendio_config.get('dias'))

    # Convertir los días a formato correcto en el prompt
    dias_incendio_str = ", ".join([f"Día {i + 1} ({dia[1]}) ({dia[0]})" for i, dia in enumerate(dias_incendio)])
    dias_no_incendio_str = ", ".join([f"Día {i + 1} ({dia[1]}) ({dia[0]})" for i, dia in enumerate(dias_no_incendio)])

    # Normalize worker availability data
    trabajadores_normalizados = []
    for trabajador in datos_trabajadores:
        trabajador_norm = trabajador.copy()

        # Normalize availability to a consistent format
        if isinstance(trabajador['disponibilidad'], list):
            disp_obj = {}
            for dia in ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]:
                if dia in trabajador['disponibilidad']:
                    disp_obj[dia] = ["diurno", "nocturno"]
                else:
                    disp_obj[dia] = []
            trabajador_norm['disponibilidad'] = disp_obj

        trabajadores_normalizados.append(trabajador_norm)

        # Extracción de configuraciones
    incendio_config = config_planificacion.get('incendio', {})
    no_incendio_config = config_planificacion.get('noIncendio', {})

    # Obtener número de retenes de cada tipo
    turno_diurno_incendio = incendio_config.get('turnoDiurno')
    turno_nocturno_incendio = incendio_config.get('turnoNocturno')

    cabildo_personas = no_incendio_config.get('cabildoPersonas')

    # Extraer configuración de retenes de no incendio
    retenes = no_incendio_config.get('retenes')
    cantidad_turnos = len(retenes)
    retenes_configuracion = {reten['turno']: reten['personas'] for reten in retenes}
    print(retenes_configuracion)
    print("-"*100)
    # Generación del prompt
    prompt = (
        f"Genera una planificación detallada de turnos para los retenes contra incendios para los próximos "
        f"{incendio_config.get('dias')} días a "
        f"partir de la fecha {incendio_config.get('fechaInicio', 'actual')}. Los días a planificar son: "
        f"{dias_incendio_str}. "
        f"Genera una planificación detallada de turnos para los retenes contra incendios para los próximos "
        f"{no_incendio_config.get('dias')} días a "
        f"partir de la fecha {no_incendio_config.get('fechaInicio', 'actual')}. Los días a planificar son: "
        f"{dias_no_incendio_str}. "
        "Sigue estrictamente las siguientes reglas y no incluyas comentarios, advertencias ni recomendaciones "
        "adicionales:\n\n"

        "Genera la planificación tanto para el caso de incendio como para el caso de no incendio. "
        "Diferencia claramente las dos planificaciones en tu respuesta.\n\n"

        "1. **Período de Planificación:**\n"
        f"- La planificación para caso de incendio debe abarcar exactamente los próximos {incendio_config.get('dias')} "
        f"días a partir de la fecha {fecha_inicio_incendio}.\n\n"
        f"- La planificación para caso de no incendio debe abarcar exactamente los próximos "
        f"{no_incendio_config.get('dias')} días a partir de la fecha {fecha_inicio_no_incendio}.\n\n"

        "2. **Retenes Disponibles y Disponibilidad:**\n"
        f"- En caso de incendio, el turno diurno debe contar con {turno_diurno_incendio} personas trabajando y "
        f"en el turno nocturno debe contar con {turno_nocturno_incendio}; el resto descansan.\n"
        f"- En caso de no incendio, el turno diurno debe contar con {turno_diurno_incendio} personas trabajando y "
        f"en el turno nocturno debe contar con {turno_nocturno_incendio}; el resto descansan.\n"
        "- Excluye de la planificación a los trabajadores que se encuentren en estado de baja o de vacaciones.\n"
        "- Considera que hay 11 retenes del Cabildo y 11 retenes de refuerzo (Gesplan).\n\n"

        "3. **Reglas de Rotación y Descansos OBLIGATORIOS:**\n"
        "- **Patrón de turnos permitido en caso de incendio:** Noche, Noche, Descanso, Mañana, Mañana, Descanso, "
        "Noche, Noche, Descanso...\n"
        "- **Ningún trabajador puede trabajar más de 2 días seguidos.**\n"
        "- **Después de trabajar 2 días consecutivos, el siguiente día es obligatoriamente de descanso.**\n"
        "- **Está absolutamente prohibido que un trabajador trabaje 3 o más días seguidos.**\n"
        "- **No puede haber un cambio directo de nocturno a diurno sin un día de descanso obligatorio en medio.**\n"
        "- **Cada trabajador debe seguir el patrón de turnos de forma estricta, asegurando que después de dos días "
        "seguidos haya un día de descanso obligatorio.**\n"
        "- **No se puede asignar a un trabajador a dos turnos el mismo día.**\n"
        "- **En caso de no incendio, ningún trabajador puede trabajar más del 50% de los días de la planificación.**\n"
        "- **Distribuye de forma equitativa los turnos entre los trabajadores y trata de utilizar a todos los "
        "trabajadores que estén disponibles.**\n"
        "- **Asegúrate de que todos los trabajadores tengan días de descanso equilibrados, evitando sobrecargar a "
        "unos y subutilizar a otros.**\n"

        "4. **Distribución Equitativa:**\n"
        "- La carga de trabajo debe distribuirse de manera balanceada para todos los trabajadores.\n"
        "- Ningún trabajador debe estar sobrecargado ni subutilizado.\n"
        "- Evita que los mismos trabajadores sean asignados repetidamente a los mismos turnos en los 7 días.\n"
        "- Distribuye los turnos de manera que todos los trabajadores acumulen una cantidad similar de horas "
        "de trabajo en la semana, evitando asignar más de 4 días en total por trabajador.\n"

        "5. **Formato de Respuesta en caso de Incendio:**\n"
        "- Inicia con el texto 'PLANIFICACIÓN EN CASO DE INCENDIO:'\n"
        "- Usa EXACTAMENTE el siguiente formato para cada día:\n"
        "  **Día N (Nombre del día)(Fecha):**\n"
        f"  - Turno Diurno (08:00-20:00): (Lista de {turno_diurno_incendio} nombres)\n"
        f"  - Turno Nocturno (20:00-08:00): (Lista de {turno_nocturno_incendio} nombres)\n"
        "- Los nombres deben estar separados por comas y en una sola línea por turno.\n"
        "- Se deben respetar las reglas de rotación y descanso sin excepciones.\n\n"


        "6. **Turnos en No Incendio:**\n"
        "- **Turno personal del Cabildo:** De 12:30 a 21:30.\n"
        f"- **Turno personal de refuerzo:** El personal de refuerzo se divide en {cantidad_turnos} turnos entre las"
        f"21:30 hasta 17:30.\n"
        "- En caso de no incendio, los turnos de los retenes del Cabildo y los de los retenes de refuerzo son "
        "independientes.\n"
        "- De 12:30 a 17:30 coinciden los turnos de ambas cuadrillas.\n\n"
        "- **Un retén de refuerzo no puede trabajar dos turnos el mismo día obligatoriamente.**"
        "- Los retenes del Cabildo deben trabajar exclusivamente en los días en los que tengan disponibilidad. "
        "Si un trabajador del Cabildo no tiene disponibilidad en un día específico, no debe ser asignado.\n"
        "- Los retenes de refuerzo deben ser asignados únicamente en los turnos y días específicos en los que estén "
        "disponibles. "
        "Si un retén de refuerzo solo está disponible para turnos nocturnos, no puede ser asignado a un turno diurno, "
        "y viceversa.\n"
        "- **Asegúrate de que se respeten las disponibilidades de cada trabajador, tanto del Cabildo como de "
        "refuerzo.**\n"
        "- **Distribuye los turnos de forma equitativa entre todos los trabajadores disponibles, teniendo en cuenta "
        "sus disponibilidades individuales.**\n"
        "- **Evita asignar a trabajadores a turnos que no sean parte de su disponibilidad, como en el caso de Juan "
        "Mata, quien solo está disponible para turnos nocturnos.**\n\n"
        "- En todo momento deben haber como mínimo 4 retenes de guardia y como máximo 8, 4 del Cabildo y 4 de "
        "refuerzo de 12:30 a 17:30, que es cuando coinciden.\n\n"
        "- Los retenes que estén de baja o de vacaciones no podrán ser convocados para trabajar.\n"
        "- Los retenes del Cabildo que no tengan disponibilidad para ese día no pueden ser convocados para trabajar.\n"
        "- Los retenes de refuerzo que no tengan disponibilidad para ese día durante ese turno no pueden ser "
        "convocados para trabajar.\n\n"
        "- Los trabajadores **NO** deben ser asignados a un turno donde no estén disponibles según su lista de días y "
        "turnos disponibles.\n"
        "- Los trabajadores de refuerzo **NO** deben trabajar en turnos no especificados como parte de su "
        "disponibilidad "
        "(por ejemplo, si un trabajador solo está disponible para turnos nocturnos, no puede ser asignado a un "
        "turno diurno).\n"
        "- **Distribuye los turnos de forma equitativa entre todos los trabajadores disponibles, teniendo en cuenta "
        "sus disponibilidades individuales.**"
        "- **Ningún trabajador debe estar asignado a ambos turnos en el mismo día.**"

        "7. **Formato y Detalle de la Respuesta en caso de No Incendio:**\n"
        "- Inicia esta sección con el texto 'PLANIFICACIÓN EN CASO DE NO INCENDIO:'\n"
        f"- La respuesta debe incluir, para cada uno de los {no_incendio_config.get('dias')} días, los turnos de los "
        f"retenes del Cabildo y los turnos "
        "de los retenes de refuerzo.\n"
        "- Usa EXACTAMENTE el siguiente formato para cada día:\n"
        "  **Día N (Nombre del día)(Fecha):**\n"
        f"**Las horas de los turnos de los retenes refuerzo se dividiran de forma equitativa en función de la cantidad "
        f"de turnos que haya {cantidad_turnos} "
        f"**La duración de los turnos de los retenes de refuerzo deben ser las mismas**." )


    horarios_turnos = calcular_horarios_turnos(cantidad_turnos)

    for turno, personas in retenes_configuracion.items():
        turno_num = int(turno) if isinstance(turno, str) and turno.isdigit() else turno
        horario = horarios_turnos.get(turno_num, "horario")
        prompt += f"  - Turno Retenes de refuerzo {turno} ({horario}): (Lista de {personas} nombres)\n"

    prompt += f"  - Turno Retenes del Cabildo (12:30-21:30): (Lista de {cabildo_personas} nombres)\n"
    prompt += "- Los turnos de los retenes de refuerzo deben varia, un trabajador no puede tener más de un turno."
    prompt += "- Los nombres de los trabajadores deben estar separados por comas en una sola línea por turno.\n"
    prompt += ("- Si hay más de un Turno Retenes de refuerzo, un trabajador no puede ser asignado a más de un turno en "
               "un mismo día")
    prompt += ("- No se deben incluir recomendaciones sobre el uso de software de planificación ni ningún comentario "
               "extra; ")
    prompt += "solo la planificación.\n\n"

    prompt += "Datos de disponibilidad del personal:\n\n"

    for trabajador in datos_trabajadores:
        pertenece_cabildo = "Sí" if trabajador.get('personalCabildo', False) else "No"
        estado = trabajador.get('estado', 'No especificado')
        prompt += f"Trabajador: {trabajador['nombre']} {trabajador['apellidos']}\n"
        prompt += f"Estado: {estado}\n"
        prompt += f"Pertenece al Cabildo: {pertenece_cabildo}\n"
        prompt += f"Disponibilidad: {json.dumps(trabajador['disponibilidad'], ensure_ascii=False)}\n"
        prompt += f"Días No Disponibles: {json.dumps(trabajador['diasNoDisponibles'], ensure_ascii=False)}\n"
        prompt += f"Excepciones: {json.dumps(trabajador.get('excepciones', {}), ensure_ascii=False)}\n\n"

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "Eres un asistente especializado en planificación de turnos y horarios. "
                                          "Tu objetivo es crear una planificación justa y equilibrada respetando "
                                          "absolutamente todas las restricciones de disponibilidad."},
            {"role": "user", "content": prompt}],
        max_tokens=2500,
        temperature=0.1
    )
    planificacion = response.choices[0].message.content.strip()

    return planificacion
