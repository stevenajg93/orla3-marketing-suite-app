import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        // ORLA³ Brand Colors
        'cobalt': {
          DEFAULT: '#2d2e83',
          50: '#e8e8f7',
          100: '#d1d1ef',
          200: '#a3a3df',
          300: '#7575cf',
          400: '#4747bf',
          500: '#2d2e83',
          600: '#242569',
          700: '#1b1c4f',
          800: '#121235',
          900: '#09091b',
        },
        'gold': {
          DEFAULT: '#dbb12a',
          intense: '#ae8b0f',
          50: '#fef9e7',
          100: '#fdf3cf',
          200: '#fbe79f',
          300: '#f9db6f',
          400: '#f7cf3f',
          500: '#dbb12a',
          600: '#ae8b0f',
          700: '#826816',
          800: '#564510',
          900: '#2b2308',
        },
        'royal': {
          DEFAULT: '#29235c',
          50: '#e7e6f2',
          100: '#cfcde5',
          200: '#9f9bcb',
          300: '#6f69b1',
          400: '#3f3797',
          500: '#29235c',
          600: '#211c4a',
          700: '#191537',
          800: '#100e25',
          900: '#080712',
        },
      },
      fontFamily: {
        'graphik': ['Graphik', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
};
export default config;
