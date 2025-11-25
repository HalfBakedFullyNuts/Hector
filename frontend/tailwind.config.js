/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          blue: '#A7D9EE',
          'blue-dark': '#8BC8DE',
          green: '#BEE6BE',
          'green-dark': '#A8D6A8',
        },
        base: {
          white: '#FFFFFF',
          'off-white': '#F8F8F8',
        },
        text: {
          dark: '#333333',
          light: '#666666',
          placeholder: '#999999',
        },
        border: {
          light: '#CCCCCC',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
      },
      borderRadius: {
        'button': '0.375rem', // 6px
        'input': '0.5rem',    // 8px
        'card': '0.75rem',    // 12px
      },
      boxShadow: {
        'card': '0px 2px 8px rgba(0, 0, 0, 0.1)',
      },
    },
  },
  plugins: [],
}
