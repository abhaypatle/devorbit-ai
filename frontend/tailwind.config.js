/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        midnight: "#0F172A",
        panel: "#1E293B",
        electric: "#2563EB",
        cyan: "#06B6D4",
      },
      boxShadow: {
        glow: "0 0 32px rgba(37, 99, 235, .18)",
      },
    },
  },
  plugins: [],
};
