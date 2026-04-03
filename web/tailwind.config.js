/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: 'class',
  content: [
    "./templates/**/*.html",
    "./static/**/*.js",
  ],
  theme: {
    extend: {
      fontFamily: {
        display: ['"Cinzel"',        'Georgia', 'serif'],
        body:    ['"Crimson Text"',  'Georgia', 'serif'],
        ui:      ['"Inter"',         'system-ui', 'sans-serif'],
      },
      colors: {
        dsa: {
          red:     '#8B1A1A',
          gold:    '#C9A84C',
          dark:    '#0c0a09',
          parchment: '#f5e6c8',
        },
        parchment: {
          50:  '#fdf9f0',
          100: '#f9f0da',
          200: '#f3e0b5',
          300: '#eacc88',
          400: '#dfb45a',
          500: '#d49d38',
          600: '#b9832d',
          700: '#996626',
          800: '#7d5125',
          900: '#674322',
          950: '#3a2210',
        },
      },
      boxShadow: {
        'glow-amber': '0 0 20px -4px rgba(201, 168, 76, 0.3)',
        'glow-red':   '0 0 20px -4px rgba(139, 26, 26, 0.4)',
        'parchment':  '0 2px 12px 0 rgba(58, 34, 16, 0.15)',
      },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
      },
    },
  },
  plugins: [],
}
