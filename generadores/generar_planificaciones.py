import json
from openai import OpenAI
from datetime import datetime, timedelta


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
        nombre_dia = dia_actual.strftime("%A")
        nombre_dia_es = traduccion.get(nombre_dia, nombre_dia)

        dias_semana.append((dia_actual.strftime("%Y-%m-%d"), nombre_dia_es))

    return dias_semana


def generar_planificacion_trabajos_openai(datos_trabajadores, token_openai, archivo_configuracion,
                                          resultados_validacion=None):
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

    tipo_planificacion = config_planificacion.get('tipoPlanificacion', 'ambos')
    print(f"Generando planificación para: {tipo_planificacion}")

    generar_incendio = tipo_planificacion in ['ambos', 'incendio']
    generar_no_incendio = tipo_planificacion in ['ambos', 'noIncendio']

    incendio_config = config_planificacion.get('incendio', {}) if generar_incendio else {}
    no_incendio_config = config_planificacion.get('noIncendio', {}) if generar_no_incendio else {}
    materiales_config = config_planificacion.get('materiales', {})

    fecha_inicio_incendio = None
    fecha_inicio_no_incendio = None
    turno_diurno_incendio = 0
    turno_nocturno_incendio = 0
    cabildo_personas = 0
    cantidad_turnos = 0
    retenes_configuracion = {}
    dias_incendio_str = ""
    dias_no_incendio_str = ""
    horarios_turnos = {}
    conductores_por_turno = 0

    if generar_incendio:
        fecha_inicio_incendio = datetime.strptime(
            incendio_config.get('fechaInicio', datetime.now().strftime('%Y-%m-%d')),
            '%Y-%m-%d'
        )
        turno_diurno_incendio = incendio_config.get('turnoDiurno')
        turno_nocturno_incendio = incendio_config.get('turnoNocturno')
        dias_incendio = generar_dias_semana(fecha_inicio_incendio, incendio_config.get('dias'))
        dias_incendio_str = ", ".join([f"Día {i + 1} ({dia[1]}) ({dia[0]})" for i, dia in enumerate(dias_incendio)])
        conductores_por_turno = incendio_config.get('conductores')

    if generar_no_incendio:
        fecha_inicio_no_incendio = datetime.strptime(
            no_incendio_config.get('fechaInicio', datetime.now().strftime('%Y-%m-%d')),
            '%Y-%m-%d'
        )
        cabildo_personas = no_incendio_config.get('cabildoPersonas')
        retenes = no_incendio_config.get('retenes', [])
        cantidad_turnos = len(retenes)
        retenes_configuracion = {reten['turno']: reten['personas'] for reten in retenes}
        horarios_turnos = calcular_horarios_turnos(cantidad_turnos)
        dias_no_incendio = generar_dias_semana(fecha_inicio_no_incendio, no_incendio_config.get('dias'))
        dias_no_incendio_str = ", ".join(
            [f"Día {i + 1} ({dia[1]}) ({dia[0]})" for i, dia in enumerate(dias_no_incendio)])

    trabajadores_normalizados = []
    for trabajador in datos_trabajadores:
        trabajador_norm = trabajador.copy()

        if isinstance(trabajador['disponibilidad'], list):
            disp_obj = {}
            for dia in ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]:
                if dia in trabajador['disponibilidad']:
                    disp_obj[dia] = ["diurno", "nocturno"]
                else:
                    disp_obj[dia] = []
            trabajador_norm['disponibilidad'] = disp_obj

        trabajadores_normalizados.append(trabajador_norm)

    prompt = ""

    # Encabezado común del prompt
    prompt += ("Eres un asistente especializado en planificación de turnos y horarios. "
               "Debes crear una planificación justa que respete todas las restricciones.\n "
               "No incluyas comentarios, advertencias o recomendaciones adicionales.\n\n")

    # Prompt para caso de incendio
    if generar_incendio:
        fecha_inicio_incendio = datetime.strptime(
            incendio_config.get('fechaInicio', datetime.now().strftime('%Y-%m-%d')),
            '%Y-%m-%d'
        )
        prompt += (
            f"Genera una planificación detallada de turnos para los retenes contra incendios para los próximos "
            f"{incendio_config.get('dias')} días a "
            f"partir de la fecha {incendio_config.get('fechaInicio', 'actual')}. \n Los días a planificar son: "
            f"{dias_incendio_str}.\n\n"

            "1. **Período de Planificación:**\n"
            f"- La planificación para caso de incendio debe abarcar exactamente los próximos "
            f"{incendio_config.get('dias')} días a partir de la fecha {fecha_inicio_incendio}.\n\n"

            "2. **Retenes Disponibles y Disponibilidad:**\n"
            f"- En caso de incendio, el turno diurno debe contar con {turno_diurno_incendio} personas trabajando y "
            f"en el turno nocturno debe contar con {turno_nocturno_incendio}; el resto descansan.\n"
            "- Excluye de la planificación a los trabajadores que se encuentren en estado de baja o de vacaciones.\n"
            "- Considera que hay 11 retenes del Cabildo y 11 retenes de refuerzo QUE DEBEN SER UTILIZADOS EN SU "
            "TOTALIDAD A LO LARGO DE LA PLANIFICACIÓN.\n\n"

            "3. **Reglas de Rotación y Descansos OBLIGATORIOS:**\n"
            # "- **Patrón de turnos permitido en caso de incendio:** Noche, Noche, Descanso, Mañana, Mañana, Descanso, "
            # "Noche, Noche, Descanso...\n"
            "- **Ningún trabajador puede trabajar más de 2 días seguidos.**\n"
            "- **Después de trabajar 2 días consecutivos, el siguiente día es obligatoriamente de descanso.**\n"
            "- **Está absolutamente prohibido que un trabajador trabaje 3 o más días seguidos.**\n"
            "- **No puede haber un cambio directo de nocturno a diurno sin un día de descanso obligatorio en medio.**\n"
            # "- **Cada trabajador debe seguir el patrón de turnos de forma estricta, asegurando que después de dos 
            # días seguidos haya un día de descanso obligatorio.**\n"
            "- **No se puede asignar un trabajador a dos turnos el mismo día.**\n"
            "- **Distribuye de forma equitativa los turnos entre los trabajadores y trata de utilizar a todos los "
            "trabajadores que estén disponibles.**\n"
            "- **Asegúrate de que todos los trabajadores tengan días de descanso equilibrados, evitando sobrecargar a "
            "unos y subutilizar a otros.**\n\n"

            "4. **Distribución Equitativa:**\n"
            "- La carga de trabajo debe distribuirse de manera balanceada para todos los trabajadores.\n"
            "- Ningún trabajador debe estar sobrecargado ni subutilizado.\n"
            "- Evita que los mismos trabajadores sean asignados repetidamente a los mismos turnos todos los días.\n"
            "- Distribuye los turnos de manera que todos los trabajadores acumulen una cantidad similar de horas "
            "de trabajo en la semana.\n\n"
            
            "5. **Recursos materiales y humanos:**\n"
            f"- Debes asignar exactamente {conductores_por_turno} conductores en cada turno.\n"
            f"- Incluye en cada día de la planificación los siguientes materiales obligatorios:\n"
            f"  * {materiales_config.get('camionesCisterna', 1)} camiones cisterna\n"
            f"  * {materiales_config.get('mascarasGas', 0)} máscaras de gas\n"
            f"  * {materiales_config.get('hachas', 0)} hachas\n"
            f"  * {materiales_config.get('escalerasMecanicas', 1)} escaleras mecánicas\n\n"

            "6. **Formato de Respuesta en caso de Incendio:**\n"
            "- Inicia con el texto 'PLANIFICACIÓN EN CASO DE INCENDIO:'\n"
            "- Usa EXACTAMENTE el siguiente formato para cada día:\n"
            "  **Día N (Nombre del día)(Fecha):**\n"
            f"  - Turno Diurno (08:00-20:00): (Lista de {turno_diurno_incendio} nombres, indicando [C] si tiene carnet "
            f"de conducir)\n"
            f"  - Turno Nocturno (20:00-08:00): (Lista de {turno_nocturno_incendio} nombres, indicando [C] si tiene "
            f"carnet de conducir)\n"
            "  - Materiales requeridos: Enumera los materiales obligatorios según lo especificado\n"
            "- Ejemplo: Juan Pérez [C], María López, Pedro Rodríguez [C], Ana García\n"
            "- Los nombres deben estar separados por comas y en una sola línea por turno.\n"
            "- Se deben respetar las reglas de rotación y descanso sin excepciones.\n\n"
        )

    if generar_no_incendio:
        prompt += (
            f"Genera una planificación detallada de turnos para los retenes en caso de no incendio para los próximos "
            f"{no_incendio_config.get('dias')} días a "
            f"partir de la fecha {no_incendio_config.get('fechaInicio', 'actual')}. \n Los días a planificar son: "
            f"{dias_no_incendio_str}.\n\n"

            "1. **Período de Planificación:**\n"
            f"- La planificación para caso de no incendio debe abarcar exactamente los próximos "
            f"{no_incendio_config.get('dias')} días a partir de la fecha {fecha_inicio_no_incendio}.\n\n"

            "2. **Turnos en No Incendio:**\n"
            "- **Turno personal del Cabildo:** De 12:30 a 21:30.\n"
            f"- **Turno personal de refuerzo:** El personal de refuerzo se divide en {cantidad_turnos} turnos entre "
            f"las 21:30 hasta 17:30.\n"
            "- En caso de no incendio, los turnos de los retenes del Cabildo y los de los retenes de refuerzo son "
            "independientes.\n"
            "- **Un retén de refuerzo no puede trabajar dos turnos el mismo día obligatoriamente.**\n"
            "- Los retenes del Cabildo deben trabajar exclusivamente en los días en los que tengan disponibilidad.\n"
            "Si un trabajador del Cabildo no tiene disponibilidad en un día específico, no debe ser asignado.\n"
            "- Los retenes de refuerzo deben ser asignados únicamente en los días específicos en los que "
            "estén disponibles.\n"
            "- **Asegúrate de que se respeten las disponibilidades de cada trabajador, tanto del Cabildo como de "
            "refuerzo.**\n"
            "- **Distribuye los turnos de forma equitativa entre todos los trabajadores disponibles, teniendo en "
            "cuenta sus disponibilidades individuales.**\n"
            "- Los retenes que estén de baja o de vacaciones no podrán ser convocados para trabajar.\n"
            "- Los retenes del Cabildo que no tengan disponibilidad para ese día no pueden ser convocados para "
            "trabajar.\n"
            "- Los retenes de refuerzo que no tengan disponibilidad para ese día no pueden ser "
            "convocados para trabajar.\n\n"
            "- Los retenes **NO** deben ser asignados a un turno donde no estén disponibles según su lista de días"
            " disponibles.\n"
            "- **Distribuye los turnos de forma equitativa entre todos los trabajadores disponibles, teniendo en "
            "cuenta sus disponibilidades individuales.**\n"
            "- **Ningún trabajador debe estar asignado a ambos turnos en el mismo día.**\n\n"
            "- Antes de asignar un trabajador a un turno, verifica que el día (por ejemplo, 'lunes', 'martes', etc.) "
            "figure en su lista de disponibilidad.\n Si no es así, no se debe asignar en ese día.\n"
            "ES OBLIGATORIO que en la planificación se asignen los 22 retenes disponibles. \n "
            "- ES CRÍTICO no asignar a ningún retén en un día que no esté en su lista de disponibilidad.\n"
            "Si algún retén no aparece asignado en ningún turno, la planificación debe ser rechazada y corregida.\n\n"

            "3. **Formato y Detalle de la Respuesta en caso de No Incendio:**\n"
        )

        if generar_incendio:
            prompt += "- Inicia esta sección con el texto 'PLANIFICACIÓN EN CASO DE NO INCENDIO:'\n"
        else:
            prompt += "- Inicia con el texto 'PLANIFICACIÓN EN CASO DE NO INCENDIO:'\n"

        prompt += (
            f"- La respuesta debe incluir, para cada uno de los {no_incendio_config.get('dias')} días, los turnos de "
            f"los retenes del Cabildo y los turnos de los retenes de refuerzo.\n"
            "- Usa EXACTAMENTE el siguiente formato para cada día:\n"
            "  **Día N (Nombre del día)(Fecha):**\n"
            f"**Las horas de los turnos de los retenes refuerzo se dividiran de forma equitativa en función de "
            f"la cantidad de turnos que haya {cantidad_turnos} \n"
            f"**La duración de los turnos de los retenes de refuerzo deben ser las mismas**.\n\n"
        )

        for turno, personas in retenes_configuracion.items():
            turno_num = int(turno) if isinstance(turno, str) and turno.isdigit() else turno
            horario = horarios_turnos.get(turno_num, "horario")
            prompt += f"  - Turno Retenes de refuerzo {turno} ({horario}): (Lista de {personas} nombres)\n"

        prompt += f"  - Turno Retenes del Cabildo (12:30-21:30): (Lista de {cabildo_personas} nombres)\n"
        prompt += ("- Los turnos de los retenes de refuerzo deben variar, un retén no puede tener más de "
                   "un turno seguido.\n")
        prompt += "- Los nombres de los trabajadores deben estar separados por comas en una sola línea por turno.\n"
        prompt += (
            "- Si hay más de un Turno Retenes de refuerzo, un trabajador no puede ser asignado a más de un turno en "
            "un mismo día \n")
        prompt += (
            "- No se deben incluir recomendaciones sobre el uso de software de planificación ni ningún comentario "
            "extra; ")
        prompt += "solo la planificación.\n\n"

    prompt += "Datos de disponibilidad del personal:\n\n"

    for trabajador in datos_trabajadores:
        pertenece_cabildo = "Sí" if trabajador.get('personalCabildo', False) else "No"
        tiene_carnet = "Sí" if trabajador.get('carnetConducir', False) else "No"
        estado = trabajador.get('estado', 'No especificado')
        prompt += f"Trabajador: {trabajador['nombre']} {trabajador['apellidos']}\n"
        prompt += f"Estado: {estado}\n"
        prompt += f"Pertenece al Cabildo: {pertenece_cabildo}\n"
        prompt += f"Carnet de Conducir: {tiene_carnet}\n"
        prompt += f"Disponibilidad: {json.dumps(trabajador['disponibilidad'], ensure_ascii=False)}\n"
        prompt += f"Días No Disponibles: {json.dumps(trabajador['diasNoDisponibles'], ensure_ascii=False)}\n"
        prompt += f"Excepciones: {json.dumps(trabajador.get('excepciones', {}), ensure_ascii=False)}\n\n"

    prompt += (
        "- ES OBLIGATORIO asignar a TODOS los 22 retenes disponibles al menos en algún turno.\n"
        "- Ningún trabajador debe ser asignado más de 3-4 días a la semana para garantizar una distribución "
        "equitativa.\n"
    )

    if resultados_validacion:
        prompt += "\n\nATENCIÓN: Revisa el informe de validación que se te proporciona a continuación:\n"
        if resultados_validacion and isinstance(resultados_validacion, dict):
            if "planificacion_no_incendio" in resultados_validacion:
                no_incendio = resultados_validacion["planificacion_no_incendio"]
                prompt += "\n- **Planificación NO INCENDIO:**\n"

                if no_incendio.get("errores"):
                    prompt += "  - **Errores encontrados:**\n"
                    prompt += "".join(f"    - {error}\n" for error in no_incendio["errores"])
                else:
                    prompt += "  - ✅ No se encontraron errores.\n"

                prompt += f"  - **Respeto de disponibilidad:** {'✅ SÍ' if no_incendio.get('respeto_disponibilidad') else '❌ NO'}\n"
                prompt += f"  - **Total usuarios asignados:** {no_incendio.get('total_usuarios_asignados', 0)}\n"
                prompt += f"  - **Total usuarios no asignados:** {no_incendio.get('total_usuarios_no_asignados', 0)}\n"
                if no_incendio.get('total_usuarios_no_asignados', 0) > 0:
                    prompt += f"  - **Usuarios no asignados:** {no_incendio.get('usuarios_no_asignados', 0)}\n"

                if no_incendio.get("dias_trabajados"):
                    prompt += "  - **Días trabajados por usuario:**\n"
                    prompt += "".join(
                        f"    - {usuario}: {dias} día(s)\n" for usuario, dias in no_incendio["dias_trabajados"].items())

            if "planificacion_incendio" in resultados_validacion:
                incendio = resultados_validacion["planificacion_incendio"]
                prompt += "\n- **Planificación INCENDIO:**\n"

                if incendio.get("errores"):
                    prompt += "  - **Errores encontrados:**\n"
                    prompt += "".join(f"    - {error}\n" for error in incendio["errores"])
                else:
                    prompt += "  - ✅ No se encontraron errores.\n"

                prompt += f"  - **Respeto de disponibilidad:** {'✅ SÍ' if incendio.get('respeto_disponibilidad') else '❌ NO'}\n"
                prompt += f"  - **Total usuarios asignados:** {incendio.get('total_usuarios_asignados', 0)}\n"
                prompt += f"  - **Total usuarios no asignados:** {incendio.get('total_usuarios_no_asignados', 0)}\n"
                if incendio.get('total_usuarios_no_asignados', 0) > 0:
                    prompt += f"  - **Usuarios no asignados:** {incendio.get('usuarios_no_asignados', 0)}\n"

                if incendio.get("dias_trabajados"):
                    prompt += "  - **Días trabajados por usuario:**\n"
                    prompt += "".join(
                        f"    - {usuario}: {dias} día(s)\n" for usuario, dias in incendio["dias_trabajados"].items())

        else:
            prompt += "- ❌ **No hay resultados de validación previa disponibles.**\n"

        prompt += "\n6. **Instrucciones para rehacer la planificación:**\n"
        prompt += "- IMPORTANTE: Corrige TODOS los errores de disponibilidad mencionados en la validación.\n"
        prompt += "- IMPORTANTE: Si un retén no tiene el lunes como día disponible no lo asignes un lunes a trabajar.\n"
        prompt += ("- IMPORTANTE: Si un retén tiene entre 0 y 1 días asignados, quita algún día a alguno de los"
                   " retenes que más trabajan y súmaselo a este retén.\n")
        prompt += ("- Asegúrate de NO asignar trabajadores en días donde no tienen disponibilidad en caso de "
                   "no incendio.\n")
        prompt += ("- Incluye obligatoriamente a todos los retenes disponibles "
                   "que no fueron asignados en la planificación anterior.\n")

    print(prompt)
    if resultados_validacion:
        print("Se están utilizando resultados de validación para corregir problemas")

    response = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[
            {"role": "system", "content": "Eres un asistente especializado en planificación de turnos y horarios. "
                                          "Tu objetivo es crear una planificación justa y equilibrada respetando "
                                          "absolutamente todas las restricciones de disponibilidad."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=3000,
        temperature=0.1,
        stream=True
    )

    print("\nGenerando planificación...\n")
    planificacion_completa = ""
    for chunk in response:
        if chunk.choices[0].delta.content:
            content_chunk = chunk.choices[0].delta.content
            planificacion_completa += content_chunk
            print(content_chunk, end="", flush=True)

    planificacion = planificacion_completa.strip()

    return planificacion, prompt
