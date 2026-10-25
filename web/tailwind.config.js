/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        horizon: {
          blue: '#1e40af',
          teal: '#0f766e',
          dark: '#0f172a',
          card: '#1e293b',
          border: '#334155',
          muted: '#94a3b8',
        },
      },
    },
  },
  plugins: [],
}
