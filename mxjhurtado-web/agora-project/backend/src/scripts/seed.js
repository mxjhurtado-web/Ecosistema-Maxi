const mongoose = require('mongoose');
const dotenv = require('dotenv');
const Scenario = require('../models/scenario.model');
const connectDB = require('../config/db');

dotenv.config();

const seedScenarios = [
    {
        title: "Cliente Molesto por Cargo Desconocido",
        description: "El cliente ve un cargo de $500 MXN que no reconoce en su estado de cuenta.",
        customerType: "angry",
        objective: "Calmar al cliente, validar su identidad y explicar que el cargo es una pre-autorización que desaparecerá en 24 horas.",
        baseScript: "El cliente iniciará reclamando. Debes pedirle los últimos 4 dígitos de la tarjeta. Si valida, explícale lo de la pre-autorización.",
        difficulty: "medium"
    }
];

const seedDB = async () => {
    try {
        await connectDB();

        // Clear existing scenarios
        await Scenario.deleteMany();
        console.log('Scenarios cleared...');

        // Add seed scenarios
        await Scenario.insertMany(seedScenarios);
        console.log('Sample scenario added!');

        process.exit();
    } catch (error) {
        console.error(error);
        process.exit(1);
    }
};

seedDB();
