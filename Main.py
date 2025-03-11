from flask import Flask, render_template, request, jsonify,redirect
import os
import json
from datetime import datetime
from leer_datos import leer_datos_json
from generar_planificaciones import generar_planificacion_trabajos_openai
from separar_planificaciones import separar_planificaciones
from convertir_tabla import convertir_a_tabla
from generar_html import generar_html_con_toggle
import pandas as pd
import traceback
import shutil
app = Flask(__name__)

# Archivos de datos
DATA_FILE = "trabajadores/disponibilidades.json"


# Funciones de utilidad (sin cambios)
def leer_datos():
    try:
        if not os.path.exists(DATA_FILE):
            # Si el archivo no existe, crearlo con un array vacío
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                json.dump([], f)
            return []
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error al leer datos: {e}")
        return []


def guardar_datos(datos):
    try:
        # Asegurar que el directorio existe
        os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(datos, f, indent=2, ensure_ascii=False)
        print("Datos guardados correctamente")
        return True
    except Exception as e:
        print(f"Error al guardar datos: {e}")
        return False


def determinar_estado(reincorporacion, vacaciones):
    fecha_actual = datetime.today().date()

    if vacaciones and vacaciones.get("inicio") and vacaciones.get("fin"):
        inicio_vac = datetime.strptime(vacaciones["inicio"], "%Y-%m-%d").date()
        fin_vac = datetime.strptime(vacaciones["fin"], "%Y-%m-%d").date()
        if inicio_vac <= fecha_actual <= fin_vac:
            return "vacaciones"

    if not reincorporacion:
        return "activo"

    reincorporacion_date = datetime.strptime(reincorporacion, "%Y-%m-%d").date()
    return "baja" if reincorporacion_date > fecha_actual else "activo"


def actualizar_estados_iniciales():
    trabajadores = leer_datos()
    fecha_actual = datetime.today().date()

    cambios = False
    for trabajador in trabajadores:
        if "excepciones" in trabajador:
            reincorporacion = trabajador["excepciones"].get("reincorporacion")
            vacaciones = trabajador["excepciones"].get("vacaciones")

            try:
                # Procesamiento de fechas con manejo de errores
                fecha_reincorporacion = None
                fecha_inicio_vacaciones = None
                fecha_fin_vacaciones = None

                if reincorporacion:
                    fecha_reincorporacion = datetime.strptime(reincorporacion, "%Y-%m-%d").date()

                if vacaciones and vacaciones.get("inicio"):
                    fecha_inicio_vacaciones = datetime.strptime(vacaciones["inicio"], "%Y-%m-%d").date()

                if vacaciones and vacaciones.get("fin"):
                    fecha_fin_vacaciones = datetime.strptime(vacaciones["fin"], "%Y-%m-%d").date()

                # Caso 1: Hoy comienzan las vacaciones
                if fecha_inicio_vacaciones and fecha_inicio_vacaciones == fecha_actual:
                    if trabajador.get("estado") != "vacaciones":
                        trabajador["estado"] = "vacaciones"
                        cambios = True
                        print(
                            f"Trabajador {trabajador['id']} actualizado a VACACIONES (Inicio: {vacaciones['inicio']})")

                # Caso 2: Verificar si está de vacaciones
                elif fecha_inicio_vacaciones and fecha_fin_vacaciones:
                    if fecha_inicio_vacaciones <= fecha_actual <= fecha_fin_vacaciones:
                        if trabajador.get("estado") != "vacaciones":
                            trabajador["estado"] = "vacaciones"
                            cambios = True
                            print(f"Trabajador {trabajador['id']} actualizado a VACACIONES (Durante periodo)")
                    elif fecha_actual > fecha_fin_vacaciones and trabajador.get("estado") == "vacaciones":
                        # Fin de vacaciones
                        trabajador["estado"] = "activo"
                        trabajador["excepciones"]["vacaciones"] = None
                        cambios = True
                        print(f"Trabajador {trabajador['id']} actualizado a ACTIVO (Fin de vacaciones)")

                # Caso 3: Verificar reincorporación
                if fecha_reincorporacion and fecha_actual >= fecha_reincorporacion and trabajador.get(
                        "estado") == "baja":
                    trabajador["estado"] = "activo"
                    trabajador["excepciones"]["reincorporacion"] = None
                    cambios = True
                    print(f"Trabajador {trabajador['id']} actualizado a ACTIVO (Reincorporación alcanzada)")

            except ValueError as e:
                print(f"Error al procesar fechas para trabajador {trabajador['id']}: {e}")

    if cambios:
        exito = guardar_datos(trabajadores)
        if exito:
            print("Estados actualizados según la fecha actual.")
        else:
            print("Error al guardar los estados actualizados.")
    else:
        print("No se encontraron cambios en los estados de los trabajadores.")



