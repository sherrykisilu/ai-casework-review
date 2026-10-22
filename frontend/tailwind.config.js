/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#172033",
        paper: "#f7f5ef",
        accent: "#0f766e",
        warning: "#b45309"
      }
    }
  },
  plugins: []
};
