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

app.post('/api/recursos', async (req, res) => {
    try {
        const { id, nombre, apellidos, turnos, excepciones } = req.body;

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

        // Validar que las vacaciones estén después de la reincorporación si es necesario
        if (excepciones?.vacaciones?.inicio) {
            validarVacaciones(excepciones.reincorporacion, excepciones.vacaciones.inicio);
        }

        const recurso = {
            id,
            nombre,
            apellidos,
            estado,
            disponibilidad: turnos,
            excepciones: excepciones || {},
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
        const { nombre, apellidos, turnos, excepciones } = req.body;

        const recursos = await leerDatos();
        const index = recursos.findIndex(r => r.id === id);

        if (index === -1) {
            return res.status(404).json({
                status: 'error',
                mensaje: 'Recurso no encontrado'
            });
        }

        const todosDias = ['lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado', 'domingo'];

        const disponibilidad = {};
        Object.entries(turnos).forEach(([dia, turnosDelDia]) => {
            if (turnosDelDia.length > 0) {
                disponibilidad[dia] = turnosDelDia;
            }
        });

        const diasNoDisponibles = todosDias.filter(dia => !disponibilidad[dia]);

        recursos[index] = {
            ...recursos[index],
            nombre,
            apellidos,
            estado: determinarEstado(excepciones?.reincorporacion, excepciones?.vacaciones),
            disponibilidad,
            diasNoDisponibles,
            excepciones: excepciones || {},
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
