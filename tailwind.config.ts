import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        // ORLA³ Official Brand Colors (6 Core Colors)
        // Source: Brand Guidelines 02/2025

        // Main Colors: Gold (Energy, Sun, Orla the Gold Lady)
        'gold': {
          DEFAULT: '#dbb12a',    // C12 M29 Y100 K2.5 - Gold
          intense: '#ae8b0f',    // C26 M38 Y100 K15 - Intense Gold
        },

        // Additional Colors: Blue (Trust, Royalty, Balance)
        'cobalt': {
          DEFAULT: '#2d2e83',    // C99 M94 Y4 K0 - Cobalt Blue (Trust)
        },
        'royal': {
          DEFAULT: '#29235c',    // C100 M100 Y29 K19 - Royal Blue (Royalty, Balance)
        },

        // Text & Background (Purity, Authority, Clarity)
        // Black: #000000 - Authority, Elegance
        // White: #ffffff - Purity, Clarity, Transparency, Innovation

        // Extended Palette: Neutral Grays (UI Elements Only - Never for Branding)
        // These are for functional UI elements like text, borders, disabled states
        'gray': {
          50: '#f9fafb',         // Very light backgrounds
          100: '#f3f4f6',        // Light backgrounds, hover states
          200: '#e5e7eb',        // Borders, dividers
          300: '#d1d5db',        // Disabled borders
          400: '#9ca3af',        // Placeholder text, disabled text
          500: '#6b7280',        // Secondary text
          600: '#4b5563',        // Body text
          700: '#374151',        // Dark text
          800: '#1f2937',        // Very dark text
          900: '#111827',        // Near black
        },
        'slate': {
          900: '#0f172a',        // App background gradient
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
