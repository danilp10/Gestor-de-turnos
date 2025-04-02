from flask import jsonify, request
from datetime import datetime
from trabajadores.modelo import guardar_datos, determinar_estado
from procesamiento.leer_datos import leer_datos_json


def configurar_rutas_trabajadores(app):
    """
    Configura las rutas relacionadas con los trabajadores en la aplicación Flask.
    """

    @app.route('/api/trabajadores', methods=['GET'])
    def obtener_trabajadores():
        fichero_json = 'trabajadores/disponibilidades.json'
        trabajadores = leer_datos_json(fichero_json)
        return jsonify({
            "status": "ok",
            "total": len(trabajadores),
            "trabajadores": trabajadores
        })

    @app.route('/api/trabajadores/<id>', methods=['GET'])
    def obtener_trabajador(id):
        fichero_json = 'trabajadores/disponibilidades.json'
        trabajadores = leer_datos_json(fichero_json)
        trabajador = next((t for t in trabajadores if str(t["id"]) == str(id)), None)
        if not trabajador:
            return jsonify({"status": "error", "mensaje": "Trabajador no encontrado"}), 404
        return jsonify(trabajador)

    @app.route('/api/trabajadores', methods=['POST'])
    def agregar_trabajador():
        try:
            datos = request.get_json()

            if not datos.get("id") or not datos.get("nombre") or not datos.get("apellidos"):
                return jsonify({
                    "status": "error",
                    "mensaje": "Faltan campos obligatorios (id, nombre, apellidos)"
                }), 400
            fichero_json = 'trabajadores/disponibilidades.json'
            trabajadores = leer_datos_json(fichero_json)

            if any(str(t["id"]) == str(datos["id"]) for t in trabajadores):
                return jsonify({
                    "status": "error",
                    "tipo": "ID_DUPLICADO",
                    "mensaje": "Ya existe un trabajador con este ID"
                }), 409

            datos["id"] = str(datos["id"])

            datos["estado"] = determinar_estado(
                datos.get("excepciones", {}).get("reincorporacion"),
                datos.get("excepciones", {}).get("vacaciones")
            )

            if "disponibilidad" in datos:
                todos_dias = ['lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado', 'domingo']
                datos["diasNoDisponibles"] = [dia for dia in todos_dias if dia not in datos["disponibilidad"]]

            datos["timestamp"] = datetime.now().isoformat()
            trabajadores.append(datos)

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
            fichero_json = 'trabajadores/disponibilidades.json'
            trabajadores = leer_datos_json(fichero_json)
            index = next((i for i, t in enumerate(trabajadores) if str(t["id"]) == str(id)), -1)

            if index == -1:
                return jsonify({"status": "error", "mensaje": "Trabajador no encontrado"}), 404

            datos["id"] = id

            if "disponibilidad" in datos:
                todos_dias = ['lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado', 'domingo']
                datos["diasNoDisponibles"] = [dia for dia in todos_dias if dia not in datos["disponibilidad"]]

            datos["estado"] = determinar_estado(
                datos.get("excepciones", {}).get("reincorporacion"),
                datos.get("excepciones", {}).get("vacaciones")
            )

            datos["timestamp"] = datetime.now().isoformat()

            trabajador_actualizado = {**trabajadores[index], **datos}
            trabajadores[index] = trabajador_actualizado

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

    @app.route('/api/trabajadores/buscar', methods=['GET'])
    def buscar_trabajadores():
        try:
            nombre = request.args.get('nombre', '').lower()
            apellidos = request.args.get('apellidos', '').lower()

            if not nombre and not apellidos:
                return jsonify({
                    "status": "error",
                    "mensaje": "Debe proporcionar al menos un parámetro de búsqueda (nombre o apellidos)"
                }), 400

            fichero_json = 'trabajadores/disponibilidades.json'
            trabajadores = leer_datos_json(fichero_json)

            resultados = []
            for trabajador in trabajadores:
                nombre_trabajador = trabajador.get("nombre", "").lower()
                apellidos_trabajador = trabajador.get("apellidos", "").lower()

                coincide_nombre = not nombre or nombre in nombre_trabajador
                coincide_apellidos = not apellidos or apellidos in apellidos_trabajador

                if coincide_nombre and coincide_apellidos:
                    resultados.append(trabajador)

            return jsonify({
                "status": "ok",
                "total": len(resultados),
                "resultados": resultados
            })

        except Exception as e:
            print(f"Error en búsqueda de trabajadores: {e}")
            return jsonify({
                "status": "error",
                "mensaje": f"Error: {str(e)}"
            }), 500
