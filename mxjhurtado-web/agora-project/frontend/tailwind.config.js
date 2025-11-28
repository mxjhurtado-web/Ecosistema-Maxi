/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                primary: '#2563eb', // Blue 600
                secondary: '#475569', // Slate 600
                accent: '#f59e0b', // Amber 500
                background: '#f8fafc', // Slate 50
                surface: '#ffffff',
            }
        },
    },
    plugins: [],
}
