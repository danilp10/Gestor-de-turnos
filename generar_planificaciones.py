import json
from openai import OpenAI


def generar_planificacion_trabajos_openai(datos_trabajadores, token_openai):
    client = OpenAI(api_key=token_openai)

    prompt = (
        "Genera una planificación detallada de turnos para los retenes contra incendios para los próximos 7 días a "
        "partir de la fecha actual. "
        "Sigue estrictamente las siguientes reglas y no incluyas comentarios, advertencias ni recomendaciones "
        "adicionales:\n\n"
        "Genera la planificación tanto para el caso de incendio como para el caso de no incendio. "
        "Diferencia claramente las dos planificaciones en tu respuesta.\n\n"

        "1. **Período de Planificación:**\n"
        "- La planificación debe abarcar exactamente los próximos 7 días a partir de la fecha actual.\n\n"

        "2. **Retenes Disponibles y Disponibilidad:**\n"
        "- Cada turno debe contar con 4 retenes trabajando; el resto descansan.\n"
        "- Excluye de la planificación a los trabajadores que se encuentren en estado de baja o de vacaciones.\n"
        "- Considera que hay 11 retenes del Cabildo y 11 retenes de refuerzo (Gesplan).\n\n"

        "3. **Turnos en Incendio:**\n"
        "- **Turno Diurno:** 08:00 - 20:00 (salida a las 07:00, regreso a las 21:00).\n"
        "- **Turno Nocturno:** 20:00 - 08:00 (salida a las 19:00, regreso a las 09:00).\n"
        "- La asignación de turnos nocturnos debe seguir la rotación exacta: **Noche, noche, descanso, mañana, mañana, "
        "descanso, noche, noche, descanso...**.\n\n"
        "- Los retenes que estén de baja o de vacaciones no podrán ser convocados para trabajar."

        "4. **Turnos en No Incendio:**\n"
        "- **Turno personal del Cabildo:** De 12:30 a 21:30.\n"
        "- **Turno personal de refuerzo:** El personal de refuerzo se divide en 2 turnos, uno de 21:30 - 07:30 y otro "
        "de 07:30 - 17:30.\n"
        "- En caso de no incendio los turnos de los retenes del Cabildo y los de los retenes de refuerzo son "
        "independientes.\n"
        "- De 12:30 a 17:30 coinciden los turnos de ambas cuadrillas.\n\n"
        "- Los retenes del Cabildo trabajan 2 días sí y 2 días no.\n\n"
        "- En todo momento deben haber como mínimo 4 retenes de guardia y como máximo 8, 4 del Cabildo y 4 de "
        "refuerzo de 12:30 a 17:30, que es cuando coinciden.\n\n"
        "- Los retenes que estén de baja o de vacaciones no podrán ser convocados para trabajar.\n"
        "- Los retenes del Cabildo que no tengan disponibilidad para ese día no pueden ser convocados para trabajar.\n"
        "- Los retenes de refuerzo que no tengan disponibilidad para ese día durante ese turno no pueden ser "
        "convocados para trabajar. \n\n"

        "5. **Formato y Detalle de la Respuesta en caso de Incendio:**\n"
        "- Inicia esta sección con el texto 'PLANIFICACIÓN EN CASO DE INCENDIO:'\n"
        "- La respuesta debe incluir, para cada uno de los 7 días, los turnos diurnos y nocturnos con los nombres de "
        "los retenes asignados.\n"
        "- Usa EXACTAMENTE el siguiente formato para cada día:\n"
        "  **Día N:**\n"
        "  - Turno Diurno (08:00-20:00): Nombre1, Nombre2, Nombre3, Nombre4\n"
        "  - Turno Nocturno (20:00-08:00): Nombre1, Nombre2, Nombre3, Nombre4\n"
        "- Los nombres de los trabajadores deben estar separados por comas en una sola línea por turno.\n"
        "- No se deben incluir recomendaciones sobre el uso de software de planificación ni ningún comentario extra; "
        "solo la planificación.\n\n"

        "6. **Formato y Detalle de la Respuesta en caso de No Incendio:**\n"
        "- Inicia esta sección con el texto 'PLANIFICACIÓN EN CASO DE NO INCENDIO:'\n"
        "- La respuesta debe incluir, para cada uno de los 7 días, los turnos de los retenes del Cabildo y los turnos "
        "de los retenes de refuerzo.\n"
        "- Usa EXACTAMENTE el siguiente formato para cada día:\n"
        "  **Día N:**\n"
        "  - Turno Retenes de refuerzo 1 (21:30-07:30): Nombre1, Nombre2, Nombre3, Nombre4\n"
        "  - Turno Retenes de refuerzo 2 (07:30-17:30): Nombre1, Nombre2, Nombre3, Nombre4\n"
        "  - Turno Retenes del Cabildo (12:30-21:30): Nombre1, Nombre2, Nombre3, Nombre4\n"
        "- Los nombres de los trabajadores deben estar separados por comas en una sola línea por turno.\n"
        "- No se deben incluir recomendaciones sobre el uso de software de planificación ni ningún comentario extra; "
        "solo la planificación.\n\n"

        "Datos de disponibilidad del personal:\n\n"
    )

    for trabajador in datos_trabajadores:
        pertenece_cabildo = "Sí" if trabajador.get('personalCabildo', False) else "No"
        estado = trabajador.get('estado', 'No especificado')
        prompt += f"Trabajador: {trabajador['nombre']} {trabajador['apellidos']}\n"
        prompt += f"Estado: {estado}\n"
        prompt += f"Pertenece al Cabildo: {pertenece_cabildo}\n"
        prompt += f"Disponibilidad: {json.dumps(trabajador['disponibilidad'], ensure_ascii=False)}\n"
        prompt += f"Excepciones: {json.dumps(trabajador.get('excepciones', {}), ensure_ascii=False)}\n\n"

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "Eres un asistente útil."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=2500,
        temperature=0.2
    )
    planificacion = response.choices[0].message.content.strip()

    return planificacion
