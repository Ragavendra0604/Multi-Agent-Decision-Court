/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        court: {
          dark: "#0b0f19",
          card: "#111827",
          border: "#1f2937",
          accent: "#6366f1",
          prosecution: "#ef4444",
          defense: "#10b981",
          judge: "#f59e0b",
        }
      }
    },
  },
  plugins: [],
}
