from flask import Flask, render_template, request, jsonify
import os
from leer_datos import leer_datos_json
from generar_planificaciones import generar_planificacion_trabajos_openai
from separar_planificaciones import separar_planificaciones
from convertir_tabla import convertir_a_tabla
from generar_html import generar_html_con_toggle
import pandas as pd
from datetime import datetime
import traceback

app = Flask(__name__)


# Función común para generar la planificación
def generar_planificacion_completa(fichero_json='trabajadores/disponibilidades.json',
                                   fichero_conf_json='configuracion.json'):
    try:
        datos_trabajadores = leer_datos_json(fichero_json)

        if not datos_trabajadores:
            mensaje = "No se encontraron trabajadores disponibles en el archivo JSON."
            print(mensaje)
            return None, None, None, None

        apikey = os.getenv("apikey")
        planificacion_texto = generar_planificacion_trabajos_openai(datos_trabajadores, apikey, fichero_conf_json)

        planificacion_incendio, planificacion_no_incendio = separar_planificaciones(planificacion_texto)

        try:
            planificacion_incendio_df = convertir_a_tabla(planificacion_incendio)
            print(f"Convertida planificación de incendio: {len(planificacion_incendio_df)} filas")
        except Exception as e:
            mensaje = f"Error al convertir planificación de incendio: {e}"
            print(mensaje)
            planificacion_incendio_df = pd.DataFrame(columns=['Fecha', 'Día', 'Turno', 'Trabajadores'])

        try:
            planificacion_no_incendio_df = convertir_a_tabla(planificacion_no_incendio)
            print(f"Convertida planificación de no incendio: {len(planificacion_no_incendio_df)} filas")
        except Exception as e:
            mensaje = f"Error al convertir planificación de no incendio: {e}"
            print(mensaje)
            planificacion_no_incendio_df = pd.DataFrame(columns=['Fecha', 'Día', 'Turno', 'Trabajadores'])

        hora_actual = datetime.now().time()
        html_content = generar_html_con_toggle(planificacion_incendio_df, planificacion_no_incendio_df, hora_actual)

        return planificacion_texto, planificacion_incendio_df, planificacion_no_incendio_df, html_content
    except Exception as e:
        print(f"Error en generar_planificacion_completa: {str(e)}")
        traceback.print_exc()
        return None, None, None, None


# Ruta para generar la planificación (modo web)
@app.route('/generar', methods=['POST'])
def generar_planificacion_web():
    try:
        # Siempre regenerar la planificación, independientemente de si el archivo existe
        print("Regenerando planificación...")
        planificacion_texto, planificacion_incendio_df, planificacion_no_incendio_df, html_content = generar_planificacion_completa()

        if html_content:
            # Asegúrate de que existe el directorio templates
            os.makedirs('templates', exist_ok=True)

            # Sobrescribir el archivo existente
            with open("templates/planificacion_turnos_interactiva.html", "w", encoding='utf-8') as f:
                f.write(html_content)

            # También guardamos en la raíz para mantener compatibilidad con el modo script
            with open("planificacion_turnos_interactiva.html", "w", encoding='utf-8') as f:
                f.write(html_content)

            print("Generación completada en modo web")
            return jsonify({'success': True, 'message': 'Planificación generada correctamente'})
        else:
            print("Error: No se generó el contenido HTML")
            return jsonify({'success': False, 'error': 'Error al generar el contenido HTML'}), 400
    except Exception as e:
        print(f"Error en la generación: {str(e)}")
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


# Ruta principal (modo web)
@app.route('/')
def index():
    try:
        # Verificar si existe el archivo html, si no, generarlo
        if not os.path.exists('templates/planificacion_turnos_interactiva.html'):
            _, _, _, html_content = generar_planificacion_completa()
            if html_content:
                os.makedirs('templates', exist_ok=True)
                with open("templates/planificacion_turnos_interactiva.html", "w", encoding='utf-8') as f:
                    f.write(html_content)
            else:
                # Si no se pudo generar el HTML, retornar un mensaje de error
                return "Error al generar la planificación inicial. Revise los logs para más detalles.", 500

        return render_template('planificacion_turnos_interactiva.html')
    except Exception as e:
        print(f"Error en index: {str(e)}")
        traceback.print_exc()
        return "Error al cargar la página. Revise los logs para más detalles.", 500


def main():
    # Asegurarse de que existe el directorio templates
    os.makedirs('templates', exist_ok=True)

    # Comprobar si el archivo HTML ya existe, si no, generarlo al inicio
    if not os.path.exists('templates/planificacion_turnos_interactiva.html'):
        print("Generando planificación inicial...")
        _, _, _, html_content = generar_planificacion_completa()
        if html_content:
            with open("templates/planificacion_turnos_interactiva.html", "w", encoding='utf-8') as f:
                f.write(html_content)
            with open("planificacion_turnos_interactiva.html", "w", encoding='utf-8') as f:
                f.write(html_content)
        else:
            print("ADVERTENCIA: No se pudo generar el HTML inicial")

    print("Iniciando en modo web. Accede a http://127.0.0.1:5000/")
    app.run(debug=True)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Error fatal al iniciar la aplicación: {str(e)}")
        traceback.print_exc()
