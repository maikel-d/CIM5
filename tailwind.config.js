/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './templates/**/*.html',
    './direccion/templates/**/*.html',
    './static/js/**/*.js',
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          DEFAULT: '#003363',
          dark: '#002244',
          light: '#00508a',
          bg: '#e8f0f8',
        },
      },
    },
  },
  plugins: [],
}
