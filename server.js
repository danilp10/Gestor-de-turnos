const express = require('express');
const cors = require('cors');
const fs = require('fs').promises;
const path = require('path');
const app = express();
const port = 5701;

app.use(cors());
app.use(express.json());

const DATA_FILE = path.join(__dirname, 'trabajadores/disponibilidades.json');

async function leerDatos() {
    try {
        const data = await fs.readFile(DATA_FILE, 'utf8');
        return JSON.parse(data);
    } catch (error) {
        if (error.code === 'ENOENT') {
            await fs.writeFile(DATA_FILE, JSON.stringify([], null, 2));
            return [];
        }
        throw error;
    }
}

async function guardarDatos(datos) {
    await fs.writeFile(DATA_FILE, JSON.stringify(datos, null, 2));
}

function determinarEstado(reincorporacion, vacaciones) {
    const fechaActual = new Date();

    if (vacaciones && vacaciones.inicio && vacaciones.fin) {
        const fechaInicioVacaciones = new Date(vacaciones.inicio);
        const fechaFinVacaciones = new Date(vacaciones.fin);

        if (fechaActual >= fechaInicioVacaciones && fechaActual <= fechaFinVacaciones) {
            return 'vacaciones';
        }
    }

    if (!reincorporacion) return 'activo';

    const fechaReincorporacion = new Date(reincorporacion);
    return fechaReincorporacion > fechaActual ? 'baja' : 'activo';
}

function validarVacaciones(reincorporacion, vacacionesInicio) {
    if (reincorporacion) {
        const reincorporacionDate = new Date(reincorporacion);
        const vacacionesInicioDate = new Date(vacacionesInicio);

        if (vacacionesInicioDate <= reincorporacionDate) {
            print("No")
        }
    }
}

async function actualizarEstadosIniciales() {
    const recursos = await leerDatos();
    const fechaActual = new Date();
    fechaActual.setHours(0, 0, 0, 0);

    let cambios = false;

    recursos.forEach((recurso) => {
        if (recurso.excepciones) {
            let { reincorporacion, vacaciones } = recurso.excepciones;

            const fechaReincorporacion = reincorporacion ? new Date(reincorporacion) : null;
            const fechaInicioVacaciones = vacaciones?.inicio ? new Date(vacaciones.inicio) : null;
            const fechaFinVacaciones = vacaciones?.fin ? new Date(vacaciones.fin) : null;

            if (fechaReincorporacion) fechaReincorporacion.setHours(0, 0, 0, 0);
            if (fechaInicioVacaciones) fechaInicioVacaciones.setHours(0, 0, 0, 0);
            if (fechaFinVacaciones) fechaFinVacaciones.setHours(0, 0, 0, 0);

            if (fechaInicioVacaciones && fechaActual.getTime() === fechaInicioVacaciones.getTime()) {
                recurso.estado = 'vacaciones';
                cambios = true;
                console.log(`Trabajador ${recurso.id} actualizado a VACACIONES (Inicio: ${vacaciones.inicio})`);
            }

            else if ((fechaReincorporacion && fechaActual >= fechaReincorporacion) ||
                     (fechaFinVacaciones && fechaActual >= fechaFinVacaciones)) {
                recurso.estado = 'activo';
                recurso.excepciones.reincorporacion = null;
                recurso.excepciones.vacaciones = null;
                cambios = true;
                console.log(`Trabajador ${recurso.id} actualizado a ACTIVO (Reincorporación o fin de vacaciones alcanzado)`);
            }
        }
    });

    if (cambios) {
        await guardarDatos(recursos);
        console.log("Estados actualizados según la fecha actual.");
    } else {
        console.log("No se encontraron cambios en los estados de los trabajadores.");
    }
}

actualizarEstadosIniciales();

