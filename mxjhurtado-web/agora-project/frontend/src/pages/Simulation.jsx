import React, { useEffect, useState, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { io } from 'socket.io-client';
import DashboardLayout from '../layout/DashboardLayout';
import { useAuthStore } from '../context/AuthContext';
import { Mic, Square, Send, User, Bot, Volume2, VolumeX } from 'lucide-react';
import useSpeechRecognition from '../hooks/useSpeechRecognition';
import useSpeechSynthesis from '../hooks/useSpeechSynthesis';

const Simulation = () => {
    const { id: scenarioId } = useParams();
    const { user } = useAuthStore();
    const navigate = useNavigate();

    const [socket, setSocket] = useState(null);
    const [messages, setMessages] = useState([]);
    const [inputText, setInputText] = useState('');
    const [scenario, setScenario] = useState(null);
    const [simulationId, setSimulationId] = useState(null);
    const messagesEndRef = useRef(null);

    // Voice Hooks
    const {
        isListening,
        transcript,
        startListening,
        stopListening,
        hasSupport: hasSTTSupport
    } = useSpeechRecognition();

    const {
        speak,
        cancel: cancelSpeech,
        isSpeaking,
        hasSupport: hasTTSSupport
    } = useSpeechSynthesis();

    // Update input text when transcript changes
    useEffect(() => {
        if (transcript) {
            setInputText(transcript);
        }
    }, [transcript]);

    useEffect(() => {
        // Connect to Socket.io
        const newSocket = io('http://localhost:5000');
        setSocket(newSocket);

        newSocket.on('connect', () => {
            console.log('Connected to socket server');
            // Start simulation
            newSocket.emit('start_simulation', { userId: user._id, scenarioId });
        });

        newSocket.on('simulation_started', (data) => {
            setSimulationId(data.simulationId);
            setScenario(data.scenario);
            const initialMsg = 'Simulación iniciada. El cliente está en línea.';
            setMessages([{ role: 'system', content: initialMsg }]);
            speak(initialMsg);
        });

        newSocket.on('ai_response', (data) => {
            setMessages(prev => [...prev, {
                role: 'customer',
                content: data.text,
                emotionalState: data.emotionalState
            }]);

            // Speak the AI response
            speak(data.text);
        });

        newSocket.on('simulation_ended', (data) => {
            navigate('/evaluation', { state: { result: data.result } });
        });

        return () => {
            newSocket.close();
            cancelSpeech();
        };
    }, [scenarioId, user._id, navigate, speak, cancelSpeech]);

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    const handleSendMessage = (e) => {
        e.preventDefault();
        if (!inputText.trim()) return;

        // Optimistic update
        setMessages(prev => [...prev, { role: 'agent', content: inputText }]);

        // Send to backend
        socket.emit('agent_audio', { text: inputText });
        setInputText('');

        // Stop listening if we were (manual send overrides voice)
        if (isListening) stopListening();
    };

    const toggleRecording = () => {
        if (isListening) {
            stopListening();
        } else {
            startListening();
        }
    };

    const endSimulation = () => {
        if (socket) {
            socket.emit('end_simulation');
        }
    };

    return (
        <DashboardLayout>
            <div className="flex flex-col h-[calc(100vh-100px)]">
                {/* Header */}
                <div className="bg-white p-4 rounded-t-xl shadow-sm border-b flex justify-between items-center">
                    <div>
                        <h2 className="text-xl font-bold text-gray-800">{scenario?.title || 'Cargando escenario...'}</h2>
                        <p className="text-sm text-gray-500">{scenario?.customerType} - {scenario?.objective}</p>
                    </div>
                    <div className="flex items-center space-x-4">
                        {isSpeaking && (
                            <div className="flex items-center text-blue-600 text-sm animate-pulse">
                                <Volume2 size={16} className="mr-1" />
                                Hablando...
                            </div>
                        )}
                        <button
                            onClick={endSimulation}
                            className="bg-red-100 text-red-600 px-4 py-2 rounded-lg hover:bg-red-200 font-medium"
                        >
                            Terminar Llamada
                        </button>
                    </div>
                </div>

                {/* Chat Area */}
                <div className="flex-1 bg-gray-50 p-4 overflow-y-auto space-y-4">
                    {messages.map((msg, index) => (
                        <div key={index} className={`flex ${msg.role === 'agent' ? 'justify-end' : 'justify-start'}`}>
                            <div className={`max-w-[70%] rounded-2xl p-4 ${msg.role === 'agent'
                                ? 'bg-primary text-white rounded-tr-none'
                                : msg.role === 'system'
                                    ? 'bg-gray-200 text-gray-600 text-center w-full max-w-full'
                                    : 'bg-white text-gray-800 border border-gray-200 rounded-tl-none shadow-sm'
                                }`}>
                                {msg.role !== 'system' && (
                                    <div className="flex items-center space-x-2 mb-1 opacity-75 text-xs">
                                        {msg.role === 'agent' ? <User size={12} /> : <Bot size={12} />}
                                        <span className="capitalize">{msg.role === 'agent' ? 'Tú' : 'Cliente'}</span>
                                        {msg.emotionalState && <span className="text-xs bg-yellow-100 text-yellow-800 px-1 rounded">{msg.emotionalState}</span>}
                                    </div>
                                )}
                                <p>{msg.content}</p>
                            </div>
                        </div>
                    ))}
                    <div ref={messagesEndRef} />
                </div>

                {/* Input Area */}
                <div className="bg-white p-4 rounded-b-xl shadow-sm border-t">
                    <form onSubmit={handleSendMessage} className="flex items-center space-x-4">
                        {hasSTTSupport ? (
                            <button
                                type="button"
                                onClick={toggleRecording}
                                className={`p-3 rounded-full transition-all duration-200 ${isListening
                                    ? 'bg-red-500 text-white animate-pulse ring-4 ring-red-200'
                                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                                    }`}
                                title={isListening ? "Detener grabación" : "Iniciar grabación"}
                            >
                                {isListening ? <Square size={24} /> : <Mic size={24} />}
                            </button>
                        ) : (
                            <div className="text-xs text-red-500 w-20 text-center">No Mic Support</div>
                        )}

                        <input
                            type="text"
                            className="flex-1 border rounded-lg px-4 py-3 focus:outline-none focus:border-primary"
                            placeholder={isListening ? "Escuchando..." : "Escribe tu respuesta..."}
                            value={inputText}
                            onChange={(e) => setInputText(e.target.value)}
                        />

                        <button
                            type="submit"
                            className="bg-primary text-white p-3 rounded-lg hover:bg-blue-700 transition-colors"
                            disabled={!inputText.trim()}
                        >
                            <Send size={24} />
                        </button>
                    </form>
                </div>
            </div>
        </DashboardLayout>
    );
};

export default Simulation;
