import json
from openai import OpenAI
import os
import pandas as pd

TOKEN_OPENAI = os.getenv("apikey")
FICHERO_JSON = 'trabajadores/disponibilidades.json'


def leer_datos_json():
    try:
        with open(FICHERO_JSON, 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        print("El archivo JSON no se encuentra. Asegúrate de tener los datos guardados.")
        return []


def generar_planificacion_trabajos_openai(datos_trabajadores):
    client = OpenAI(api_key=TOKEN_OPENAI)

    prompt = (
        "Genera una planificación detallada de turnos para los retenes contra incendios para los próximos 7 días a partir de la fecha actual. "
        "Sigue estrictamente las siguientes reglas y no incluyas comentarios, advertencias ni recomendaciones adicionales:\n\n"

        "1. **Período de Planificación:**\n"
        "- La planificación debe abarcar exactamente los próximos 7 días a partir de la fecha actual.\n\n"

        "2. **Retenes Disponibles y Disponibilidad:**\n"
        "- Cada turno debe contar con 4 retenes trabajando; el resto descansan.\n"
        "- Excluye de la planificación a los trabajadores que se encuentren en estado de baja o de vacaciones.\n"
        "- En caso de incendio, incluye como disponibles a los trabajadores que estén de vacaciones, pero siempre excluye a los de baja.\n"
        "- Considera que hay 11 retenes del Cabildo y 11 retenes de refuerzo (Gesplan).\n\n"

        "3. **Turnos en Incendio:**\n"
        "- **Turno Diurno:** 08:00 - 20:00 (salida a las 07:00, regreso a las 21:00).\n"
        "- **Turno Nocturno:** 20:00 - 08:00 (salida a las 19:00, regreso a las 09:00).\n"
        "- La asignación de turnos nocturnos debe seguir la rotación exacta: **Noche, noche, descanso, mañana, mañana, descanso, noche, noche, descanso...**.\n\n"

        "4. **Criterios de Estado de Fatiga:**\n"
        "- **Verde:** Quedan de 8 a 12 horas de trabajo.\n"
        "- **Amarillo:** Quedan de 6 a 8 horas de trabajo.\n"
        "- **Naranja:** Quedan de 2 a 4 horas de trabajo.\n"
        "- **Rojo:** Quedan menos de 2 horas de trabajo.\n\n"

        "5. **Formato y Detalle de la Respuesta:**\n"
        "- La respuesta debe incluir, para cada uno de los 7 días, los turnos diurnos y nocturnos con los nombres de los retenes asignados.\n"
        "- Se debe detallar claramente qué trabajadores tienen asignado cada turno, indicando la fecha, el turno (diurno o nocturno) y los nombres completos de los retenes.\n"
        "- No se deben incluir recomendaciones sobre el uso de software de planificación ni ningún comentario extra; solo la planificación.\n\n"

        "Datos de disponibilidad del personal:\n\n"
    )

    # Incluir los datos de los trabajadores en el prompt
    for trabajador in datos_trabajadores:
        prompt += f"Trabajador: {trabajador['nombre']} {trabajador['apellidos']}\n"
        prompt += f"Disponibilidad: {json.dumps(trabajador['disponibilidad'], ensure_ascii=False)}\n"
        prompt += f"Excepciones: {json.dumps(trabajador.get('excepciones', {}), ensure_ascii=False)}\n\n"

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "Eres un asistente útil."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=1500,
        temperature=0.2
    )
    planificacion = response.choices[0].message.content.strip()

    return planificacion


def convertir_a_tabla(planificacion):
    # Separar la planificación en líneas y extraer los turnos
    lineas = planificacion.split('\n')
    turnos = []
    trabajador = None
    for linea in lineas:
        if linea.startswith("Trabajador:"):
            if trabajador:
                turnos.append(trabajador)
            trabajador = {'Trabajador': linea.replace("Trabajador: ", "")}
        elif "Disponibilidad:" in linea:
            # Asumimos que la disponibilidad viene en un formato tipo diccionario
            disponibilidad = eval(linea.replace("Disponibilidad: ", ""))
            for dia, horas in disponibilidad.items():
                trabajador[dia] = f"{horas['entrada']} - {horas['salida']}"
    if trabajador:
        turnos.append(trabajador)

    # Crear un DataFrame con los turnos
    df_turnos = pd.DataFrame(turnos)
    return df_turnos


# Función principal
def main():
    # Leer los datos del archivo JSON
    datos_trabajadores = leer_datos_json()

    if not datos_trabajadores:
        print("No se encontraron trabajadores disponibles en el archivo JSON.")
        return

    # Generar la planificación de turnos con OpenAI
    planificacion = generar_planificacion_trabajos_openai(datos_trabajadores)

    print("\nPlanificación Generada (Texto):\n")
    print(planificacion)

    # Convertir la planificación en tabla
    planificacion_df = convertir_a_tabla(planificacion)

    # Mostrar la tabla en consola
    print("\nPlanificación de Turnos (Tabla):\n")
    print(planificacion_df)

    # Opcional: Guardar la tabla como archivo HTML
    planificacion_df.to_html("planificacion_turnos.html", index=False)
    print("\nLa planificación de turnos ha sido guardada como archivo HTML.")


if __name__ == "__main__":
    main()
