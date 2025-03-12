import os
import pandas as pd
import traceback


def cargar_planificaciones_existentes():
    """
    Carga planificaciones previamente generadas desde archivos temporales.
    """
    try:
        # Verificar si existen archivos de planificación guardados
        planificacion_incendio_df = pd.DataFrame(columns=['Fecha', 'Día', 'Turno', 'Trabajadores'])
        planificacion_no_incendio_df = pd.DataFrame(columns=['Fecha', 'Día', 'Turno', 'Trabajadores'])

        # Intentar cargar desde archivos temporales si existen
        if os.path.exists('planificaciones_generadas/temp_planificacion_incendio.csv'):
            planificacion_incendio_df = pd.read_csv('planificaciones_generadas/temp_planificacion_incendio.csv')
            print("Planificación de incendio cargada desde archivo temporal")

        if os.path.exists('planificaciones_generadas/temp_planificacion_no_incendio.csv'):
            planificacion_no_incendio_df = pd.read_csv('planificaciones_generadas/temp_planificacion_no_incendio.csv')
            print("Planificación de no incendio cargada desde archivo temporal")

        return planificacion_incendio_df, planificacion_no_incendio_df
    except Exception as e:
        print(f"Error al cargar planificaciones existentes: {str(e)}")
        traceback.print_exc()
        return pd.DataFrame(), pd.DataFrame()


def guardar_planificaciones_temporales(planificacion_incendio_df, planificacion_no_incendio_df):
    """
    Guarda las planificaciones generadas en archivos temporales para futuras referencias.
    """
    try:
        if not planificacion_incendio_df.empty:
            planificacion_incendio_df.to_csv('planificaciones_generadas/temp_planificacion_incendio.csv', index=False)
            print("Planificación de incendio guardada en archivo temporal")

        if not planificacion_no_incendio_df.empty:
            planificacion_no_incendio_df.to_csv('planificaciones_generadas/temp_planificacion_no_incendio.csv', index=False)
            print("Planificación de no incendio guardada en archivo temporal")
    except Exception as e:
        print(f"Error al guardar planificaciones temporales: {str(e)}")
        traceback.print_exc()