actualizar_estados_iniciales()

# Rutas de API
@app.route('/api/trabajadores', methods=['GET'])
def obtener_trabajadores():
    trabajadores = leer_datos()
    return jsonify({
        "status": "ok",
        "total": len(trabajadores),
        "trabajadores": trabajadores
    })


@app.route('/api/trabajadores/<id>', methods=['GET'])
def obtener_trabajador(id):
    trabajadores = leer_datos()
    trabajador = next((t for t in trabajadores if str(t["id"]) == str(id)), None)
    if not trabajador:
        return jsonify({"status": "error", "mensaje": "Trabajador no encontrado"}), 404
    return jsonify(trabajador)


@app.route('/api/trabajadores', methods=['POST'])
def agregar_trabajador():
    try:
        datos = request.get_json()

        # Validar campos obligatorios
        if not datos.get("id") or not datos.get("nombre") or not datos.get("apellidos"):
            return jsonify({
                "status": "error",
                "mensaje": "Faltan campos obligatorios (id, nombre, apellidos)"
            }), 400

        trabajadores = leer_datos()

        # Validar que el ID no exista
        if any(str(t["id"]) == str(datos["id"]) for t in trabajadores):
            return jsonify({
                "status": "error",
                "tipo": "ID_DUPLICADO",
                "mensaje": "Ya existe un trabajador con este ID"
            }), 409

        # Aseguramos que ID sea un entero
        datos["id"] = str(datos["id"])  # Convertir a string para consistencia con server.js

        # Determinamos el estado inicial
        datos["estado"] = determinar_estado(
            datos.get("excepciones", {}).get("reincorporacion"),
            datos.get("excepciones", {}).get("vacaciones")
        )

        # Calculamos los días no disponibles si hay disponibilidad
        if "disponibilidad" in datos:
            todos_dias = ['lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado', 'domingo']
            datos["diasNoDisponibles"] = [dia for dia in todos_dias if dia not in datos["disponibilidad"]]

        # Añadimos timestamp de creación
        datos["timestamp"] = datetime.now().isoformat()

        # Agregar el trabajador a la lista
        trabajadores.append(datos)

        # Guardar los datos
        if guardar_datos(trabajadores):
            print(f"Trabajador con ID {datos['id']} agregado correctamente")
            return jsonify({
                "status": "ok",
                "mensaje": "Trabajador agregado correctamente",
                "datos": datos
            })
        else:
            return jsonify({
                "status": "error",
                "mensaje": "Error al guardar los datos"
            }), 500

    except Exception as e:
        print(f"Error al agregar trabajador: {e}")
        return jsonify({
            "status": "error",
            "mensaje": f"Error: {str(e)}"
        }), 500


