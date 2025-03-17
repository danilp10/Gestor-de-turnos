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

            # Validar campos obligatorios
            if not datos.get("id") or not datos.get("nombre") or not datos.get("apellidos"):
                return jsonify({
                    "status": "error",
                    "mensaje": "Faltan campos obligatorios (id, nombre, apellidos)"
                }), 400
            fichero_json = 'trabajadores/disponibilidades.json'
            trabajadores = leer_datos_json(fichero_json)

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
            fichero_json = 'trabajadores/disponibilidades.json'
            trabajadores = leer_datos_json(fichero_json)
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
