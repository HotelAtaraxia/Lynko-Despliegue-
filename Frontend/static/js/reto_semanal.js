// --- FUNCIONES PARA EL MODAL DEL RETO ---
function abrirModalReto() {
    const modal = document.getElementById('modalReto');
    if (modal) {
        modal.style.display = 'flex';
        document.body.style.overflow = 'hidden'; // Evita scroll de fondo
    }
}

function cerrarModalReto() {
    const modal = document.getElementById('modalReto');
    if (modal) {
        modal.style.display = 'none';
        document.body.style.overflow = 'auto'; // Restaura el scroll
    }
}

// --- LÓGICA DE NOTIFICACIONES Y CARGA INICIAL ---
document.addEventListener("DOMContentLoaded", function () {
    const btnCampanita = document.getElementById("btnCampanita");
    const modalNotificaciones = document.getElementById("modalNotificacionesGlobal");
    const cerrarModalBtn = document.getElementById("cerrarModalNotificaciones");
    const contenedorNotificaciones = document.getElementById("listaNotificacionesContenedor");
    const badgeNotificaciones = document.querySelector(".notification-badge");

    // Variables globales inyectadas desde el HTML/Jinja2 (definidas previamente en el template)
    if (typeof notificacionesData !== 'undefined' && typeof noLeidasCount !== 'undefined') {
        // Mostrar u ocultar el badge rojo con el número de no leídas
        if (badgeNotificaciones) {
            if (noLeidasCount > 0) {
                badgeNotificaciones.style.display = "inline-block";
                badgeNotificaciones.textContent = noLeidasCount;
            } else {
                badgeNotificaciones.style.display = "none";
            }
        }
    }

    // Abrir el modal de notificaciones al hacer clic en la campanita
    if (btnCampanita && modalNotificaciones) {
        btnCampanita.addEventListener("click", function () {
            modalNotificaciones.style.display = "flex";
            document.body.style.overflow = "hidden";
            renderizarNotificaciones();
        });
    }

    // Cerrar el modal con el botón de la "X"
    if (cerrarModalBtn && modalNotificaciones) {
        cerrarModalBtn.addEventListener("click", function () {
            modalNotificaciones.style.display = "none";
            document.body.style.overflow = "auto";
        });
    }

    // Cerrar el modal de notificaciones si se hace clic fuera del contenido
    if (modalNotificaciones) {
        modalNotificaciones.addEventListener("click", function (event) {
            if (event.target === modalNotificaciones) {
                modalNotificaciones.style.display = "none";
                document.body.style.overflow = "auto";
            }
        });
    }

    // Función interna para pintar las notificaciones
    function renderizarNotificaciones() {
        if (typeof notificacionesData === 'undefined' || !notificacionesData || notificacionesData.length === 0) {
            contenedorNotificaciones.innerHTML = `
                <div style="text-align: center; color: #718096; padding: 20px;">
                    <p style="font-size: 30px; margin: 0 0 10px 0;">📭</p>
                    <p style="margin: 0; font-weight: 500;">No tienes notificaciones recientes.</p>
                </div>`;
            return;
        }

        let htmlContenido = "";
        notificacionesData.forEach(notif => {
            let bgColor = notif.leida ? "#f8fafc" : "#fff7ed"; 
            let borderColor = notif.leida ? "#e2e8f0" : "#fdba74";
            
            htmlContenido += `
                <div style="background: ${bgColor}; border: 1px solid ${borderColor}; padding: 12px 15px; border-radius: 12px; position: relative;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 5px;">
                        <strong style="color: #2d3748; font-size: 14px;">${notif.titulo}</strong>
                        <span style="font-size: 11px; color: #a0aec0;">${notif.fecha_creacion || ''}</span>
                    </div>
                    <p style="margin: 0; color: #4a5568; font-size: 13px;">${notif.mensaje}</p>
                </div>
            `;
        });

        contenedorNotificaciones.innerHTML = htmlContenido;
    }
});