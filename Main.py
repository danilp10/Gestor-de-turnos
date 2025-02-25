import os

from leer_datos import leer_datos_json
from generar_planificaciones import generar_planificacion_trabajos_openai
from separar_planificaciones import separar_planificaciones
from convertir_tabla import convertir_a_tabla
from generar_html import generar_html_con_toggle
import pandas as pd


def main():
    fichero_json = 'trabajadores/disponibilidades.json'
    datos_trabajadores = leer_datos_json(fichero_json)

    if not datos_trabajadores:
        print("No se encontraron trabajadores disponibles en el archivo JSON.")
        return

    apikey = os.getenv("apikey")
    planificacion_texto = generar_planificacion_trabajos_openai(datos_trabajadores, apikey)

    planificacion_incendio, planificacion_no_incendio = separar_planificaciones(planificacion_texto)

    print("\nPlanificación en Caso de Incendio (Texto):\n")
    print(planificacion_incendio)

    print("\nPlanificación en Caso de No Incendio (Texto):\n")
    print(planificacion_no_incendio)

    print("Convirtiendo planificaciones a formato tabular...")
    try:
        planificacion_incendio_df = convertir_a_tabla(planificacion_incendio)
        print(f"Convertida planificación de incendio: {len(planificacion_incendio_df)} filas")
    except Exception as e:
        print(f"Error al convertir planificación de incendio: {e}")
        planificacion_incendio_df = pd.DataFrame(columns=['Fecha', 'Día', 'Turno', 'Trabajadores'])

    try:
        planificacion_no_incendio_df = convertir_a_tabla(planificacion_no_incendio)
        print(f"Convertida planificación de no incendio: {len(planificacion_no_incendio_df)} filas")
    except Exception as e:
        print(f"Error al convertir planificación de no incendio: {e}")
        planificacion_no_incendio_df = pd.DataFrame(columns=['Fecha', 'Día', 'Turno', 'Trabajadores'])

    print("Generando HTML interactivo...")
    html_content = generar_html_con_toggle(planificacion_incendio_df, planificacion_no_incendio_df)

    filename = "planificacion_turnos_interactiva.html"
    with open(filename, "w", encoding='utf-8') as f:
        f.write(html_content)

    print(f"\nLa planificación de turnos ha sido guardada como archivo HTML interactivo: {filename}")


if __name__ == "__main__":
    main()
