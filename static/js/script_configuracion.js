

        function mostrarMensaje(mensaje, tipo, elementId = 'mensaje') {
            const mensajeDiv = document.getElementById(elementId);
            mensajeDiv.textContent = mensaje;
            mensajeDiv.className = tipo;
            mensajeDiv.classList.remove('hidden');
        }

        // Función para establecer fecha actual por defecto
        function setDefaultDates() {
            const today = new Date();
            const formattedDate = today.toISOString().split('T')[0];

            document.getElementById('fecha-incendio').value = formattedDate;
            document.getElementById('fecha-no-incendio').value = formattedDate;
        }

        // Función para actualizar la visibilidad de las secciones
        function actualizarSecciones() {
            const tipoPlanificacion = document.getElementById('tipo-planificacion').value;
            const seccionIncendio = document.getElementById('seccion-incendio');
            const seccionNoIncendio = document.getElementById('seccion-no-incendio');

            // Resetear clases
            seccionIncendio.classList.remove('section-disabled');
            seccionNoIncendio.classList.remove('section-disabled');

            // Actualizar según la selección
            if (tipoPlanificacion === 'incendio') {
                seccionNoIncendio.classList.add('section-disabled');
                // Desactivar requisitos en no incendio
                document.querySelectorAll('#seccion-no-incendio input').forEach(input => {
                    input.required = false;
                });
            } else if (tipoPlanificacion === 'noIncendio') {
                seccionIncendio.classList.add('section-disabled');
                // Desactivar requisitos en incendio
                document.querySelectorAll('#seccion-incendio input').forEach(input => {
                    input.required = false;
                });
            } else {
                // Activar requisitos en ambos
                document.querySelectorAll('#seccion-incendio input, #seccion-no-incendio input').forEach(input => {
                    input.required = true;
                });
            }
        }

        // Cargar la configuración existente al iniciar
        window.addEventListener('load', function() {
            // Establecer fechas por defecto
            setDefaultDates();

            // Valores por defecto básicos
            document.getElementById('dias-incendio').value = 7;
            document.getElementById('incendio-diurno').value = 3;
            document.getElementById('incendio-nocturno').value = 3;
            document.getElementById('dias-no-incendio').value = 7;
            document.getElementById('cabildo-personas').value = 2;
            document.getElementById('no-incendio-retenes-turnos').value = 1;
            document.getElementById('conductores-incendio').value = 2;

            // Valores por defecto para materiales
            document.getElementById('camiones-cisterna').value = 1;
            document.getElementById('mascaras-gas').value = 0;
            document.getElementById('hachas').value = 0;
            document.getElementById('escaleras-mecanicas').value = 1;


            // Generar el primer turno por defecto
            let turnosContainer = document.getElementById('no-incendio-turnos-container');
            turnosContainer.innerHTML = '';
            let label = document.createElement('label');
            label.textContent = `Personas en turno de no incendio 1:`;
            let input = document.createElement('input');
            input.type = 'number';
            input.name = `no-incendio-turno-1`;
            input.value = 2;
            input.required = true;
            turnosContainer.appendChild(label);
            turnosContainer.appendChild(input);

            // Escuchar el cambio en el tipo de planificación
            document.getElementById('tipo-planificacion').addEventListener('change', actualizarSecciones);

            // Aplicar la configuración inicial de visibilidad
            actualizarSecciones();

            // Intentar cargar configuración existente
            mostrarMensaje('Cargando configuración...', 'info', 'status-message');

            fetch('/configuracion/json', {
                method: 'GET',
                headers: {
                    'Accept': 'application/json',
                }
            })
            .then(response => {
                if (response.status === 404) {
                    return { status: 'error', mensaje: 'No se ha guardado ninguna configuración aún' };
                }
                if (!response.ok) {
                    throw new Error(`Error HTTP: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                if (data.status === 'ok') {
                    // Rellenar el formulario con la configuración existente
                    mostrarMensaje('Configuración cargada correctamente', 'success', 'status-message');

                    const config = data.configuracion;

                    // Cargar tipo de planificación si existe
                    if (config.tipoPlanificacion) {
                        document.getElementById('tipo-planificacion').value = config.tipoPlanificacion;
                        actualizarSecciones();
                    }
                    // Cargar configuración de materiales si existe
                    if (config.materiales) {
                        document.getElementById('camiones-cisterna').value = config.materiales.camionesCisterna || 1;
                        document.getElementById('mascaras-gas').value = config.materiales.mascarasGas || 0;
                        document.getElementById('hachas').value = config.materiales.hachas || 0;
                        document.getElementById('escaleras-mecanicas').value = config.materiales.escalerasMecanicas || 1;
                    }
                    // Cargar configuración de incendio si existe
                    if (config.incendio) {
                        document.getElementById('dias-incendio').value = config.incendio.dias;
                        document.getElementById('fecha-incendio').value = config.incendio.fechaInicio;
                        document.getElementById('incendio-diurno').value = config.incendio.turnoDiurno;
                        document.getElementById('incendio-nocturno').value = config.incendio.turnoNocturno;
                        document.getElementById('conductores-incendio').value = config.incendio.conductores;
                    }

                    // Cargar configuración de no incendio si existe
                    if (config.noIncendio) {
                        document.getElementById('dias-no-incendio').value = config.noIncendio.dias;
                        document.getElementById('fecha-no-incendio').value = config.noIncendio.fechaInicio;
                        document.getElementById('cabildo-personas').value = config.noIncendio.cabildoPersonas;

                        const retenes = config.noIncendio.retenes || [];
                        document.getElementById('no-incendio-retenes-turnos').value = retenes.length;

                        // Crear inputs para los retenes
                        const turnosContainer = document.getElementById('no-incendio-turnos-container');
                        turnosContainer.innerHTML = '';

                        retenes.forEach((reten, i) => {
                            let label = document.createElement('label');
                            label.textContent = `Personas en turno de no incendio ${i+1}:`;

                            let input = document.createElement('input');
                            input.type = 'number';
                            input.name = `no-incendio-turno-${i+1}`;
                            input.value = reten.personas;
                            input.required = config.tipoPlanificacion !== 'incendio';

                            turnosContainer.appendChild(label);
                            turnosContainer.appendChild(input);
                        });
                    }

                    // Mostrar el botón de generar planificación
                    document.getElementById('generar-btn').classList.remove('hidden');
                } else if (data.status === 'error' && data.mensaje.includes('No se ha guardado')) {
                    // No hay configuración previa
                    mostrarMensaje('Configurando nuevos parámetros', 'info', 'status-message');
                    setTimeout(() => {
                        document.getElementById('status-message').classList.add('hidden');
                    }, 3000);
                }
            })
            .catch(error => {
                if (error.message.includes('404')) {
                    mostrarMensaje('No hay configuración previa. Introduzca los parámetros deseados.', 'info', 'status-message');
                } else {
                    mostrarMensaje(`Error: ${error.message}`, 'error', 'status-message');
                    console.error('Error al cargar la configuración:', error);
                }

                setTimeout(() => {
                    document.getElementById('status-message').classList.add('hidden');
                }, 5000);
            });
        });

        // Generar inputs dinámicos para turnos de no incendio
        document.getElementById('no-incendio-retenes-turnos').addEventListener('input', function() {
            let turnosContainer = document.getElementById('no-incendio-turnos-container');
            turnosContainer.innerHTML = '';
            let cantidadTurnos = parseInt(this.value) || 0;
            const tipoPlanificacion = document.getElementById('tipo-planificacion').value;
            const requireRequired = tipoPlanificacion !== 'incendio';

            for (let i = 1; i <= cantidadTurnos; i++) {
                let label = document.createElement('label');
                label.textContent = `Personas en turno de no incendio ${i}:`;
                let input = document.createElement('input');
                input.type = 'number';
                input.name = `no-incendio-turno-${i}`;
                input.value = 2; // Valor por defecto
                input.required = requireRequired;

                turnosContainer.appendChild(label);
                turnosContainer.appendChild(input);
            }
        });

        // Manejar envío del formulario de configuración
        document.getElementById('config-form').addEventListener('submit', function(event) {
            event.preventDefault();

            mostrarMensaje('Guardando configuración...', 'info');

            const tipoPlanificacion = document.getElementById('tipo-planificacion').value;
            let configuracion = {
                tipoPlanificacion: tipoPlanificacion
            };

            // Añadir configuración de incendio si es necesario
            if (tipoPlanificacion === 'ambos' || tipoPlanificacion === 'incendio') {
                configuracion.incendio = {
                    dias: document.getElementById('dias-incendio').value,
                    fechaInicio: document.getElementById('fecha-incendio').value,
                    turnoDiurno: document.getElementById('incendio-diurno').value,
                    turnoNocturno: document.getElementById('incendio-nocturno').value,
                    conductores: document.getElementById('conductores-incendio').value
                };
            }

            if (tipoPlanificacion === 'ambos' || tipoPlanificacion === 'noIncendio') {
                const cantidadTurnos = parseInt(document.getElementById('no-incendio-retenes-turnos').value) || 0;
                let retenes = [];

                for (let i = 1; i <= cantidadTurnos; i++) {
                    const input = document.querySelector(`input[name="no-incendio-turno-${i}"]`);
                    if (input) {
                        retenes.push({
                            turno: i,
                            personas: parseInt(input.value) || 2
                        });
                    }
                }

                configuracion.noIncendio = {
                    dias: document.getElementById('dias-no-incendio').value,
                    fechaInicio: document.getElementById('fecha-no-incendio').value,
                    cabildoPersonas: document.getElementById('cabildo-personas').value,
                    retenes: retenes
                };
            }

            configuracion.materiales = {
                camionesCisterna: parseInt(document.getElementById('camiones-cisterna').value) || 1,
                mascarasGas: parseInt(document.getElementById('mascaras-gas').value) || 0,
                hachas: parseInt(document.getElementById('hachas').value) || 0,
                escalerasMecanicas: parseInt(document.getElementById('escaleras-mecanicas').value) || 1
            };

            fetch('/configuracion', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(configuracion)
            })
            .then(response => {
                if (!response.ok) {
                    return response.json().then(data => {
                        throw new Error(data.mensaje || `Error HTTP: ${response.status}`);
                    });
                }
                return response.json();
            })
            .then(data => {
                mostrarMensaje('Configuración guardada correctamente', 'success');

                document.getElementById('generar-btn').classList.remove('hidden');
            })
            .catch(error => {
                mostrarMensaje(`Error: ${error.message}`, 'error');
            });
        });

        document.getElementById('generar-btn').addEventListener('click', function() {
            mostrarMensaje('Generando planificación, por favor espere...', 'info');
            toggleButtonSpinner('generar-btn', true);

            // Iniciar contador de tiempo
            const tiempoContador = document.getElementById('tiempo-contador');
            tiempoContador.textContent = 'Tiempo transcurrido: 0 segundos';
            tiempoContador.classList.remove('hidden');

            let segundos = 0;
            const contadorId = setInterval(() => {
                segundos++;
                tiempoContador.textContent = `Tiempo transcurrido: ${segundos} segundos`;
            }, 1000);

            fetch('/generar', {
                method: 'POST'
            })
            .then(response => {
                if (!response.ok) {
                    return response.json().then(data => {
                        throw new Error(data.error || `Error HTTP: ${response.status}`);
                    });
                }
                return response.json();
            })
            .then(data => {
                // Detener contador
                clearInterval(contadorId);
                tiempoContador.classList.add('hidden');
                toggleButtonSpinner('generar-btn', false);

                mostrarMensaje('Planificación generada correctamente. Redirigiendo...', 'success');

                setTimeout(() => {
                    window.location.href = '/planificacion';
                }, 1500);
            })
            .catch(error => {
                // Detener contador en caso de error
                clearInterval(contadorId);
                tiempoContador.classList.add('hidden');

                mostrarMensaje(`Error al generar planificación: ${error.message}`, 'error');
                toggleButtonSpinner('generar-btn', false);
            });
        });

        // Función para mostrar/ocultar el spinner global
        function toggleSpinner(show = true) {
            const spinner = document.getElementById('spinner-global');
            if (show) {
                spinner.classList.remove('hidden');
            } else {
                spinner.classList.add('hidden');
            }
        }

        function toggleButtonSpinner(buttonId, show = true) {
            const button = document.getElementById(buttonId);
            if (!button) return;

            const spinner = button.querySelector('.spinner');
            if (!spinner) return;

            if (show) {
                spinner.style.display = 'inline-block';
                button.classList.add('loading');
                button.classList.add('disabled');
            } else {
                spinner.style.display = 'none';
                button.classList.remove('loading');
                button.classList.remove('disabled');
            }
        }