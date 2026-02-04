/**
 * Indicador de semáforo
 */

import { SemaforoLevel } from '../../types/job';

interface SemaforoIndicatorProps {
    level: SemaforoLevel;
    score: number;
    size?: 'sm' | 'md' | 'lg';
}

export const SemaforoIndicator = ({ level, score, size = 'md' }: SemaforoIndicatorProps) => {
    const colors = {
        verde: {
            bg: 'bg-semaforo-verde',
            text: 'text-semaforo-verde',
            label: 'VERDE',
        },
        amarillo: {
            bg: 'bg-semaforo-amarillo',
            text: 'text-semaforo-amarillo',
            label: 'AMARILLO',
        },
        rojo: {
            bg: 'bg-semaforo-rojo',
            text: 'text-semaforo-rojo',
            label: 'ROJO',
        },
    };

    const sizes = {
        sm: { dot: 'w-3 h-3', text: 'text-sm' },
        md: { dot: 'w-4 h-4', text: 'text-base' },
        lg: { dot: 'w-6 h-6', text: 'text-lg' },
    };

    const config = colors[level];
    const sizeConfig = sizes[size];

    return (
        <div className="flex items-center gap-2">
            <div className={`${config.bg} ${sizeConfig.dot} rounded-full`} />
            <span className={`font-semibold ${config.text} ${sizeConfig.text}`}>
                {config.label}
            </span>
            <span className={`text-gray-500 ${sizeConfig.text}`}>
                Score: {score}/100
            </span>
        </div>
    );
};
