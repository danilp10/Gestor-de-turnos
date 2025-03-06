const express = require('express');
const cors = require('cors');
const fs = require('fs').promises;
const path = require('path');

const app = express();
const port = 5701;

app.use(cors());
app.use(express.json());

// Paths for configuration and other files
const CONFIGURACION_FILE = path.join(__dirname, 'configuracion.json');

// Función para guardar configuración
async function guardarConfiguracion(config) {
    try {
        // Convertir valores a números donde sea necesario
        const configuracionProcesada = {
            incendio: {
                dias: parseInt(config.incendio.dias),
                fechaInicio: config.incendio.fechaInicio,
                turnoDiurno: parseInt(config.incendio.turnoDiurno),
                turnoNocturno: parseInt(config.incendio.turnoNocturno)
            },
            noIncendio: {
                dias: parseInt(config.noIncendio.dias),
                fechaInicio: config.noIncendio.fechaInicio,
                cabildoPersonas: parseInt(config.noIncendio.cabildoPersonas),
                retenes: config.noIncendio.retenes.map(reten => ({
                    turno: parseInt(reten.turno),
                    personas: parseInt(reten.personas)
                }))
            }
        };

        // Guardar la configuración procesada
        await fs.writeFile(CONFIGURACION_FILE, JSON.stringify(configuracionProcesada, null, 2), 'utf8');
        console.log('Configuración guardada correctamente');
        return configuracionProcesada;
    } catch (error) {
        console.error('Error al guardar la configuración:', error);
        throw error;
    }
}

// Ruta para procesar configuración
app.post('/configuracion', async (req, res) => {
    try {
        // Validar que se reciba la configuración
        const config = req.body;

        if (!config || !config.incendio || !config.noIncendio) {
            return res.status(400).json({
                status: 'error',
                mensaje: 'Configuración inválida'
            });
        }

        // Guardar configuración
        const configuracionGuardada = await guardarConfiguracion(config);

        // Respuesta exitosa
        res.json({
            status: 'ok',
            mensaje: 'Configuración guardada con éxito',
            configuracion: configuracionGuardada
        });

    } catch (error) {
        console.error('Error en la ruta de configuración:', error);
        res.status(500).json({
            status: 'error',
            mensaje: 'Error interno del servidor',
            detalles: error.message
        });
    }
});

// Ruta para recuperar la configuración
app.get('/configuracion', async (req, res) => {
    try {
        // Leer el archivo de configuración
        const configuracion = await fs.readFile(CONFIGURACION_FILE, 'utf8');

        res.json({
            status: 'ok',
            configuracion: JSON.parse(configuracion)
        });
    } catch (error) {
        if (error.code === 'ENOENT') {
            // Si el archivo no existe, devolver un error específico
            return res.status(404).json({
                status: 'error',
                mensaje: 'No se ha guardado ninguna configuración aún'
            });
        }

        console.error('Error al recuperar la configuración:', error);
        res.status(500).json({
            status: 'error',
            mensaje: 'Error interno del servidor',
            detalles: error.message
        });
    }
});

app.listen(port, () => {
    console.log(`Servidor corriendo en http://localhost:${port}`);
});