app.post('/api/recursos', async (req, res) => {
    try {
        const { id, nombre, apellidos, turnos, excepciones, personalCabildo } = req.body;

        if (!id || !nombre || !apellidos) {
            return res.status(400).json({
                status: 'error',
                mensaje: 'Faltan campos obligatorios (id, nombre, apellidos)'
            });
        }

        const recursos = await leerDatos();

        const trabajadorExistente = recursos.find(r => r.id === id);
        if (trabajadorExistente) {
            return res.status(409).json({
                status: 'error',
                mensaje: 'Ya existe un trabajador con este ID',
                tipo: 'ID_DUPLICADO'
            });
        }

        const estado = determinarEstado(excepciones?.reincorporacion, excepciones?.vacaciones);

        const todosDias = ['lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado', 'domingo'];
        let disponibilidad = {};
        let diasNoDisponibles = [];

        if (personalCabildo) {
            // Si es personal del Cabildo, se guardan los días seleccionados y los días no seleccionados
            const diasSeleccionados = turnos || [];
            disponibilidad = diasSeleccionados;
            diasNoDisponibles = todosDias.filter(dia => !diasSeleccionados.includes(dia));
        } else {
            // Si no es personal del Cabildo, se usa el formato original con turnos diurnos/nocturnos
            disponibilidad = {};
            Object.entries(turnos || {}).forEach(([dia, turnosDelDia]) => {
                if (turnosDelDia.length > 0) {
                    disponibilidad[dia] = turnosDelDia;
                }
            });
            diasNoDisponibles = todosDias.filter(dia =>
                !Object.keys(disponibilidad).includes(dia.toLowerCase())
            );
        }

        const recurso = {
            id,
            nombre,
            apellidos,
            personalCabildo,
            estado,
            disponibilidad,
            excepciones: excepciones || {},
            diasNoDisponibles,
            timestamp: new Date().toISOString()
        };

        recursos.push(recurso);
        await guardarDatos(recursos);

        console.log('Datos recibidos y guardados:', recurso);

        res.json({
            status: 'ok',
            mensaje: 'Datos recibidos y guardados correctamente',
            datos: recurso
        });
    } catch (error) {
        console.error('Error al procesar la solicitud:', error);
        res.status(500).json({
            status: 'error',
            mensaje: error.message || 'Error interno del servidor'
        });
    }
});


app.put('/api/recursos/:id', async (req, res) => {
    try {
        const { id } = req.params;
        const { nombre, apellidos, turnos, excepciones, personalCabildo } = req.body;

        const recursos = await leerDatos();
        const index = recursos.findIndex(r => r.id === id);

        if (index === -1) {
            return res.status(404).json({
                status: 'error',
                mensaje: 'Recurso no encontrado'
            });
        }

        const todosDias = ['lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado', 'domingo'];
        let disponibilidad = [];
        let diasNoDisponibles = [];

        if (personalCabildo) {
            // Si es del Cabildo, guardamos solo los días seleccionados en disponibilidad
            disponibilidad = turnos || [];
            diasNoDisponibles = todosDias.filter(dia => !disponibilidad.includes(dia));
        } else {
            // Si NO es del Cabildo, mantenemos el formato de turnos diurnos/nocturnos
            disponibilidad = {};
            Object.entries(turnos || {}).forEach(([dia, turnosDelDia]) => {
                if (turnosDelDia.length > 0) {
                    disponibilidad[dia] = turnosDelDia;
                }
            });
            diasNoDisponibles = todosDias.filter(dia =>
                !Object.keys(disponibilidad).includes(dia.toLowerCase())
            );
        }

        recursos[index] = {
            ...recursos[index],
            nombre,
            apellidos,
            personalCabildo,
            estado: determinarEstado(excepciones?.reincorporacion, excepciones?.vacaciones),
            disponibilidad,
            excepciones: excepciones || {},
            diasNoDisponibles,
            timestamp: new Date().toISOString()
        };

        await guardarDatos(recursos);

        res.json({
            status: 'ok',
            mensaje: 'Datos actualizados correctamente',
            datos: recursos[index]
        });
    } catch (error) {
        console.error('Error al actualizar recurso:', error);
        res.status(500).json({
            status: 'error',
            mensaje: 'Error interno del servidor'
        });
    }
});



app.get('/api/recursos/:id', async (req, res) => {
    try {
        const { id } = req.params;
        const recursos = await leerDatos();
        const recurso = recursos.find(r => r.id === id)

        if (!recurso) {
            return res.status(404).json({
                status: 'error',
                mensaje: 'Recurso no encontrado'
            });
        }

        res.json(recurso);
    } catch (error) {
        console.error('Error al obtener recurso:', error);
        res.status(500).json({
            status: 'error',
            mensaje: 'Error interno del servidor'
        });
    }
});

app.get('/api/recursos', async (req, res) => {
    try {
        const recursos = await leerDatos();
        res.json({
            status: 'ok',
            total: recursos.length,
            recursos
        });
    } catch (error) {
        console.error('Error al obtener recursos:', error);
        res.status(500).json({
            status: 'error',
            mensaje: 'Error interno del servidor'
        });
    }
});

app.get('/start-server', (req, res) => {
    res.send('El servidor ya está en ejecución.');
});

app.listen(port, () => {
    console.log(`Servidor corriendo en http://localhost:${port}`);
});
