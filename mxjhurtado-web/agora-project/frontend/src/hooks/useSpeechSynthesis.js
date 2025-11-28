import { useState, useEffect, useRef } from 'react';

const useSpeechSynthesis = () => {
    const [isSpeaking, setIsSpeaking] = useState(false);
    const [voices, setVoices] = useState([]);
    const synth = window.speechSynthesis;

    useEffect(() => {
        const updateVoices = () => {
            setVoices(synth.getVoices());
        };

        updateVoices();
        if (synth.onvoiceschanged !== undefined) {
            synth.onvoiceschanged = updateVoices;
        }
    }, [synth]);

    const speak = (text) => {
        if (!synth) return;

        // Cancel any current speaking
        synth.cancel();

        const utterance = new SpeechSynthesisUtterance(text);

        // Try to find a Spanish voice
        const spanishVoice = voices.find(voice => voice.lang.includes('es'));
        if (spanishVoice) {
            utterance.voice = spanishVoice;
        }

        utterance.onstart = () => setIsSpeaking(true);
        utterance.onend = () => setIsSpeaking(false);
        utterance.onerror = () => setIsSpeaking(false);

        synth.speak(utterance);
    };

    const cancel = () => {
        if (synth) {
            synth.cancel();
            setIsSpeaking(false);
        }
    };

    return {
        speak,
        cancel,
        isSpeaking,
        hasSupport: !!window.speechSynthesis
    };
};

export default useSpeechSynthesis;
