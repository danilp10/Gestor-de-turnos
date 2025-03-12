from flask import render_template, request, jsonify
import os
import json
import traceback


def configurar_rutas_configuracion(app):
    """
    Configura las rutas relacionadas con la configuración en la aplicación Flask.
    """

    @app.route('/configuracion')
    def configuracion():
        try:
            return render_template('configuracion.html')
        except Exception as e:
            print(f"Error al cargar la página de configuración: {str(e)}")
            traceback.print_exc()
            return "Error al cargar la página de configuración. Revise los logs para más detalles.", 500

    @app.route('/configuracion', methods=['POST'])
    def guardar_configuracion():
        try:
            config = request.get_json()

            # Validate configuration
            if not config:
                return jsonify({
                    'status': 'error',
                    'mensaje': 'Configuración inválida'
                }), 400

            # Get planning type
            tipo_planificacion = config.get('tipoPlanificacion', 'ambos')

            # Initialize processed configuration with planning type
            configuracion_procesada = {
                'tipoPlanificacion': tipo_planificacion
            }

            # Validate fire configuration if needed
            if tipo_planificacion in ['ambos', 'incendio']:
                if not config.get('incendio'):
                    return jsonify({
                        'status': 'error',
                        'mensaje': 'Falta configuración para caso de incendio'
                    }), 400

                configuracion_procesada['incendio'] = {
                    'dias': int(config['incendio']['dias']),
                    'fechaInicio': config['incendio']['fechaInicio'],
                    'turnoDiurno': int(config['incendio']['turnoDiurno']),
                    'turnoNocturno': int(config['incendio']['turnoNocturno'])
                }

            # Validate non-fire configuration if needed
            if tipo_planificacion in ['ambos', 'noIncendio']:
                if not config.get('noIncendio'):
                    return jsonify({
                        'status': 'error',
                        'mensaje': 'Falta configuración para caso de no incendio'
                    }), 400

                configuracion_procesada['noIncendio'] = {
                    'dias': int(config['noIncendio']['dias']),
                    'fechaInicio': config['noIncendio']['fechaInicio'],
                    'cabildoPersonas': int(config['noIncendio']['cabildoPersonas']),
                    'retenes': [
                        {
                            'turno': int(reten['turno']),
                            'personas': int(reten['personas'])
                        } for reten in config['noIncendio']['retenes']
                    ]
                }

            # Save to JSON file
            with open('configuracion/configuracion.json', 'w', encoding='utf-8') as f:
                json.dump(configuracion_procesada, f, indent=2, ensure_ascii=False)

            return jsonify({
                'status': 'ok',
                'mensaje': 'Configuración guardada con éxito',
                'configuracion': configuracion_procesada
            })

        except Exception as e:
            print(f"Error al guardar la configuración: {str(e)}")
            traceback.print_exc()
            return jsonify({
                'status': 'error',
                'mensaje': 'Error interno del servidor',
                'detalles': str(e)
            }), 500

    @app.route('/configuracion/json', methods=['GET'])
    def obtener_configuracion():
        try:
            if os.path.exists('configuracion/configuracion.json'):
                with open('configuracion/configuracion.json', 'r', encoding='utf-8') as f:
                    config = json.load(f)

                # Add content type header explicitly
                response = jsonify({
                    'status': 'ok',
                    'configuracion': config
                })
                response.headers['Content-Type'] = 'application/json'
                return response
            else:
                response = jsonify({
                    'status': 'error',
                    'mensaje': 'No se ha guardado ninguna configuración aún'
                })
                response.headers['Content-Type'] = 'application/json'
                return response, 404

        except Exception as e:
            print(f"Error al obtener la configuración: {str(e)}")
            traceback.print_exc()
            response = jsonify({
                'status': 'error',
                'mensaje': 'Error interno del servidor',
                'detalles': str(e)
            })
            response.headers['Content-Type'] = 'application/json'
            return response, 500
