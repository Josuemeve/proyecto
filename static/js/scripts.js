// scripts.js

// Función para ocultar alertas después de 3 segundos
document.addEventListener("DOMContentLoaded", () => {
    const alerts = document.querySelectorAll(".alert");
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.opacity = 0;
            setTimeout(() => alert.remove(), 500);
        }, 3000);
    });
});
