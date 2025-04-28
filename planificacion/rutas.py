from flask import request, jsonify, redirect, render_template
import os
import json
from datetime import datetime
import traceback

from generadores.generar_html import generar_html_con_toggle
from planificacion.generador import generar_planificacion_completa
from planificacion.utilidades import cargar_planificaciones_existentes, guardar_planificaciones_temporales
from validaciones.verificar_planificacion_genereda import (
    cargar_datos_usuarios,
    cargar_planificacion_desde_csv,
    validar_planificacion,
    exportar_resultados_json
)


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
                        f"Configuración modificada temporalmente para generar solo planificación de "
                        f"{tipo_planificacion_solicitada}")
                except Exception as e:
                    print(f"Error al modificar la configuración: {str(e)}")
                    # Si hay error, continuamos con la configuración original

            # Regenerar la planificación con la configuración actual
            print("Generando planificación estándar...")
            planificacion_texto, planificacion_incendio_df, planificacion_no_incendio_df, prompt, _ \
                = generar_planificacion_completa()

            # Restaurar la configuración original si fue modificada
            if configuracion_original is not None:
                try:
                    with open('configuracion/configuracion.json', 'w', encoding='utf-8') as f:
                        json.dump(configuracion_original, f, indent=2, ensure_ascii=False)
                    print("Configuración original restaurada")
                except Exception as e:
                    print(f"Error al restaurar la configuración original: {str(e)}")

            # Conservar la otra planificación si solo se regeneró una
            if (tipo_planificacion_solicitada == 'incendio' and not planificacion_no_incendio_df.empty and not
                planificacion_no_incendio_existente.empty):
                planificacion_no_incendio_df = planificacion_no_incendio_existente
                print("Se conservó la planificación de no incendio existente")
            elif (tipo_planificacion_solicitada == 'noIncendio' and not planificacion_incendio_df.empty and not
                  planificacion_incendio_existente.empty):
                planificacion_incendio_df = planificacion_incendio_existente
                print("Se conservó la planificación de incendio existente")

            # Guardar las planificaciones en archivos temporales para futuras regeneraciones parciales
            guardar_planificaciones_temporales(planificacion_incendio_df, planificacion_no_incendio_df)

            # Validar planificaciones automáticamente
            print("Validando planificaciones generadas...")
            validar_planificaciones_generadas()

            # Generar el HTML final con ambas planificaciones (la regenerada y la conservada)
            hora_actual = datetime.now().time()
            html_content = generar_html_con_toggle(planificacion_incendio_df, planificacion_no_incendio_df,
                                                   hora_actual, prompt=prompt)

            if html_content:
                # Asegúrate de que existe el directorio templates
                os.makedirs('templates', exist_ok=True)

                # Sobrescribir el archivo existente
                with open("templates/planificacion_turnos_interactiva.html", "w", encoding='utf-8') as f:
                    f.write(html_content)

                print("Generación completada en modo web")
                return jsonify({'success': True, 'message': 'Planificación generada y validada correctamente'})
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
            if not os.path.exists('templates/planificacion_turnos_interactiva.html'):
                return redirect('/')

            return render_template('planificacion_turnos_interactiva.html')
        except Exception as e:
            print(f"Error al mostrar planificación: {str(e)}")
            traceback.print_exc()
            return "Error al cargar la planificación. Revise los logs para más detalles.", 500

    @app.route('/regenerar', methods=['POST'])
    def regenerar_planificacion():
        try:
            if request.content_type and 'application/json' in request.content_type:
                request_data = request.get_json() or {}
            else:
                request_data = request.form.to_dict() or {}
            tipo_planificacion_solicitada = request_data.get('tipoPlanificacion', None)

            # Verificar si se está solicitando rehacer la planificación con resultados de validación
            rehacer_con_validacion = request_data.get('rehacerConValidacion', False)
            resultados_validacion = None

            # Si se está rehaciendo con validación, cargar los resultados de validación
            if rehacer_con_validacion:
                ruta_validacion = 'validaciones/resultados_validacion.json'
                if os.path.exists(ruta_validacion):
                    try:
                        with open(ruta_validacion, 'r', encoding='utf-8') as f:
                            resultados_validacion = json.load(f)
                        print("Cargados resultados de validación para rehacer la planificación")
                    except Exception as e:
                        print(f"Error al cargar resultados_validacion.json: {str(e)}")

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
                        f"Configuración modificada temporalmente para generar solo planificación de "
                        f"{tipo_planificacion_solicitada}")
                except Exception as e:
                    print(f"Error al modificar la configuración: {str(e)}")
                    # Si hay error, continuamos con la configuración original

            # Regenerar la planificación con la configuración actual
            print("Regenerando planificación...")

            # Pasar los resultados_validacion a la función generar_planificacion_completa
            planificacion_texto, planificacion_incendio_df, planificacion_no_incendio_df, prompt, _ \
                = generar_planificacion_completa(resultados_validacion=resultados_validacion)

            # Restaurar la configuración original si fue modificada
            if configuracion_original is not None:
                try:
                    with open('configuracion/configuracion.json', 'w', encoding='utf-8') as f:
                        json.dump(configuracion_original, f, indent=2, ensure_ascii=False)
                    print("Configuración original restaurada")
                except Exception as e:
                    print(f"Error al restaurar la configuración original: {str(e)}")

            # Conservar la otra planificación si solo se regeneró una
            if (tipo_planificacion_solicitada == 'incendio' and not planificacion_no_incendio_df.empty and not
            planificacion_no_incendio_existente.empty):
                planificacion_no_incendio_df = planificacion_no_incendio_existente
                print("Se conservó la planificación de no incendio existente")
            elif (tipo_planificacion_solicitada == 'noIncendio' and not planificacion_incendio_df.empty and not
            planificacion_incendio_existente.empty):
                planificacion_incendio_df = planificacion_incendio_existente
                print("Se conservó la planificación de incendio existente")

            # Guardar las planificaciones en archivos temporales para futuras regeneraciones parciales
            guardar_planificaciones_temporales(planificacion_incendio_df, planificacion_no_incendio_df)

            # Validar planificaciones automáticamente
            print("Validando planificaciones regeneradas...")
            validar_planificaciones_generadas()

            # Generar el HTML final con ambas planificaciones (la regenerada y la conservada)
            hora_actual = datetime.now().time()
            html_content = generar_html_con_toggle(planificacion_incendio_df, planificacion_no_incendio_df,
                                                   hora_actual, prompt=prompt)

            if html_content:
                # Asegúrate de que existe el directorio templates
                os.makedirs('templates', exist_ok=True)

                # Sobrescribir el archivo existente
                with open("templates/planificacion_turnos_interactiva.html", "w", encoding='utf-8') as f:
                    f.write(html_content)

                print("Regeneración completada")
                return jsonify({'success': True, 'message': 'Planificación regenerada y validada correctamente'})
            else:
                print("Error: No se generó el contenido HTML")
                return jsonify({'success': False, 'error': 'Error al generar el contenido HTML'}), 400
        except Exception as e:
            print(f"Error en la regeneración: {str(e)}")
            traceback.print_exc()
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/resultados-validacion')
    def ver_resultados_validacion():
        try:
            ruta_resultados = 'validaciones/resultados_validacion.json'

            if not os.path.exists(ruta_resultados):
                return jsonify({
                    'success': False,
                    'error': 'No hay resultados de validación disponibles'
                }), 404

            with open(ruta_resultados, 'r', encoding='utf-8') as f:
                resultados = json.load(f)

            return jsonify({
                'success': True,
                'resultados': resultados
            })
        except Exception as e:
            print(f"Error al obtener resultados de validación: {str(e)}")
            traceback.print_exc()
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500


