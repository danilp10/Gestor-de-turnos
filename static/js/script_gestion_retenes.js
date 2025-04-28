
        const diasSemana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"];


        function generarDiasDisponibles() {
            return diasSemana.map(dia => `
                <div class="day-container">
                    <label><input type="checkbox" id="${dia.toLowerCase()}"> ${dia}</label>
                </div>
            `).join('');
        }

        document.getElementById('dias').innerHTML = generarDiasDisponibles();

        let modoEdicion = false;
        let trabajadorActual = null;

        function mostrarNuevo() {
            modoEdicion = false;
            document.getElementById('optionsContainer').style.display = 'none';
            document.getElementById('formContainer').style.display = 'block';
            document.getElementById('formTitle').textContent = 'Ingresar Nuevo Trabajador';
            document.getElementById('id').disabled = false;
            document.getElementById('datosForm').reset();
            actualizarEstadoVisual();
        }

        function mostrarBusqueda() {
            document.getElementById('searchContainer').style.display = 'block';
        }

        function volverAOpciones() {
            document.getElementById('optionsContainer').style.display = 'block';
            document.getElementById('formContainer').style.display = 'none';
            document.getElementById('searchContainer').style.display = 'none';
            document.getElementById('searchError').style.display = 'none';
            document.getElementById('idError').style.display = 'none';

            document.getElementById('resultadosBusqueda').innerHTML = '';

            document.getElementById('searchId').value = '';
            document.getElementById('searchNombre').value = '';
            document.getElementById('searchApellidos').value = '';
        }

        const API_URL = "/api/trabajadores";

        async function buscarTrabajador() {

            const id = document.getElementById('searchId').value;
            try {
            const response = await fetch(`${API_URL}/${id}`);
                if (!response.ok) {
                    throw new Error('Trabajador no encontrado');
                }
                trabajadorActual = await response.json();
                cargarDatosTrabajador(trabajadorActual);
            } catch (error) {
                document.getElementById('searchError').textContent = 'Trabajador no encontrado';
                document.getElementById('searchError').style.display = 'block';
            }
        }

        function cargarDatosTrabajador(datos) {
            console.log("Cargando datos del trabajador:", datos);
            modoEdicion = true;
            document.getElementById('optionsContainer').style.display = 'none';
            document.getElementById('formContainer').style.display = 'block';
            document.getElementById('formTitle').textContent = 'Modificar Trabajador';

            document.getElementById('id').value = datos.id;
            document.getElementById('id').disabled = true;
            document.getElementById('nombre').value = datos.nombre || '';
            document.getElementById('apellidos').value = datos.apellidos || '';
            document.getElementById('personalCabildo').checked = datos.personalCabildo || false;
            document.getElementById('carnetConducir').checked = datos.carnetConducir || false;

            diasSemana.forEach(dia => {
                const diaLower = dia.toLowerCase();
                const checkboxDia = document.getElementById(diaLower);
                if (checkboxDia) checkboxDia.checked = false;
            });

            if (datos.disponibilidad) {
                if (Array.isArray(datos.disponibilidad)) {
                    datos.disponibilidad.forEach(dia => {
                        const checkbox = document.getElementById(dia.toLowerCase());
                        if (checkbox) checkbox.checked = true;
                    });
                } else if (typeof datos.disponibilidad === 'object') {
                    Object.keys(datos.disponibilidad).forEach(dia => {
                        if (datos.disponibilidad[dia]) {
                            const checkbox = document.getElementById(dia.toLowerCase());
                            if (checkbox) checkbox.checked = true;
                        }
                    });
                }
            }
            document.getElementById('vacacionesInicio').value = '';
            document.getElementById('vacacionesFin').value = '';
            document.getElementById('reincorporacion').value = '';

            if (datos.excepciones) {
                if (datos.excepciones.vacaciones) {
                    document.getElementById('vacacionesInicio').value = datos.excepciones.vacaciones.inicio || '';
                    document.getElementById('vacacionesFin').value = datos.excepciones.vacaciones.fin || '';
                }
                if (datos.excepciones.reincorporacion) {
                    document.getElementById('reincorporacion').value = datos.excepciones.reincorporacion || '';
                }
            }

            actualizarEstadoVisual();
        }


        function actualizarEstadoVisual() {
            const reincorporacion = document.getElementById('reincorporacion').value;
            const vacacionesInicio = document.getElementById('vacacionesInicio').value;
            const vacacionesFin = document.getElementById('vacacionesFin').value;
            const estadoDiv = document.getElementById('estadoTrabajador');
            const inputVacacionesInicio = document.getElementById('vacacionesInicio');

            inputVacacionesInicio.setCustomValidity("");
            inputVacacionesInicio.disabled = false;

            const fechaActual = new Date();

            if (vacacionesInicio && vacacionesFin) {
                const inicioVacaciones = new Date(vacacionesInicio);
                const finVacaciones = new Date(vacacionesFin);

                if (fechaActual >= inicioVacaciones && fechaActual <= finVacaciones) {
                    estadoDiv.textContent = 'Estado: Vacaciones';
                    estadoDiv.style.color = '#FF8C00';
                    return;
                }
            }

            if (!reincorporacion) {
                estadoDiv.textContent = 'Estado: Activo';
                estadoDiv.style.color = 'green';
            } else {
                const fechaReincorporacion = new Date(reincorporacion);

                if (fechaReincorporacion > fechaActual) {
                    estadoDiv.textContent = 'Estado: Baja';
                    estadoDiv.style.color = 'red';
                    inputVacacionesInicio.disabled = false;
                } else {
                    estadoDiv.textContent = 'Estado: Activo';
                    estadoDiv.style.color = 'green';
                }
            }

            if (reincorporacion && vacacionesInicio) {
                const vacacionesInicioDate = new Date(vacacionesInicio);
                const reincorporacionDate = new Date(reincorporacion);

                if (reincorporacionDate > fechaActual && vacacionesInicioDate <= reincorporacionDate) {
                    inputVacacionesInicio.setCustomValidity("La fecha de inicio de las vacaciones debe ser posterior a la fecha de reincorporación.");
                }
            }
        }


        document.getElementById('datosForm').addEventListener('submit', async (e) => {
            e.preventDefault();

            const id = document.getElementById('id').value;
            const nombre = document.getElementById('nombre').value;
            const apellidos = document.getElementById('apellidos').value;
            const personalCabildo = document.getElementById('personalCabildo').checked;
            const carnetConducir = document.getElementById('carnetConducir').checked; // Nuevo campo


            let disponibilidad = [];
            diasSemana.forEach(dia => {
                const diaLower = dia.toLowerCase();
                if (document.getElementById(diaLower).checked) {
                    disponibilidad.push(diaLower);
                }
            });

            const excepciones = {
                vacaciones: document.getElementById('vacacionesInicio').value && document.getElementById('vacacionesFin').value ?
                    { inicio: document.getElementById('vacacionesInicio').value, fin: document.getElementById('vacacionesFin').value }
                    : null,
                reincorporacion: document.getElementById('reincorporacion').value || null
            };

            const reincorporacion = document.getElementById('reincorporacion').value;
            const vacacionesInicio = document.getElementById('vacacionesInicio').value;
            if (reincorporacion && vacacionesInicio) {
                const reincorporacionDate = new Date(reincorporacion);
                const vacacionesInicioDate = new Date(vacacionesInicio);

                if (vacacionesInicioDate <= reincorporacionDate) {
                    alert("La fecha de inicio de las vacaciones debe ser posterior a la fecha de reincorporación.");
                    return;
                }
            }

            const datos = {
                id,
                nombre,
                apellidos,
                personalCabildo,
                carnetConducir,
                disponibilidad,
                excepciones
            };

            try {
                const url = modoEdicion ? `${API_URL}/${id}` : API_URL;
                const method = modoEdicion ? "PUT" : "POST";

                const response = await fetch(url, {
                    method: method,
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(datos)
                });

                const resultado = await response.json();

                if (resultado.status === 'error' && resultado.tipo === 'ID_DUPLICADO') {
                    document.getElementById('idError').style.display = 'block';
                    return;
                }

                document.getElementById('idError').style.display = 'none';
                alert(modoEdicion ? 'Datos actualizados correctamente' : 'Datos guardados correctamente');
                volverAOpciones();
                document.getElementById('datosForm').reset();

            } catch (error) {
                console.error('Error:', error);
                alert('Error al procesar la solicitud');
            }
        });

        async function buscarTrabajadoresPorNombreApellidos() {
            const nombreBuscado = document.getElementById('searchNombre').value.trim();
            const apellidosBuscados = document.getElementById('searchApellidos').value.trim();

            if (!nombreBuscado && !apellidosBuscados) {
                alert("Ingrese al menos un nombre o apellido para buscar.");
                return;
            }

            try {
                // Construir la URL con los parámetros de búsqueda
                let url = `${API_URL}/buscar?`;
                if (nombreBuscado) {
                    url += `nombre=${encodeURIComponent(nombreBuscado)}`;
                }
                if (apellidosBuscados) {
                    if (nombreBuscado) url += '&';
                    url += `apellidos=${encodeURIComponent(apellidosBuscados)}`;
                }

                const response = await fetch(url);
                if (!response.ok) {
                    throw new Error('Error al obtener los datos');
                }

                const data = await response.json();

                if (data.status === 'error') {
                    throw new Error(data.mensaje);
                }

                const coincidencias = data.resultados || [];
                const resultadosContainer = document.getElementById('resultadosBusqueda');
                resultadosContainer.innerHTML = "";

                if (coincidencias.length === 0) {
                    resultadosContainer.innerHTML = "<p>No se encontraron coincidencias.</p>";
                    return;
                }

                const listaResultados = document.createElement("ul");
                listaResultados.className = "lista-resultados";

                coincidencias.forEach(trabajador => {
                    const item = document.createElement("li");
                    item.innerHTML = `<strong>${trabajador.nombre} ${trabajador.apellidos}</strong> (ID: ${trabajador.id})`;
                    item.style.cursor = "pointer";
                    item.onclick = () => cargarDatosTrabajador(trabajador);
                    listaResultados.appendChild(item);
                });

                resultadosContainer.appendChild(listaResultados);

            } catch (error) {
                console.error('Error:', error);
                alert('Error al procesar la búsqueda: ' + error.message);
            }
        }
