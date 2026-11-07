/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#fff5f5',
          100: '#fed7d7',
          500: '#e53e3e',
          600: '#c53030',
          700: '#9b2c2c',
          900: '#742a2a',
        },
        dark: {
          900: '#0f1117',
          800: '#161922',
          700: '#1f2430',
          600: '#2b3142',
        }
      }
    },
  },
  plugins: [],
}
