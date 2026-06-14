import type { Config } from 'tailwindcss'

export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Nunito', 'sans-serif'],
      },
      colors: {
        navy: {
          DEFAULT: '#1E3A5F',
          dark: '#162D4A',
          light: '#2A4A72',
        },
      },
      keyframes: {
        'bounce-dot': {
          '0%, 60%, 100%': { transform: 'translateY(0)' },
          '30%': { transform: 'translateY(-5px)' },
        },
      },
      animation: {
        'bounce-dot': 'bounce-dot 0.9s infinite',
      },
    },
  },
  plugins: [],
} satisfies Config
