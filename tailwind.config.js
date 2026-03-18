/** @type {import('tailwindcss').Config} */
module.exports = {
    content: [
        "./templates/**/*.html",
        "./**/templates/**/*.html",
    ],
    theme: {
        extend: {
            colors: {
                'brand-blue': '#0A2540',
                'brand-blue-light': '#1e3d59',
                'brand-accent': '#6366f1',
            },
            fontFamily: {
                sans: ['Inter', 'sans-serif'],
            },
        },
    },
    plugins: [],
}
