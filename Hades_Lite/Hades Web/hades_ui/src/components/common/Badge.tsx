/**
 * Badge component
 */

import { ReactNode } from 'react';

interface BadgeProps {
    children: ReactNode;
    color?: 'green' | 'yellow' | 'red' | 'blue' | 'gray';
    size?: 'sm' | 'md';
}

export const Badge = ({ children, color = 'gray', size = 'md' }: BadgeProps) => {
    const colorClasses = {
        green: 'bg-green-100 text-green-800',
        yellow: 'bg-yellow-100 text-yellow-800',
        red: 'bg-red-100 text-red-800',
        blue: 'bg-blue-100 text-blue-800',
        gray: 'bg-gray-100 text-gray-800',
    };

    const sizeClasses = {
        sm: 'px-2 py-0.5 text-xs',
        md: 'px-2.5 py-1 text-sm',
    };

    return (
        <span className={`inline-flex items-center rounded-full font-medium ${colorClasses[color]} ${sizeClasses[size]}`}>
            {children}
        </span>
    );
};
