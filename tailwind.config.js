/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: {
          dark: '#121212',
          DEFAULT: '#171717',
          light: '#1e1e1e'
        },
        primary: {
          dark: '#0a84ff',
          DEFAULT: '#0a84ff',
          light: '#33a1ff'
        },
        secondary: {
          dark: '#00c16e',
          DEFAULT: '#00d170',
          light: '#33da8a'
        },
        accent: {
          purple: '#bf5af2',
          pink: '#ff2d55',
          orange: '#ff9f0a',
          yellow: '#ffd60a',
          teal: '#5ac8fa',
          indigo: '#5e5ce6'
        },
        glass: {
          DEFAULT: 'rgba(255, 255, 255, 0.05)',
          strong: 'rgba(255, 255, 255, 0.1)',
          weak: 'rgba(255, 255, 255, 0.02)'
        }
      },
      fontFamily: {
        sans: ['Inter var', 'Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
        display: ['Audiowide', 'sans-serif']
      },
      boxShadow: {
        'neon-primary': '0 0 5px theme(colors.primary.DEFAULT), 0 0 20px rgba(10, 132, 255, 0.5)',
        'neon-secondary': '0 0 5px theme(colors.secondary.DEFAULT), 0 0 20px rgba(0, 209, 112, 0.5)',
        'neon-purple': '0 0 5px theme(colors.accent.purple), 0 0 20px rgba(191, 90, 242, 0.5)',
        'neon-pink': '0 0 5px theme(colors.accent.pink), 0 0 20px rgba(255, 45, 85, 0.5)',
        'neon-glow': '0 0 10px rgba(255, 255, 255, 0.3)',
        'glass': '0 8px 32px rgba(0, 0, 0, 0.1)',
      },
      backdropBlur: {
        xs: '2px',
      },
    },
  },
  plugins: [],
}