def validar_planificaciones_generadas():
    """
    Función auxiliar para validar automáticamente las planificaciones generadas
    y guardar los resultados en un archivo JSON.
    """
    try:
        disponibilidades = 'trabajadores/disponibilidades.json'
        planificacion_no_incendio = "planificaciones_generadas/temp_planificacion_no_incendio.csv"
        planificacion_incendio = "planificaciones_generadas/temp_planificacion_incendio.csv"
        ruta_resultados_json = "validaciones/resultados_validacion.json"

        os.makedirs(os.path.dirname(ruta_resultados_json), exist_ok=True)

        usuarios = cargar_datos_usuarios(disponibilidades)

        print("Validando planificación sin incendio...")
        plan_no_incendio = cargar_planificacion_desde_csv(planificacion_no_incendio)
        resultados_no_incendio = validar_planificacion(usuarios, plan_no_incendio, es_incendio=False)

        print("Validando planificación con incendio...")
        plan_incendio = cargar_planificacion_desde_csv(planificacion_incendio)
        resultados_incendio = validar_planificacion(usuarios, plan_incendio, es_incendio=True)

        exportar_resultados_json(resultados_no_incendio, resultados_incendio, ruta_resultados_json)

        print("Validación completada y resultados guardados en:", ruta_resultados_json)
        return True
    except Exception as e:
        print(f"Error durante la validación: {str(e)}")
        traceback.print_exc()
        return False