@app.route('/api/trabajadores/<id>', methods=['PUT'])
def actualizar_trabajador(id):
    try:
        datos = request.get_json()
        trabajadores = leer_datos()
        index = next((i for i, t in enumerate(trabajadores) if str(t["id"]) == str(id)), -1)

        if index == -1:
            return jsonify({"status": "error", "mensaje": "Trabajador no encontrado"}), 404

        # Mantener el ID original
        datos["id"] = id

        # Calcular días no disponibles si hay disponibilidad
        if "disponibilidad" in datos:
            todos_dias = ['lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado', 'domingo']
            datos["diasNoDisponibles"] = [dia for dia in todos_dias if dia not in datos["disponibilidad"]]

        # Calcular el estado
        datos["estado"] = determinar_estado(
            datos.get("excepciones", {}).get("reincorporacion"),
            datos.get("excepciones", {}).get("vacaciones")
        )

        # Actualizar timestamp
        datos["timestamp"] = datetime.now().isoformat()

        # Preservar datos que no se están actualizando
        trabajador_actualizado = {**trabajadores[index], **datos}
        trabajadores[index] = trabajador_actualizado

        # Guardar los cambios
        if guardar_datos(trabajadores):
            print(f"Trabajador con ID {id} actualizado correctamente")
            return jsonify({
                "status": "ok",
                "mensaje": "Trabajador actualizado correctamente",
                "datos": trabajador_actualizado
            })
        else:
            return jsonify({
                "status": "error",
                "mensaje": "Error al guardar los datos actualizados"
            }), 500

    except Exception as e:
        print(f"Error al actualizar trabajador: {e}")
        return jsonify({
            "status": "error",
            "mensaje": f"Error: {str(e)}"
        }), 500


# Ruta principal con menú de opciones
@app.route('/')
def index():
    return render_template('inicio.html')


# Página de gestión de trabajadores
@app.route('/trabajadores')
def trabajadores():
    return render_template('gestionar_retenes.html')

# Página de configuración de planificación
@app.route('/configuracion')
def configuracion():
    try:
        return render_template('configuracion.html')
    except Exception as e:
        print(f"Error al cargar la página de configuración: {str(e)}")
        traceback.print_exc()
        return "Error al cargar la página de configuración. Revise los logs para más detalles.", 500

# Save configuration route
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
        with open('configuracion.json', 'w', encoding='utf-8') as f:
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

# Get saved configuration route
@app.route('/configuracion/json', methods=['GET'])
def obtener_configuracion():
    try:
        if os.path.exists('configuracion.json'):
            with open('configuracion.json', 'r', encoding='utf-8') as f:
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

        # Cargar la configuración para determinar el tipo de planificación
        try:
            with open(fichero_conf_json, 'r', encoding='utf-8') as f:
                config = json.load(f)
                tipo_planificacion = config.get('tipoPlanificacion', 'ambos')
                # Cargar las configuraciones específicas
                incendio_config = config.get('incendio', {})
                no_incendio_config = config.get('noIncendio', {})
        except Exception as e:
            print(f"Error al leer el tipo de planificación: {e}")
            tipo_planificacion = 'ambos'  # Valor por defecto
            incendio_config = {}
            no_incendio_config = {}

        # Inicializar dataframes vacíos
        planificacion_incendio_df = pd.DataFrame(columns=['Fecha', 'Día', 'Turno', 'Trabajadores'])
        planificacion_no_incendio_df = pd.DataFrame(columns=['Fecha', 'Día', 'Turno', 'Trabajadores'])

        # Procesar según el tipo de planificación
        if tipo_planificacion in ['ambos', 'incendio', 'noIncendio']:
            planificacion_incendio = ""
            planificacion_no_incendio = ""

            # Si es ambos, separar las planificaciones
            if tipo_planificacion == 'ambos':
                planificacion_incendio, planificacion_no_incendio = separar_planificaciones(planificacion_texto)
            # Si es solo incendio
            elif tipo_planificacion == 'incendio':
                planificacion_incendio = planificacion_texto
            # Si es solo no incendio
            else:
                planificacion_no_incendio = planificacion_texto

            # Procesar planificación de incendio si es necesario
            if tipo_planificacion in ['ambos', 'incendio'] and planificacion_incendio:
                try:
                    # Pasar la fecha de inicio correctamente
                    fecha_inicio_incendio = incendio_config.get('fechaInicio')
                    planificacion_incendio_df = convertir_a_tabla(planificacion_incendio,
                                                                  fecha_inicio_str=fecha_inicio_incendio)
                    print(f"Convertida planificación de incendio: {len(planificacion_incendio_df)} filas")
                except Exception as e:
                    mensaje = f"Error al convertir planificación de incendio: {e}"
                    print(mensaje)

            # Procesar planificación de no incendio si es necesario
            if tipo_planificacion in ['ambos', 'noIncendio'] and planificacion_no_incendio:
                try:
                    # Pasar la fecha de inicio correctamente
                    fecha_inicio_no_incendio = no_incendio_config.get('fechaInicio')
                    planificacion_no_incendio_df = convertir_a_tabla(planificacion_no_incendio,
                                                                     fecha_inicio_str=fecha_inicio_no_incendio)
                    print(f"Convertida planificación de no incendio: {len(planificacion_no_incendio_df)} filas")
                except Exception as e:
                    mensaje = f"Error al convertir planificación de no incendio: {e}"
                    print(mensaje)

        # Generar el HTML con las planificaciones procesadas
        hora_actual = datetime.now().time()
        html_content = generar_html_con_toggle(planificacion_incendio_df, planificacion_no_incendio_df, hora_actual)

        return planificacion_texto, planificacion_incendio_df, planificacion_no_incendio_df, html_content
    except Exception as e:
        print(f"Error en generar_planificacion_completa: {str(e)}")
        traceback.print_exc()
        return None, None, None, None


