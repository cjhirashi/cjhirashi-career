// Paleta armonica del proyecto (ver COLOR_PALETTE.md en la raiz):
//   Morado  #A855F7 -> cliente / entrada de datos / accion primaria
//   Verde   #10B981 -> servidor / procesamiento / exito
//   Cyan    #06B6D4 -> almacenamiento / documentacion / informacion
export default {
    darkMode: "class",
    content: ["./index.html", "./src/**/*.{ts,tsx}"],
    theme: {
        extend: {
            colors: {
                brand: {
                    purple: {
                        50: "#faf5ff",
                        100: "#f3e8ff",
                        200: "#e9d5ff",
                        300: "#d8b4fe",
                        400: "#c084fc",
                        500: "#a855f7",
                        600: "#9333ea",
                        700: "#7e22ce",
                        800: "#6b21a8",
                        900: "#581c87",
                    },
                    green: {
                        50: "#ecfdf5",
                        100: "#d1fae5",
                        200: "#a7f3d0",
                        300: "#6ee7b7",
                        400: "#34d399",
                        500: "#10b981",
                        600: "#059669",
                        700: "#047857",
                        800: "#065f46",
                        900: "#064e3b",
                    },
                    cyan: {
                        50: "#ecfeff",
                        100: "#cffafe",
                        200: "#a5f3fc",
                        300: "#67e8f9",
                        400: "#22d3ee",
                        500: "#06b6d4",
                        600: "#0891b2",
                        700: "#0e7490",
                        800: "#155e75",
                        900: "#164e63",
                    },
                },
            },
            fontFamily: {
                sans: [
                    "Inter",
                    "ui-sans-serif",
                    "system-ui",
                    "-apple-system",
                    "Segoe UI",
                    "Roboto",
                    "sans-serif",
                ],
            },
            animation: {
                "fade-in": "fadeIn 0.2s ease-out",
                "slide-up": "slideUp 0.25s ease-out",
                "toast-in": "toastIn 0.25s ease-out",
            },
            keyframes: {
                fadeIn: {
                    "0%": { opacity: "0" },
                    "100%": { opacity: "1" },
                },
                slideUp: {
                    "0%": { opacity: "0", transform: "translateY(8px)" },
                    "100%": { opacity: "1", transform: "translateY(0)" },
                },
                toastIn: {
                    "0%": { opacity: "0", transform: "translateX(16px)" },
                    "100%": { opacity: "1", transform: "translateX(0)" },
                },
            },
        },
    },
    plugins: [],
};
