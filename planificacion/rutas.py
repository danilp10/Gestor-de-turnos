from flask import request, jsonify, redirect, render_template
import os
import json
from datetime import datetime
import traceback

from generadores.generar_html import generar_html_con_toggle
from planificacion.generador import generar_planificacion_completa
from planificacion.utilidades import cargar_planificaciones_existentes, guardar_planificaciones_temporales


def configurar_rutas_planificacion(app):
    """
    Configura las rutas relacionadas con la planificación en la aplicación Flask.
    """

    @app.route('/generar', methods=['POST'])
    def generar_planificacion_web():
        try:
            # Comprobar si existe el archivo de configuración
            if not os.path.exists('configuracion/configuracion.json'):
                return jsonify({
                    'success': False,
                    'error': 'Debe configurar los parámetros primero desde la página de configuración'
                }), 400

            if request.content_type and 'application/json' in request.content_type:
                request_data = request.get_json() or {}
            else:
                # Handle form data or empty request
                request_data = request.form.to_dict() or {}
            tipo_planificacion_solicitada = request_data.get('tipoPlanificacion', None)

            # Cargar planificaciones existentes para mantenerlas si es necesario
            planificacion_incendio_existente, planificacion_no_incendio_existente = cargar_planificaciones_existentes()

            # Si se especificó un tipo específico de planificación, modificar temporalmente la configuración
            configuracion_original = None
            if tipo_planificacion_solicitada in ['incendio', 'noIncendio']:
                try:
                    # Guardar la configuración original
                    with open('configuracion/configuracion.json', 'r', encoding='utf-8') as f:
                        configuracion_original = json.load(f)

                    # Crear una copia de la configuración original pero modificando el tipo de planificación
                    config_modificada = configuracion_original.copy()
                    config_modificada['tipoPlanificacion'] = tipo_planificacion_solicitada

                    # Guardar temporalmente la configuración modificada
                    with open('configuracion/configuracion.json', 'w', encoding='utf-8') as f:
                        json.dump(config_modificada, f, indent=2, ensure_ascii=False)

                    print(
                        f"Configuración modificada temporalmente para generar solo planificación de {tipo_planificacion_solicitada}")
                except Exception as e:
                    print(f"Error al modificar la configuración: {str(e)}")
                    # Si hay error, continuamos con la configuración original

            # Regenerar la planificación con la configuración actual
            print("Regenerando planificación...")
            planificacion_texto, planificacion_incendio_df, planificacion_no_incendio_df, _ = generar_planificacion_completa()

            # Restaurar la configuración original si fue modificada
            if configuracion_original is not None:
                try:
                    with open('configuracion/configuracion.json', 'w', encoding='utf-8') as f:
                        json.dump(configuracion_original, f, indent=2, ensure_ascii=False)
                    print("Configuración original restaurada")
                except Exception as e:
                    print(f"Error al restaurar la configuración original: {str(e)}")

            # NUEVO: Conservar la otra planificación si solo se regeneró una
            if tipo_planificacion_solicitada == 'incendio' and not planificacion_no_incendio_df.empty and not planificacion_no_incendio_existente.empty:
                planificacion_no_incendio_df = planificacion_no_incendio_existente
                print("Se conservó la planificación de no incendio existente")
            elif tipo_planificacion_solicitada == 'noIncendio' and not planificacion_incendio_df.empty and not planificacion_incendio_existente.empty:
                planificacion_incendio_df = planificacion_incendio_existente
                print("Se conservó la planificación de incendio existente")

            # Guardar las planificaciones en archivos temporales para futuras regeneraciones parciales
            guardar_planificaciones_temporales(planificacion_incendio_df, planificacion_no_incendio_df)

            # Generar el HTML final con ambas planificaciones (la regenerada y la conservada)
            hora_actual = datetime.now().time()
            html_content = generar_html_con_toggle(planificacion_incendio_df, planificacion_no_incendio_df, hora_actual)

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

    @app.route('/planificacion')
    def ver_planificacion():
        try:
            # Verify if HTML file exists
            if not os.path.exists('templates/planificacion_turnos_interactiva.html'):
                return redirect('/')

            return render_template('planificacion_turnos_interactiva.html')
        except Exception as e:
            print(f"Error al mostrar planificación: {str(e)}")
            traceback.print_exc()
            return "Error al cargar la planificación. Revise los logs para más detalles.", 500
