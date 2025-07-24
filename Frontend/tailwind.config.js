const { nextui } = require("@nextui-org/react");

/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
    "./node_modules/@nextui-org/theme/dist/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      keyframes: {
        gradient: {
          '0%': { backgroundPosition: '0% 50%' },
          '100%': { backgroundPosition: '100% 50%' },
        },
      },
      animation: {
        gradient: 'gradient 4s linear infinite',
      },
    },
  },
  darkMode: "class",
  plugins: [
    nextui({
      themes: {
       
       
      
        light: {
          // ...
          colors: {
            primary: "#3B8A58",
            danger: "#E66D57",
          },
        },
        dark: {
          // ...
          colors: {
            background: "#141518",
            primary: "#FFFFFF",
            danger: "#E66D57",
            secondary: "#FFC107",
            text: "#FFFFFF",
          },
        },
        // ... custom themes
      },
    }),
    require("tailwind-scrollbar"),
  ],
};
