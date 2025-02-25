def generar_html_con_toggle(df_incendio, df_no_incendio):
    """
    Genera un HTML con ambas planificaciones y un botón para alternar entre ellas
    """
    tiene_incendio = not df_incendio.empty
    tiene_no_incendio = not df_no_incendio.empty

    if not tiene_incendio and tiene_no_incendio:
        df_incendio, df_no_incendio = df_no_incendio, df_incendio
        tiene_incendio = True
        tiene_no_incendio = False

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
        }
        .toggle-btn:hover {
            background-color: #007c63;
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
            html += f"""
                        <tr class="{clase_turno}">
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

            html += f"""
                        <tr class="{clase_turno}">
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
    </div>
    </body>
    </html>
    """
    return html
