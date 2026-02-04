/**
 * Badge de país
 */

interface CountryBadgeProps {
    country: {
        code: string;
        name: string;
    };
}

export const CountryBadge = ({ country }: CountryBadgeProps) => {
    if (!country || !country.code) {
        return null;
    }

    return (
        <div className="inline-flex items-center gap-2 px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm font-medium">
            <span className="text-lg">{getFlagEmoji(country.code)}</span>
            <span>{country.name}</span>
        </div>
    );
};

// Helper para obtener emoji de bandera
const getFlagEmoji = (countryCode: string): string => {
    const codePoints = countryCode
        .toUpperCase()
        .split('')
        .map(char => 127397 + char.charCodeAt(0));
    return String.fromCodePoint(...codePoints);
};
