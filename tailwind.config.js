/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: 'class',
  content: [
    "./public/**/*.{html,js}",
    "./content_publisher.py"
  ],
  theme: {
    extend: {
      colors: {
        brand: '#6366f1',
      }
    },
  },
  plugins: [],
}
