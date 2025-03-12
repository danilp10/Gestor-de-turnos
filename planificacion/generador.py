import os
import json
import pandas as pd
import traceback
from datetime import datetime

# Importar funciones externas
from procesamiento.leer_datos import leer_datos_json
from generadores.generar_planificaciones import generar_planificacion_trabajos_openai
from procesamiento.separar_planificaciones import separar_planificaciones
from procesamiento.convertir_tabla import convertir_a_tabla
from generadores.generar_html import generar_html_con_toggle


def generar_planificacion_completa(fichero_json='trabajadores/disponibilidades.json',
                                   fichero_conf_json='configuracion/configuracion.json'):
    """
    Genera una planificación completa basada en la configuración actual.

    Args:
        fichero_json: Ruta al archivo JSON con datos de trabajadores
        fichero_conf_json: Ruta al archivo JSON con la configuración

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
