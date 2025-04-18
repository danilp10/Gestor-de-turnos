import json
import os
from datetime import datetime
from procesamiento.leer_datos import leer_datos_json

DATA_FILE = "trabajadores/disponibilidades.json"


def guardar_datos(datos):
    """
    Guarda los datos de los trabajadores en el archivo JSON.
    """
    try:
        os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(datos, f, indent=2, ensure_ascii=False)
        print("Datos guardados correctamente")
        return True
    except Exception as e:
        print(f"Error al guardar datos: {e}")
        return False


def determinar_estado(reincorporacion, vacaciones):
    """
    Determina el estado actual del trabajador en función de su reincorporación y vacaciones.
    """
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
    """
    Actualiza los estados de los trabajadores en función de la fecha actual.
    """
    fichero_json = 'trabajadores/disponibilidades.json'
    trabajadores = leer_datos_json(fichero_json)
    fecha_actual = datetime.today().date()

    cambios = False
    for trabajador in trabajadores:
        if "excepciones" in trabajador:
            reincorporacion = trabajador["excepciones"].get("reincorporacion")
            vacaciones = trabajador["excepciones"].get("vacaciones")

            try:
                fecha_reincorporacion = None
                fecha_inicio_vacaciones = None
                fecha_fin_vacaciones = None

                if reincorporacion:
                    fecha_reincorporacion = datetime.strptime(reincorporacion, "%Y-%m-%d").date()

                if vacaciones and vacaciones.get("inicio"):
                    fecha_inicio_vacaciones = datetime.strptime(vacaciones["inicio"], "%Y-%m-%d").date()

                if vacaciones and vacaciones.get("fin"):
                    fecha_fin_vacaciones = datetime.strptime(vacaciones["fin"], "%Y-%m-%d").date()

                if fecha_inicio_vacaciones and fecha_inicio_vacaciones == fecha_actual:
                    if trabajador.get("estado") != "vacaciones":
                        trabajador["estado"] = "vacaciones"
                        cambios = True
                        print(f"Trabajador {trabajador['id']} actualizado a VACACIONES (Inicio: {vacaciones['inicio']})")

                elif fecha_inicio_vacaciones and fecha_fin_vacaciones:
                    if fecha_inicio_vacaciones <= fecha_actual <= fecha_fin_vacaciones:
                        if trabajador.get("estado") != "vacaciones":
                            trabajador["estado"] = "vacaciones"
                            cambios = True
                            print(f"Trabajador {trabajador['id']} actualizado a VACACIONES (Durante periodo)")
                    elif fecha_actual > fecha_fin_vacaciones and trabajador.get("estado") == "vacaciones":
                        trabajador["estado"] = "activo"
                        trabajador["excepciones"]["vacaciones"] = None
                        cambios = True
                        print(f"Trabajador {trabajador['id']} actualizado a ACTIVO (Fin de vacaciones)")

                if fecha_reincorporacion and fecha_actual >= fecha_reincorporacion and trabajador.get("estado") == "baja":
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
