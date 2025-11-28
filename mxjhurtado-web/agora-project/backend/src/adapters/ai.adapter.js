const { GoogleGenerativeAI } = require("@google/generative-ai");

// Abstract Base Class (Conceptual)
class AIAdapter {
    async generateResponse(context, history, userText) {
        throw new Error('Method not implemented');
    }
}

// Mock Implementation
class MockAIAdapter extends AIAdapter {
    async generateResponse(context, history, userText) {
        console.log('Mock AI generating response...');

        // Simple keyword matching for demo purposes
        let responseText = "Entiendo lo que me dice. ¿Podría explicarme más?";
        let emotionalState = "neutral";

        if (userText.toLowerCase().includes('hola')) {
            responseText = "Hola, estoy llamando porque tengo un problema con mi cuenta.";
            emotionalState = "annoyed";
        } else if (userText.toLowerCase().includes('cancelar')) {
            responseText = "¿Por qué es tan difícil cancelar? ¡Solo quiero mi dinero de vuelta!";
            emotionalState = "angry";
        } else if (userText.toLowerCase().includes('calme')) {
            responseText = "Está bien, intentaré calmarme. Pero necesito una solución.";
            emotionalState = "calm";
        }

        // Simulate network delay
        await new Promise(resolve => setTimeout(resolve, 1000));

        return {
            text: responseText,
            audioUrl: null, // In a real app, this would be a URL or binary stream
            emotionalState: emotionalState,
            done: false
        };
    }
}

// Gemini Implementation
class GeminiAIAdapter extends AIAdapter {
    constructor(apiKey) {
        super();
        this.genAI = new GoogleGenerativeAI(apiKey);
        this.model = this.genAI.getGenerativeModel({ model: "gemini-pro" });
    }

    async generateResponse(scenario, history, userText) {
        try {
            // Construct the prompt
            // 1. System Instruction / Persona
            let prompt = `Actúa como un cliente en una llamada telefónica con un agente de servicio al cliente.
  
  CONTEXTO DEL ESCENARIO:
  - Título: ${scenario.title}
  - Descripción: ${scenario.description}
  - Tu personalidad/estado actual: ${scenario.customerType}
  - Tu objetivo: ${scenario.objective} (Esto es lo que el agente debe lograr, tú debes reaccionar a sus intentos).
  
  INSTRUCCIONES:
  - Responde de manera natural, conversacional y breve (como en una llamada real).
  - Mantén tu personalidad definida. Si estás molesto, demuéstralo pero sin ser incoherente.
  - Si el agente lo hace bien, puedes calmarte. Si lo hace mal, puedes molestarte más.
  - TU SALIDA DEBE SER ESTRICTAMENTE UN JSON con este formato:
  {
    "text": "Tu respuesta verbal aquí",
    "emotionalState": "tu estado emocional actual (angry, neutral, happy, confused, nervous)",
    "done": boolean (true si consideras que la llamada terminó o se resolvió, false si debe continuar)
  }
  
  HISTORIAL DE CONVERSACIÓN:
  `;

            // 2. Add History
            history.forEach(msg => {
                const role = msg.role === 'agent' ? 'Agente' : 'Cliente (Tú)';
                prompt += `${role}: ${msg.content}\n`;
            });

            // 3. Add current user input
            prompt += `Agente: ${userText}\n`;
            prompt += `Cliente (Tú):`;

            const result = await this.model.generateContent(prompt);
            const response = await result.response;
            const text = response.text();

            // Clean markdown code blocks if present
            const jsonString = text.replace(/```json/g, '').replace(/```/g, '').trim();

            try {
                const parsed = JSON.parse(jsonString);
                return {
                    text: parsed.text,
                    audioUrl: null,
                    emotionalState: parsed.emotionalState || 'neutral',
                    done: parsed.done || false
                };
            } catch (e) {
                console.error("Error parsing JSON from Gemini:", e);
                // Fallback if JSON parsing fails
                return {
                    text: text,
                    audioUrl: null,
                    emotionalState: 'neutral',
                    done: false
                };
            }

        } catch (error) {
            console.error("Gemini API Error:", error);
            return {
                text: "Hubo un error de conexión. ¿Me escuchas?",
                audioUrl: null,
                emotionalState: 'neutral',
                done: false
            };
        }
    }
}

// Factory
const getAIAdapter = () => {
    // Logic to choose adapter based on env vars
    // We check if GEMINI_API_KEY is present and not the placeholder
    if (process.env.GEMINI_API_KEY && process.env.GEMINI_API_KEY.length > 10) {
        console.log("Using Gemini AI Adapter");
        return new GeminiAIAdapter(process.env.GEMINI_API_KEY);
    }
    console.log("Using Mock AI Adapter");
    return new MockAIAdapter();
};

module.exports = getAIAdapter;
