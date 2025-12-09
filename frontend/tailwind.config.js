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
          DEFAULT: '#32CD32',
          50: '#E8F9E8',
          100: '#D1F4D1',
          200: '#A3E9A3',
          300: '#75DE75',
          400: '#47D347',
          500: '#32CD32',
          600: '#28A428',
          700: '#1E7B1E',
          800: '#145214',
          900: '#0A290A',
        },
        secondary: {
          DEFAULT: '#CD3280',
          50: '#F9E8F2',
          100: '#F4D1E5',
          200: '#E9A3CB',
          300: '#DE75B1',
          400: '#D34797',
          500: '#CD3280',
          600: '#A42866',
          700: '#7B1E4D',
          800: '#521433',
          900: '#290A1A',
        },
      },
    },
  },
  plugins: [],
}
