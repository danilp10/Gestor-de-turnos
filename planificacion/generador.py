import os
import json
import pandas as pd
import traceback
from datetime import datetime

from procesamiento.leer_datos import leer_datos_json
from generadores.generar_planificaciones import generar_planificacion_trabajos_openai
from procesamiento.separar_planificaciones import separar_planificaciones
from procesamiento.convertir_tabla import convertir_a_tabla
from generadores.generar_html import generar_html_con_toggle


def generar_planificacion_completa(fichero_json='trabajadores/disponibilidades.json',
                                   fichero_conf_json='configuracion/configuracion.json',
                                   resultados_validacion=None):
    """
    Genera una planificación completa basada en la configuración actual.

    Args:
        fichero_json: Ruta al archivo JSON con datos de trabajadores
        fichero_conf_json: Ruta al archivo JSON con la configuración
        resultados_validacion: Ruta al archivo JSON con resultados de validación

    Returns:
        tuple: (texto_planificacion, df_incendio, df_no_incendio, html_content)
    """
    try:
        datos_trabajadores = leer_datos_json(fichero_json)

        if not datos_trabajadores:
            mensaje = "No se encontraron trabajadores disponibles en el archivo JSON."
            print(mensaje)
            return None, None, None, None

        apikey = os.getenv("apikey")

        planificacion_texto, prompt_usado = generar_planificacion_trabajos_openai(
            datos_trabajadores, apikey, fichero_conf_json, resultados_validacion)

        try:
            with open(fichero_conf_json, 'r', encoding='utf-8') as f:
                config = json.load(f)
                tipo_planificacion = config.get('tipoPlanificacion', 'ambos')
                incendio_config = config.get('incendio', {})
                no_incendio_config = config.get('noIncendio', {})
        except Exception as e:
            print(f"Error al leer el tipo de planificación: {e}")
            tipo_planificacion = 'ambos'
            incendio_config = {}
            no_incendio_config = {}

        planificacion_incendio_df = pd.DataFrame(columns=['Fecha', 'Día', 'Turno', 'Trabajadores'])
        planificacion_no_incendio_df = pd.DataFrame(columns=['Fecha', 'Día', 'Turno', 'Trabajadores'])

        if tipo_planificacion in ['ambos', 'incendio', 'noIncendio']:
            planificacion_incendio = ""
            planificacion_no_incendio = ""

            if tipo_planificacion == 'ambos':
                planificacion_incendio, planificacion_no_incendio = separar_planificaciones(planificacion_texto)
            elif tipo_planificacion == 'incendio':
                planificacion_incendio = planificacion_texto
            else:
                planificacion_no_incendio = planificacion_texto

            if tipo_planificacion in ['ambos', 'incendio'] and planificacion_incendio:
                try:
                    fecha_inicio_incendio = incendio_config.get('fechaInicio')
                    planificacion_incendio_df = convertir_a_tabla(planificacion_incendio,
                                                                  fecha_inicio_str=fecha_inicio_incendio)
                    print(f"Convertida planificación de incendio: {len(planificacion_incendio_df)} filas")
                except Exception as e:
                    mensaje = f"Error al convertir planificación de incendio: {e}"
                    print(mensaje)

            if tipo_planificacion in ['ambos', 'noIncendio'] and planificacion_no_incendio:
                try:
                    fecha_inicio_no_incendio = no_incendio_config.get('fechaInicio')
                    planificacion_no_incendio_df = convertir_a_tabla(planificacion_no_incendio,
                                                                     fecha_inicio_str=fecha_inicio_no_incendio)
                    print(f"Convertida planificación de no incendio: {len(planificacion_no_incendio_df)} filas")
                except Exception as e:
                    mensaje = f"Error al convertir planificación de no incendio: {e}"
                    print(mensaje)

        hora_actual = datetime.now().time()
        html_content = generar_html_con_toggle(planificacion_incendio_df, planificacion_no_incendio_df,
                                               hora_actual, prompt=prompt_usado)

        return planificacion_texto, planificacion_incendio_df, planificacion_no_incendio_df, html_content, prompt_usado
    except Exception as e:
        print(f"Error en generar_planificacion_completa: {str(e)}")
        traceback.print_exc()
        return None, None, None, None
