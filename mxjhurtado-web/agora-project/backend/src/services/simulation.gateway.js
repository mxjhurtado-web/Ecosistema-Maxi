const simulationService = require('./simulation.service');

module.exports = (io) => {
    io.on('connection', (socket) => {
        console.log(`Client connected: ${socket.id}`);

        let currentSimulationId = null;

        // Agent starts a simulation
        socket.on('start_simulation', async ({ userId, scenarioId }) => {
            try {
                const result = await simulationService.startSimulation(userId, scenarioId);
                currentSimulationId = result.simulationId;

                socket.emit('simulation_started', {
                    simulationId: result.simulationId,
                    scenario: result.scenario
                });

                console.log(`Simulation started: ${currentSimulationId}`);
            } catch (error) {
                socket.emit('error', { message: error.message });
            }
        });

        // Agent sends audio (simulated as text for now, or raw audio buffer)
        // For this MVP, we'll assume the frontend does STT or sends text for simplicity, 
        // OR sends a blob that we just log.
        // Let's implement the "Text" flow first as requested in the "Mock" phase, 
        // but keep the event name 'agent_audio' to show intent.
        socket.on('agent_audio', async ({ text, audioBlob }) => {
            if (!currentSimulationId) return;

            // If we received audioBlob, we would send it to STT service here.
            // For now, we expect 'text' to be passed (maybe frontend does WebSpeechAPI)
            const userText = text || "[Audio processing placeholder]";

            try {
                const aiResponse = await simulationService.processUserMessage(currentSimulationId, userText);

                // Emit response back to frontend
                socket.emit('ai_response', {
                    text: aiResponse.text,
                    audioUrl: aiResponse.audioUrl, // Frontend will play this
                    emotionalState: aiResponse.emotionalState
                });

            } catch (error) {
                socket.emit('error', { message: error.message });
            }
        });

        // End simulation
        socket.on('end_simulation', () => {
            if (currentSimulationId) {
                const result = simulationService.endSimulation(currentSimulationId);
                socket.emit('simulation_ended', { result });
                currentSimulationId = null;
            }
        });

        socket.on('disconnect', () => {
            if (currentSimulationId) {
                simulationService.endSimulation(currentSimulationId);
            }
            console.log(`Client disconnected: ${socket.id}`);
        });
    });
};
