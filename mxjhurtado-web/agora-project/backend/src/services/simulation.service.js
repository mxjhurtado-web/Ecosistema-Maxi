const getAIAdapter = require('../adapters/ai.adapter');
const Scenario = require('../models/scenario.model');

class SimulationService {
    constructor() {
        this.aiAdapter = getAIAdapter();
        this.activeSimulations = new Map(); // Store active simulation states
    }

    async startSimulation(userId, scenarioId) {
        const scenario = await Scenario.findById(scenarioId);
        if (!scenario) throw new Error('Scenario not found');

        const simulationId = `${userId}-${Date.now()}`;

        this.activeSimulations.set(simulationId, {
            userId,
            scenario,
            history: [],
            startTime: Date.now(),
        });

        return {
            simulationId,
            initialMessage: "Simulación iniciada. El cliente está esperando.",
            scenario: scenario
        };
    }

    async processUserMessage(simulationId, userText) {
        const simState = this.activeSimulations.get(simulationId);
        if (!simState) throw new Error('Simulation not found');

        // Add user message to history
        simState.history.push({ role: 'agent', content: userText });

        // Get AI response
        const aiResponse = await this.aiAdapter.generateResponse(
            simState.scenario,
            simState.history,
            userText
        );

        // Add AI response to history
        simState.history.push({ role: 'customer', content: aiResponse.text });

        return aiResponse;
    }

    endSimulation(simulationId) {
        const simState = this.activeSimulations.get(simulationId);
        if (simState) {
            const duration = Date.now() - simState.startTime;
            this.activeSimulations.delete(simulationId);
            return {
                history: simState.history,
                duration,
                scenario: simState.scenario
            };
        }
        return null;
    }
}

module.exports = new SimulationService();
