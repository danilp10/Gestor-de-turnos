from flask import Flask, render_template, request, jsonify
import os
from leer_datos import leer_datos_json
from generar_planificaciones import generar_planificacion_trabajos_openai
from separar_planificaciones import separar_planificaciones
from convertir_tabla import convertir_a_tabla
from generar_html import generar_html_con_toggle
import pandas as pd
from datetime import datetime

app = Flask(__name__)

# Ruta para generar la planificación
@app.route('/generar', methods=['POST'])
def generar_planificacion():
    fichero_json = 'trabajadores/disponibilidades.json'
    datos_trabajadores = leer_datos_json(fichero_json)

    if not datos_trabajadores:
        return jsonify({'error': 'No se encontraron trabajadores disponibles en el archivo JSON.'})

    apikey = os.getenv("apikey")
    planificacion_texto = generar_planificacion_trabajos_openai(datos_trabajadores, apikey)

    planificacion_incendio, planificacion_no_incendio = separar_planificaciones(planificacion_texto)

    try:
        planificacion_incendio_df = convertir_a_tabla(planificacion_incendio)
    except Exception:
        planificacion_incendio_df = pd.DataFrame(columns=['Fecha', 'Día', 'Turno', 'Trabajadores'])

    try:
        planificacion_no_incendio_df = convertir_a_tabla(planificacion_no_incendio)
    except Exception:
        planificacion_no_incendio_df = pd.DataFrame(columns=['Fecha', 'Día', 'Turno', 'Trabajadores'])

    hora_actual = datetime.now().time()
    html_content = generar_html_con_toggle(planificacion_incendio_df, planificacion_no_incendio_df, hora_actual)

    with open("templates/planificacion_turnos_interactiva.html", "w", encoding='utf-8') as f:
        f.write(html_content)

    return jsonify({'success': True})

# Ruta principal
@app.route('/')
def index():
    return render_template('planificacion_turnos_interactiva.html')

if __name__ == '__main__':
    app.run(debug=True)
