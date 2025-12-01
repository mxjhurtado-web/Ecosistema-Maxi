const express = require('express');
const http = require('http');
const { Server } = require('socket.io');
const cors = require('cors');
const dotenv = require('dotenv');
const connectDB = require('./config/db');

// Load env vars
dotenv.config();

// Connect to Database
// Connect to Database and Auto-Seed
connectDB().then(async () => {
    const Scenario = require('./models/scenario.model');
    const count = await Scenario.countDocuments();
    if (count === 0) {
        console.log("Database empty. Seeding default scenarios...");
        await Scenario.create([
            {
                title: "Cliente Molesto por Cargo Desconocido",
                description: "El cliente ve un cargo de $500 MXN que no reconoce en su estado de cuenta.",
                customerType: "angry",
                objective: "Calmar al cliente, validar su identidad y explicar que el cargo es una pre-autorización que desaparecerá en 24 horas.",
                baseScript: "El cliente iniciará reclamando. Debes pedirle los últimos 4 dígitos de la tarjeta. Si valida, explícale lo de la pre-autorización.",
                difficulty: "medium"
            }
        ]);
        console.log("Default scenarios seeded!");
    }
});

const app = express();
const server = http.createServer(app);

// Middleware
app.use(cors());
app.use(express.json());

// Routes
app.use('/api/auth', require('./routes/auth.routes'));
app.use('/api/scenarios', require('./routes/scenario.routes'));
app.use('/api/simulation', require('./routes/simulation.routes'));
app.use('/api/evaluation', require('./routes/evaluation.routes'));

// Socket.io Setup for Real-time Voice/Simulation
const io = new Server(server, {
    cors: {
        origin: "*", // Allow all for dev, restrict in prod
        methods: ["GET", "POST"]
    }
});

// Socket.io Logic (Move to a separate handler in a real app)
const simulationGateway = require('./services/simulation.gateway');
simulationGateway(io);

const PORT = process.env.PORT || 5000;

server.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
});