# NUEVO: Función para cargar planificaciones existentes
def cargar_planificaciones_existentes():
    try:
        # Verificar si existen archivos de planificación guardados
        planificacion_incendio_df = pd.DataFrame(columns=['Fecha', 'Día', 'Turno', 'Trabajadores'])
        planificacion_no_incendio_df = pd.DataFrame(columns=['Fecha', 'Día', 'Turno', 'Trabajadores'])

        # Intentar cargar desde archivos temporales si existen
        if os.path.exists('temp_planificacion_incendio.csv'):
            planificacion_incendio_df = pd.read_csv('temp_planificacion_incendio.csv')
            print("Planificación de incendio cargada desde archivo temporal")

        if os.path.exists('temp_planificacion_no_incendio.csv'):
            planificacion_no_incendio_df = pd.read_csv('temp_planificacion_no_incendio.csv')
            print("Planificación de no incendio cargada desde archivo temporal")

        return planificacion_incendio_df, planificacion_no_incendio_df
    except Exception as e:
        print(f"Error al cargar planificaciones existentes: {str(e)}")
        traceback.print_exc()
        return pd.DataFrame(), pd.DataFrame()


# NUEVO: Función para guardar planificaciones en archivos temporales
def guardar_planificaciones_temporales(planificacion_incendio_df, planificacion_no_incendio_df):
    try:
        if not planificacion_incendio_df.empty:
            planificacion_incendio_df.to_csv('temp_planificacion_incendio.csv', index=False)
            print("Planificación de incendio guardada en archivo temporal")

        if not planificacion_no_incendio_df.empty:
            planificacion_no_incendio_df.to_csv('temp_planificacion_no_incendio.csv', index=False)
            print("Planificación de no incendio guardada en archivo temporal")
    except Exception as e:
        print(f"Error al guardar planificaciones temporales: {str(e)}")
        traceback.print_exc()


# Ruta para generar la planificación (modo web)
@app.route('/generar', methods=['POST'])
def generar_planificacion_web():
    try:
        # Comprobar si existe el archivo de configuración
        if not os.path.exists('configuracion.json'):
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
                with open('configuracion.json', 'r', encoding='utf-8') as f:
                    configuracion_original = json.load(f)

                # Crear una copia de la configuración original pero modificando el tipo de planificación
                config_modificada = configuracion_original.copy()
                config_modificada['tipoPlanificacion'] = tipo_planificacion_solicitada

                # Guardar temporalmente la configuración modificada
                with open('configuracion.json', 'w', encoding='utf-8') as f:
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
                with open('configuracion.json', 'w', encoding='utf-8') as f:
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

# Route to view generated planning
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


if __name__ == "__main__":
    app.run(debug=True)
