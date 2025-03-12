def separar_planificaciones(planificacion_texto):
    """Separa las planificaciones de incendio y no incendio del texto generado"""

    incendio_marker = "PLANIFICACIÓN EN CASO DE INCENDIO:"
    no_incendio_marker = "PLANIFICACIÓN EN CASO DE NO INCENDIO:"

    if incendio_marker not in planificacion_texto and no_incendio_marker not in planificacion_texto:
        if "**Día 1:**" in planificacion_texto:
            partes = planificacion_texto.split("**Día 1:**", 2)
            if len(partes) > 2:
                planificacion_incendio = "**Día 1:**" + partes[1]
                planificacion_no_incendio = "**Día 1:**" + partes[2]
                return planificacion_incendio, planificacion_no_incendio
            else:
                return planificacion_texto, ""
        else:
            return planificacion_texto, ""

    if incendio_marker in planificacion_texto and no_incendio_marker in planificacion_texto:
        partes = planificacion_texto.split(no_incendio_marker)
        planificacion_incendio = partes[0].replace(incendio_marker, "").strip()
        planificacion_no_incendio = partes[1].strip()
    elif incendio_marker in planificacion_texto:
        planificacion_incendio = planificacion_texto.replace(incendio_marker, "").strip()
        planificacion_no_incendio = ""
    else:
        partes = planificacion_texto.split(no_incendio_marker)
        planificacion_incendio = partes[0].strip()
        planificacion_no_incendio = partes[1].strip()

    return planificacion_incendio, planificacion_no_incendio
