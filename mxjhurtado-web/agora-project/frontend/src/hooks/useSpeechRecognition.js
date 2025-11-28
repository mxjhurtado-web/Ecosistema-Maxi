import { useState, useEffect, useRef } from 'react';

const useSpeechRecognition = () => {
    const [isListening, setIsListening] = useState(false);
    const [transcript, setTranscript] = useState('');
    const [error, setError] = useState(null);
    const recognitionRef = useRef(null);

    useEffect(() => {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

        if (!SpeechRecognition) {
            setError('Browser does not support Speech Recognition');
            return;
        }

        const recognition = new SpeechRecognition();
        recognition.continuous = false; // Stop after one sentence/phrase
        recognition.interimResults = true;
        recognition.lang = 'es-ES'; // Spanish

        recognition.onstart = () => {
            setIsListening(true);
            setError(null);
        };

        recognition.onresult = (event) => {
            let interimTranscript = '';
            let finalTranscript = '';

            for (let i = event.resultIndex; i < event.results.length; ++i) {
                if (event.results[i].isFinal) {
                    finalTranscript += event.results[i][0].transcript;
                } else {
                    interimTranscript += event.results[i][0].transcript;
                }
            }

            // We prefer final, but show interim if that's all we have
            setTranscript(finalTranscript || interimTranscript);
        };

        recognition.onerror = (event) => {
            console.error("Speech recognition error", event.error);
            setError(`Error: ${event.error}`);
            setIsListening(false);
        };

        recognition.onend = () => {
            setIsListening(false);
        };

        recognitionRef.current = recognition;
    }, []);

    const startListening = () => {
        if (recognitionRef.current && !isListening) {
            setTranscript('');
            try {
                recognitionRef.current.start();
            } catch (e) {
                console.error("Error starting recognition:", e);
            }
        }
    };

    const stopListening = () => {
        if (recognitionRef.current && isListening) {
            recognitionRef.current.stop();
        }
    };

    return {
        isListening,
        transcript,
        startListening,
        stopListening,
        error,
        hasSupport: !!(window.SpeechRecognition || window.webkitSpeechRecognition)
    };
};

export default useSpeechRecognition;
