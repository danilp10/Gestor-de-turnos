import json
import openai
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
    openai.api_key = TOKEN_OPENAI

    prompt = (
        "Genera una planificación de turnos para los retenes contra incendios teniendo en cuenta las siguientes reglas:\n\n"
        "1. **Duración y Rotación de Turnos:**\n"
        "- Cada retén trabaja 12 horas efectivas en el incendio, con 14 horas en total considerando desplazamientos.\n"
        "- Se establecen dos turnos diarios:\n"
        "  - **Turno diurno:** 08:00 - 20:00 (salida a las 07:00, regreso a las 21:00).\n"
        "  - **Turno nocturno:** 20:00 - 08:00 (salida a las 19:00, regreso a las 09:00).\n"
        "- Los retenes trabajan en ciclos rotativos, alternando turnos y asegurando un descanso mínimo de 28 horas antes de reincorporarse.\n\n"

        "2. **Distribución de los Retenes:**\n"
        "- Hay 10 retenes disponibles.\n"
        "- 4 retenes estarán activos en cada turno, mientras los otros 6 descansan.\n"
        "- La rotación debe ser equitativa, evitando el agotamiento prolongado de los equipos.\n\n"
        
        "3. **Criterios de Ajuste y Flexibilidad:**\n"
        "- Si el incendio se prolonga, la secuencia de turnos se repite manteniendo el equilibrio entre trabajo y descanso.\n"
        "- Si algún retén muestra signos de desgaste excesivo, se pueden modificar rotaciones o agregar refuerzos.\n"
        "- Se prevé la posibilidad de realizar relevos dinámicos en función de la evolución del incendio.\n\n"

        "4. **Formato de Salida:**\n"
        "- Devuelve la planificación en formato tabular con columnas:\n"
        "  - Día\n"
        "  - Turno (Diurno/Nocturno)\n"
        "  - Retenes Asignados (lista de retenes activos)\n"
        "  - Retenes en Descanso (lista de retenes en descanso)\n"
        "- Asegúrate de mantener el ciclo de rotación correctamente.\n\n"

        "Aquí tienes la lista de retenes disponibles y su historial de turnos recientes:\n\n"
    )

    # Incluir los datos de los trabajadores en el prompt
    for trabajador in datos_trabajadores:
        prompt += f"Trabajador: {trabajador['nombre']} {trabajador['apellidos']}\n"
        prompt += f"Disponibilidad: {json.dumps(trabajador['disponibilidad'], ensure_ascii=False)}\n"
        prompt += f"Excepciones: {json.dumps(trabajador.get('excepciones', {}), ensure_ascii=False)}\n\n"

    response = openai.ChatCompletion.create(
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
