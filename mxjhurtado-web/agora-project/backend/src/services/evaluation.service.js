// In a real app, this would call an LLM with the transcript and rubric.
// For now, we'll use a mock evaluation logic.

class EvaluationService {
    async evaluateSimulation(simulationHistory, scenario) {
        console.log('Evaluating simulation...');

        // Mock evaluation delay
        await new Promise(resolve => setTimeout(resolve, 1500));

        // Simple mock logic: length of conversation determines score
        const turnCount = simulationHistory.length;
        let score = 70;
        if (turnCount > 4) score += 10;
        if (turnCount > 8) score += 10;
        if (score > 100) score = 100;

        return {
            score: score,
            criteria: [
                { name: "Saludo y Presentación", passed: true, comment: "Buen saludo inicial." },
                { name: "Manejo de Objeciones", passed: turnCount > 4, comment: turnCount > 4 ? "Bien manejado." : "Faltó profundizar." },
                { name: "Cierre de Llamada", passed: true, comment: "Despedida correcta." }
            ],
            strengths: ["Voz clara", "Amabilidad"],
            improvements: ["Escucha activa", "Confirmar datos más rápido"],
            summary: "Buena simulación en general. El agente mantuvo la calma."
        };
    }
}

module.exports = new EvaluationService();
