/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./templates/**/*.html",
    "./static/**/*.js",
  ],
  theme: {
    extend: {
      fontFamily: {
        display: ['"Cinzel"', 'Georgia', 'serif'],
        body:    ['"Inter"', 'system-ui', 'sans-serif'],
      },
      colors: {
        dsa: {
          red:    '#8B1A1A',
          gold:   '#C9A84C',
          dark:   '#0c0a09',
        },
      },
    },
  },
  plugins: [],
}
