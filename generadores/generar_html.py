import datetime
from datetime import datetime as dt


def generar_html_con_toggle(df_incendio, df_no_incendio, hora_actual=None, prompt=None):
    """
    Genera un HTML con ambas planificaciones y un botón para alternar entre ellas.
    Añade indicadores de tiempo restante solo para los trabajadores del turno actual de hoy.

    Args:
        :param df_incendio: DataFrame con la planificación en caso de incendio
        :param df_no_incendio: DataFrame con la planificación en caso de no incendio
        :param hora_actual: Hora actual para calcular el tiempo restante (si es None, se usará la hora del sistema)
        :param prompt:
    """

    fecha_actual = dt.now().date()
    if hora_actual is None:
        hora_actual = dt.now().time()
    elif isinstance(hora_actual, str):
        try:
            hora_actual = dt.strptime(hora_actual, "%H:%M").time()
        except:
            hora_actual = dt.now().time()

    def es_hoy(fecha_str):
        try:
            if "-" in fecha_str:
                fecha_df = dt.strptime(fecha_str, "%Y-%m-%d").date()
            else:
                fecha_df = dt.strptime(fecha_str, "%d/%m/%Y").date()
            return fecha_df == fecha_actual
        except:
            return False

    def calcular_horas_restantes(turno):
        if "Diurno" in turno:
            fin_turno = dt.strptime("20:00", "%H:%M").time()
        else:
            fin_turno = dt.strptime("08:00", "%H:%M").time()
            if hora_actual > fin_turno:
                fin_turno_dt = dt.combine(dt.now().date() + datetime.timedelta(days=1), fin_turno)
            else:
                fin_turno_dt = dt.combine(dt.now().date(), fin_turno)

            hora_actual_dt = dt.combine(dt.now().date(), hora_actual)
            if hora_actual.hour >= 20:
                pass
            elif hora_actual.hour < 8:
                hora_actual_dt = dt.combine(dt.now().date(), hora_actual)
            else:
                return -1

            return (fin_turno_dt - hora_actual_dt).total_seconds() / 3600

        hora_actual_dt = dt.combine(dt.now().date(), hora_actual)
        fin_turno_dt = dt.combine(dt.now().date(), fin_turno)

        if hora_actual.hour >= 8 and hora_actual.hour < 20:
            return (fin_turno_dt - hora_actual_dt).total_seconds() / 3600
        else:
            return -1

    def obtener_clase_indicador(horas_restantes):
        if horas_restantes < 0:
            return ""
        elif horas_restantes < 2:
            return "indicador-rojo"
        elif horas_restantes < 4:
            return "indicador-naranja"
        elif horas_restantes < 8:
            return "indicador-amarillo"
        else:
            return "indicador-verde"

    def formatear_trabajadores_con_indicador(trabajadores, turno, fecha):
        if not es_hoy(fecha):
            return trabajadores

        horas_restantes = calcular_horas_restantes(turno)
        if horas_restantes < 0:
            return trabajadores

        clase_indicador = obtener_clase_indicador(horas_restantes)

        es_turno_actual = False
        hora_actual_num = hora_actual.hour + hora_actual.minute / 60

        if "Diurno" in turno and 8 <= hora_actual_num < 20:
            es_turno_actual = True
        elif "Nocturno" in turno and (hora_actual_num >= 20 or hora_actual_num < 8):
            es_turno_actual = True

        if not es_turno_actual:
            return trabajadores

        nombres = [nombre.strip() for nombre in trabajadores.split(',')]
        trabajadores_formateados = []

        for nombre in nombres:
            trabajadores_formateados.append(
                f"{nombre} <span class='tiempo-indicador {clase_indicador}' title='{horas_restantes:.1f} horas restantes'></span>")

        return ", ".join(trabajadores_formateados)

    tiene_incendio = not df_incendio.empty
    tiene_no_incendio = not df_no_incendio.empty

    html = """
    <!DOCTYPE html>
    <html>
    <head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 20px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 25px 0;
            box-shadow: 0 0 20px rgba(0, 0, 0, 0.15);
        }
        thead tr {
            background-color: #009879;
            color: #ffffff;
            text-align: left;
        }
        th, td {
            padding: 12px 15px;
            border: 1px solid #dddddd;
        }
        tbody tr {
            border-bottom: 1px solid #dddddd;
        }
        tbody tr:nth-of-type(even) {
            background-color: #f3f3f3;
        }
        tbody tr:last-of-type {
            border-bottom: 2px solid #009879;
        }
        .turno-diurno {
            background-color: #fff7e6;
        }
        .turno-nocturno {
            background-color: #e6f3ff;
        }
        .turno-cabildo {
            background-color: #e6ffe6;
        }
        .turno-refuerzo1 {
            background-color: #ffe6e6;
        }
        .turno-refuerzo2 {
            background-color: #e6e6ff;
        }
        h1 {
            color: #009879;
            text-align: center;
            margin-bottom: 30px;
        }
        .toggle-container {
            text-align: center;
            margin: 20px 0;
        }
        .toggle-btn {
            background-color: #009879;
            color: white;
            border: none;
            padding: 10px 20px;
            font-size: 16px;
            cursor: pointer;
            border-radius: 5px;
            transition: background-color 0.3s;
            margin: 0 5px;
        }
        .toggle-btn:hover {
            background-color: #007c63;
        }
        .btn-incendio {
            background-color: #d9534f;
        }
        .btn-incendio:hover {
            background-color: #c9302c;
        }
        .btn-no-incendio {
            background-color: #5cb85c;
        }
        .btn-no-incendio:hover {
            background-color: #449d44;
        }
        .btn-ambas {
            background-color: #337ab7;
        }
        .btn-ambas:hover {
            background-color: #286090;
        }
        .planificacion {
            display: none;
        }
        .active {
            display: block;
        }
        .status-indicator {
            text-align: center;
            font-size: 18px;
            font-weight: bold;
            margin-bottom: 20px;
            color: #d9534f;
        }
        .status-indicator.no-incendio {
            color: #5cb85c;
        }
        .error-message {
            background-color: #ffebee;
            color: #b71c1c;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
            text-align: center;
        }
        .tiempo-indicador {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-left: 5px;
            vertical-align: middle;
        }
        .indicador-verde {
            background-color: #4CAF50;
        }
        .indicador-amarillo {
            background-color: #FFEB3B;
        }
        .indicador-naranja {
            background-color: #FF9800;
        }
        .indicador-rojo {
            background-color: #F44336;
        }
        .leyenda {
            margin: 20px 0;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 5px;
            background-color: #f9f9f9;
        }
        .leyenda-item {
            display: flex;
            align-items: center;
            margin: 5px 0;
        }
        .leyenda-color {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 10px;
            display: inline-block;
        }
        .fecha-actual {
            background-color: #f0f8ff;
            border-left: 4px solid #4285f4;
        }
        .regenerar-container {
            margin: 20px 0;
            text-align: center;
        }
        .mensaje-estado {
            margin-top: 10px;
            padding: 10px;
            border-radius: 5px;
        }
        .mensaje-info {
            background-color: #d1ecf1;
            color: #0c5460;
        }
        .mensaje-error {
            background-color: #f8d7da;
            color: #721c24;
        }
        .mensaje-exito {
            background-color: #d4edda;
            color: #155724;
        }
        .btn-generar {
            background-color: #5bc0de;
        }
        .btn-generar:hover {
            background-color: #46b8da;
        }
        .spinner {
            display: none;
            width: 16px;
            height: 16px;
            border: 3px solid rgba(255,255,255,0.3);
            border-radius: 50%;
            border-top: 3px solid #fff;
            animation: spin 1s linear infinite;
            vertical-align: middle;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .button-text {
            margin-right: 20px;
        }
        .prompt-container {
            margin: 0; /* Elimina márgenes */
            padding: 15px;
            border: 1px solid #ddd;
            border-radius: 5px;
            background-color: #f9f9f9;
            width: 100%; /* Asegura que ocupe todo el ancho de la pantalla */
            box-sizing: border-box; /* Asegura que el padding no se agregue al ancho total */
        }

    </style>
    </head>
    <body>
    <div class="container">
        <h1>Planificación Semanal de Turnos</h1>
    """

    if not tiene_incendio and not tiene_no_incendio:
        html += """
        <div class="error-message">
            <h2>Error en la generación de planificaciones</h2>
            <p>No se han podido procesar correctamente los datos de planificación. Por favor, intente generar la planificación nuevamente.</p>
        </div>
        """
        return html + "</div></body></html>"

    if tiene_incendio and tiene_no_incendio:
        html += """
        <div class="toggle-container">
            <button id="toggleBtn" class="toggle-btn">Cambiar a Planificación Sin Incendio</button>
        </div>

        <div id="statusIndicator" class="status-indicator">
            SITUACIÓN ACTUAL: INCENDIO
        </div>
        """
    else:
        if tiene_incendio:
            html += """
            <div class="status-indicator">
                SITUACIÓN ACTUAL: INCENDIO
                <p style="font-size: 14px; color: #666;">(Solo se ha generado la planificación para caso de incendio)</p>
            </div>
            """
        else:
            html += """
            <div class="status-indicator no-incendio">
                SITUACIÓN ACTUAL: NO INCENDIO
                <p style="font-size: 14px; color: #666;">(Solo se ha generado la planificación para caso de no incendio)</p>
            </div>
            """

    html += """
    <div class="leyenda">
        <h3>Leyenda de Tiempo Restante (solo para trabajadores del turno actual)</h3>
        <div class="leyenda-item">
            <span class="leyenda-color indicador-verde"></span>
            <span>8-12 horas restantes de turno</span>
        </div>
        <div class="leyenda-item">
            <span class="leyenda-color indicador-amarillo"></span>
            <span>6-8 horas restantes de turno</span>
        </div>
        <div class="leyenda-item">
            <span class="leyenda-color indicador-naranja"></span>
            <span>2-4 horas restantes de turno</span>
        </div>
        <div class="leyenda-item">
            <span class="leyenda-color indicador-rojo"></span>
            <span>Menos de 2 horas restantes de turno</span>
        </div>
    </div>
    """

    clase_visibilidad = "planificacion active" if tiene_incendio else "planificacion"
    html += f"""
        <div id="planIncendio" class="{clase_visibilidad}">
            <h2>Planificación en Caso de Incendio</h2>
            <table>
                <thead>
                    <tr>
                        <th>Fecha</th>
                        <th>Día</th>
                        <th>Turno</th>
                        <th>Trabajadores</th>
                    </tr>
                </thead>
                <tbody>
    """

    if tiene_incendio:
        for _, row in df_incendio.iterrows():
            clase_turno = 'turno-diurno' if 'Diurno' in row['Turno'] else 'turno-nocturno'

            clase_fecha_actual = ' fecha-actual' if es_hoy(row['Fecha']) else ''

            trabajadores_formateados = formatear_trabajadores_con_indicador(
                row['Trabajadores'],
                row['Turno'],
                row['Fecha']
            )

            html += f"""
                        <tr class="{clase_turno}{clase_fecha_actual}">
                            <td>{row['Fecha']}</td>
                            <td>{row['Día']}</td>
                            <td>{row['Turno']}</td>
                            <td>{trabajadores_formateados}</td>
                        </tr>
            """

    html += """
                </tbody>
            </table>
        </div>
    """

    clase_visibilidad = "planificacion" if tiene_incendio else "planificacion active"
    html += f"""
        <div id="planNoIncendio" class="{clase_visibilidad}">
            <h2>Planificación en Caso de No Incendio</h2>
            <table>
                <thead>
                    <tr>
                        <th>Fecha</th>
                        <th>Día</th>
                        <th>Turno</th>
                        <th>Trabajadores</th>
                    </tr>
                </thead>
                <tbody>
    """

    if tiene_no_incendio:
        for _, row in df_no_incendio.iterrows():
            if 'Cabildo' in row['Turno']:
                clase_turno = 'turno-cabildo'
            elif 'refuerzo 1' in row['Turno']:
                clase_turno = 'turno-refuerzo1'
            else:
                clase_turno = 'turno-refuerzo2'

            clase_fecha_actual = ' fecha-actual' if es_hoy(row['Fecha']) else ''

            html += f"""
                        <tr class="{clase_turno}{clase_fecha_actual}">
                            <td>{row['Fecha']}</td>
                            <td>{row['Día']}</td>
                            <td>{row['Turno']}</td>
                            <td>{row['Trabajadores']}</td>
                        </tr>
            """

    html += """
                </tbody>
            </table>
        </div>
    """

    html += """
    <div class="regenerar-container">
        <div id="botonesPlan">
    """

    if tiene_incendio and tiene_no_incendio:
        html += """
            <button id="regenerarAmbasBtn" class="toggle-btn btn-ambas">
                <span class="button-text">Rehacer Ambas Planificaciones</span>
                <span id="spinnerAmbas" class="spinner"></span>
            </button>
        """

    if tiene_incendio:
        html += """
            <button id="regenerarIncendioBtn" class="toggle-btn btn-incendio">
                <span class="button-text">Rehacer Plan Incendio</span>
                <span id="spinnerIncendio" class="spinner"></span>
            </button>
        """

    if tiene_no_incendio:
        html += """
            <button id="regenerarNoIncendioBtn" class="toggle-btn btn-no-incendio">
                <span class="button-text">Rehacer Plan No Incendio</span>
                <span id="spinnerNoIncendio" class="spinner"></span>
            </button>
        """

    html += """
        </div>
        <div id="mensajeEstado"></div>
    </div>
    """

    if prompt is not None:
        start_index = prompt.find("Eres un asistente")
        if start_index != -1:
            prompt = prompt[start_index:]

        html += f"""
        <div class="prompt-container">
            <pre>{prompt}</pre>
        </div>
        """

    if tiene_incendio and tiene_no_incendio:
        html += """
        <script>
            const toggleBtn = document.getElementById('toggleBtn');
            const planIncendio = document.getElementById('planIncendio');
            const planNoIncendio = document.getElementById('planNoIncendio');
            const statusIndicator = document.getElementById('statusIndicator');

            let mostrandoIncendio = true;

            toggleBtn.addEventListener('click', function() {
                if (mostrandoIncendio) {
                    planIncendio.classList.remove('active');
                    planNoIncendio.classList.add('active');
                    toggleBtn.textContent = 'Cambiar a Planificación Con Incendio';
                    statusIndicator.textContent = 'SITUACIÓN ACTUAL: NO INCENDIO';
                    statusIndicator.classList.add('no-incendio');
                } else {
                    planNoIncendio.classList.remove('active');
                    planIncendio.classList.add('active');
                    toggleBtn.textContent = 'Cambiar a Planificación Sin Incendio';
                    statusIndicator.textContent = 'SITUACIÓN ACTUAL: INCENDIO';
                    statusIndicator.classList.remove('no-incendio');
                }
                mostrandoIncendio = !mostrandoIncendio;
            });
        </script>
        """

    html += """
    <script>
        function mostrarSpinner(tipo) {
            const tipoCapitalizado = tipo.charAt(0).toUpperCase() + tipo.slice(1);
            const spinner = document.getElementById('spinner' + tipoCapitalizado);
            if (spinner) {
                spinner.style.display = 'inline-block';
            }
        }
        
        // Modifica la función ocultarSpinners para ocultar todos los spinners
        function ocultarSpinners() {
            document.querySelectorAll('.spinner').forEach(spinner => {
                spinner.style.display = 'none';
            });
        }
        
        function habilitarBotones() {
            document.querySelectorAll('button').forEach(button => {
                button.disabled = false;
            });
        }
        
        function generarPlanificacion(tipo) {
            const mensajeEstado = document.getElementById('mensajeEstado');
            
            // Mostrar spinner
            mostrarSpinner(tipo);
            
            // Iniciar contador de tiempo
            let segundos = 0;
            const contadorId = setInterval(() => {
                segundos++;
                const tiempoTexto = document.getElementById('tiempoTexto');
                if (tiempoTexto) {
                    tiempoTexto.textContent = `Tiempo transcurrido: ${segundos} segundos`;
                }
            }, 1000);
        
            let mensajeTexto = '';
            if (tipo === 'ambas') {
                mensajeTexto = 'Generando ambas planificaciones, por favor espere...';
            } else {
                mensajeTexto = 'Generando nueva planificación para caso de ' + 
                              (tipo === 'incendio' ? 'incendio' : 'no incendio') + ', por favor espere...';
            }
        
            mensajeEstado.innerHTML = '<div class="mensaje-estado mensaje-info">' + mensajeTexto + 
                                     '<div id="tiempoTexto">Tiempo transcurrido: 0 segundos</div></div>';
        
            document.querySelectorAll('button').forEach(button => {
                button.disabled = true;
            });
        
            // Realizar la petición AJAX a la ruta /regenerar
            fetch('/regenerar', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ tipoPlanificacion: tipo, rehacerConValidacion: true })
            })
            .then(response => response.json())
            .then(data => {
                clearInterval(contadorId); // Detener contador
                ocultarSpinners(); // Ocultar spinners
                
                if (data.success) {
                    mensajeEstado.innerHTML = '<div class="mensaje-estado mensaje-exito">¡Planificación regenerada correctamente! Recargando página...</div>';
                    // Esperar un momento y recargar la página para mostrar la nueva planificación
                    setTimeout(() => {
                        window.location.reload();
                    }, 1500);
                } else {
                    mensajeEstado.innerHTML = '<div class="mensaje-estado mensaje-error">Error: ' + (data.error || 'Error desconocido') + '</div>';
                    habilitarBotones();
                }
            })
            .catch(error => {
                clearInterval(contadorId); // Detener contador
                ocultarSpinners(); // Ocultar spinners
                
                console.error('Error:', error);
                mensajeEstado.innerHTML = '<div class="mensaje-estado mensaje-error">Error en la comunicación con el servidor. Por favor, intente nuevamente.</div>';
                habilitarBotones();
            });
        }
    """

    if tiene_incendio and tiene_no_incendio:
        html += """
    document.getElementById('regenerarAmbasBtn').addEventListener('click', function() {
        generarPlanificacion('ambas');
    });
        """

    if tiene_incendio:
        html += """
    if (document.getElementById('regenerarIncendioBtn')) {
        document.getElementById('regenerarIncendioBtn').addEventListener('click', function() {
            generarPlanificacion('incendio');
        });
    }
        """

    if tiene_no_incendio:
        html += """
    if (document.getElementById('regenerarNoIncendioBtn')) {
        document.getElementById('regenerarNoIncendioBtn').addEventListener('click', function() {
            generarPlanificacion('noIncendio');
        });
    }
        """
    html += """
    window.addEventListener('pageshow', function(event) {
            // This ensures spinners are hidden when using back/forward navigation
            if (event.persisted) {
                ocultarSpinners();
                habilitarBotones();
            }
        });
    """

    html += """
    </script>
    """

    html += """
    </div>
    </body>
    </html>
    """
    return html
