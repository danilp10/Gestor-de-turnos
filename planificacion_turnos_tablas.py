import json
import openai
import pandas as pd

# Configuración
TOKEN_OPENAI = 'tu_token_de_openai_aqui'
FICHERO_JSON = 'trabajadores/disponibilidades.json'

# Función para leer el archivo JSON
def leer_datos_json():
    try:
        with open(FICHERO_JSON, 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        print("El archivo JSON no se encuentra. Asegúrate de tener los datos guardados.")
        return []

# Función para enviar la solicitud a OpenAI y generar la planificación de turnos en texto
def generar_planificacion_trabajos_openai(datos_trabajadores):
    openai.api_key = TOKEN_OPENAI

    prompt = (
        "Con la siguiente información sobre los trabajadores y su disponibilidad, genera una planificación de turnos "
        "semanal. Organiza a los trabajadores según sus días y horas disponibles, teniendo en cuenta las excepciones "
        "como vacaciones y bajas. Si hay días no disponibles, asigna las horas restantes a los días libres.\n\n"
    )

    # Incluir los datos de los trabajadores en el prompt
    for trabajador in datos_trabajadores:
        prompt += f"Trabajador: {trabajador['nombre']} {trabajador['apellidos']}\n"
        prompt += f"Disponibilidad: {json.dumps(trabajador['disponibilidad'], ensure_ascii=False)}\n"
        prompt += f"Excepciones: {json.dumps(trabajador.get('excepciones', {}), ensure_ascii=False)}\n\n"

    # Solicitar la planificación de OpenAI
    response = openai.Completion.create(
        engine="gpt-4",
        prompt=prompt,
        max_tokens=1500,
        n=1,
        stop=None,
        temperature=0.2
    )

    planificacion = response.choices[0].text.strip()
    return planificacion

# Función para convertir la planificación generada por OpenAI en un DataFrame
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
