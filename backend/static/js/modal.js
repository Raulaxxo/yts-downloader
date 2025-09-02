// === SISTEMA DE MODALES PERSONALIZADOS ===

class CustomModal {
    constructor() {
        this.overlay = null;
        this.container = null;
        this.isOpen = false;
        this.currentResolve = null;
    }

    // Crear la estructura HTML del modal
    createModal() {
        if (this.overlay) {
            this.overlay.remove();
        }

        this.overlay = document.createElement('div');
        this.overlay.className = 'modal-overlay';
        this.overlay.innerHTML = `
            <div class="modal-container">
                <div class="modal-icon"></div>
                <div class="modal-title"></div>
                <div class="modal-message"></div>
                <div class="modal-buttons"></div>
            </div>
        `;

        document.body.appendChild(this.overlay);
        this.container = this.overlay.querySelector('.modal-container');

        // Cerrar al hacer clic en el overlay (no en el contenedor)
        this.overlay.addEventListener('click', (e) => {
            if (e.target === this.overlay) {
                this.close(false);
            }
        });

        // Prevenir cierre al hacer clic en el contenedor
        this.container.addEventListener('click', (e) => {
            e.stopPropagation();
        });

        // Manejar tecla Escape
        this.keydownHandler = (e) => {
            if (e.key === 'Escape' && this.isOpen) {
                this.close(false);
            }
        };
        document.addEventListener('keydown', this.keydownHandler);
    }

    // Mostrar modal de alerta
    alert(title, message, type = 'info') {
        return new Promise((resolve) => {
            this.currentResolve = resolve;
            this.createModal();

            const icon = this.overlay.querySelector('.modal-icon');
            const titleEl = this.overlay.querySelector('.modal-title');
            const messageEl = this.overlay.querySelector('.modal-message');
            const buttonsEl = this.overlay.querySelector('.modal-buttons');

            // Configurar icono según el tipo
            const icons = {
                success: '✅',
                error: '❌',
                warning: '⚠️',
                info: 'ℹ️'
            };

            icon.textContent = icons[type] || icons.info;
            icon.className = `modal-icon ${type}`;
            titleEl.textContent = title;
            messageEl.textContent = message;

            // Botón OK
            const okButton = document.createElement('button');
            okButton.className = 'modal-btn modal-btn-primary';
            okButton.textContent = 'Entendido';
            okButton.addEventListener('click', (e) => {
                e.preventDefault();
                this.disableButton(okButton);
                this.close(true);
            });
            
            buttonsEl.innerHTML = '';
            buttonsEl.appendChild(okButton);

            this.show();
        });
    }

    // Deshabilitar botón temporalmente para prevenir doble clic
    disableButton(button) {
        if (button.disabled) return;
        button.disabled = true;
        const originalText = button.textContent;
        button.textContent = 'Procesando...';
        setTimeout(() => {
            if (button) {
                button.disabled = false;
                button.textContent = originalText;
            }
        }, 1000);
    }

    // Mostrar modal de confirmación
    confirm(title, message, options = {}) {
        return new Promise((resolve) => {
            this.currentResolve = resolve;
            this.createModal();

            const icon = this.overlay.querySelector('.modal-icon');
            const titleEl = this.overlay.querySelector('.modal-title');
            const messageEl = this.overlay.querySelector('.modal-message');
            const buttonsEl = this.overlay.querySelector('.modal-buttons');

            // Configurar contenido
            icon.textContent = '❓';
            icon.className = 'modal-icon question';
            titleEl.textContent = title;
            messageEl.textContent = message;

            // Configurar botones
            const confirmText = options.confirmText || 'Confirmar';
            const cancelText = options.cancelText || 'Cancelar';
            const confirmClass = options.dangerous ? 'modal-btn-danger' : 'modal-btn-primary';

            // Crear botones con event listeners
            const cancelButton = document.createElement('button');
            cancelButton.className = 'modal-btn modal-btn-secondary';
            cancelButton.textContent = cancelText;
            cancelButton.addEventListener('click', (e) => {
                e.preventDefault();
                this.disableButton(cancelButton);
                this.close(false);
            });

            const confirmButton = document.createElement('button');
            confirmButton.className = `modal-btn ${confirmClass}`;
            confirmButton.textContent = confirmText;
            confirmButton.addEventListener('click', (e) => {
                e.preventDefault();
                this.disableButton(confirmButton);
                this.close(true);
            });

            buttonsEl.innerHTML = '';
            buttonsEl.appendChild(cancelButton);
            buttonsEl.appendChild(confirmButton);

            this.show();
        });
    }

    // Mostrar modal de entrada de texto
    prompt(title, message, defaultValue = '') {
        return new Promise((resolve) => {
            this.currentResolve = resolve;
            this.createModal();

            const icon = this.overlay.querySelector('.modal-icon');
            const titleEl = this.overlay.querySelector('.modal-title');
            const messageEl = this.overlay.querySelector('.modal-message');
            const buttonsEl = this.overlay.querySelector('.modal-buttons');

            icon.textContent = '✏️';
            icon.className = 'modal-icon question';
            titleEl.textContent = title;

            // Agregar input al mensaje
            messageEl.innerHTML = `
                <p style="margin-bottom: 1rem;">${message}</p>
                <input type="text" id="modal-input" value="${defaultValue}" 
                       style="width: 100%; padding: 0.75rem; border: 1px solid rgba(255,255,255,0.3); 
                              border-radius: 10px; background: rgba(255,255,255,0.1); 
                              color: white; font-size: 1rem; outline: none;
                              backdrop-filter: blur(10px);">
            `;

            // Crear botones con event listeners
            const cancelButton = document.createElement('button');
            cancelButton.className = 'modal-btn modal-btn-secondary';
            cancelButton.textContent = 'Cancelar';
            cancelButton.addEventListener('click', (e) => {
                e.preventDefault();
                this.disableButton(cancelButton);
                this.close(null);
            });

            const acceptButton = document.createElement('button');
            acceptButton.className = 'modal-btn modal-btn-primary';
            acceptButton.textContent = 'Aceptar';
            acceptButton.addEventListener('click', (e) => {
                e.preventDefault();
                this.disableButton(acceptButton);
                this.submitPrompt();
            });

            buttonsEl.innerHTML = '';
            buttonsEl.appendChild(cancelButton);
            buttonsEl.appendChild(acceptButton);

            this.show();

            // Enfocar el input
            setTimeout(() => {
                const input = document.getElementById('modal-input');
                if (input) {
                    input.focus();
                    input.select();
                    // También permitir enviar con Enter
                    input.addEventListener('keydown', (e) => {
                        if (e.key === 'Enter') {
                            this.submitPrompt();
                        }
                    });
                }
            }, 100);
        });
    }

    // Enviar resultado del prompt
    submitPrompt() {
        const input = document.getElementById('modal-input');
        const value = input ? input.value : '';
        this.close(value);
    }

    // Mostrar el modal
    show() {
        this.isOpen = true;
        document.body.style.overflow = 'hidden';
        
        // Animación de entrada
        setTimeout(() => {
            this.overlay.classList.add('show');
        }, 10);

        // Efecto de pulso
        setTimeout(() => {
            this.container.classList.add('pulse');
            setTimeout(() => {
                this.container.classList.remove('pulse');
            }, 600);
        }, 300);
    }

    // Cerrar el modal
    close(result) {
        if (!this.isOpen || !this.overlay) return;
        
        this.isOpen = false;
        document.body.style.overflow = '';
        
        // Eliminar event listener de teclado
        if (this.keydownHandler) {
            document.removeEventListener('keydown', this.keydownHandler);
            this.keydownHandler = null;
        }
        
        this.overlay.classList.remove('show');
        
        setTimeout(() => {
            if (this.overlay && this.overlay.parentNode) {
                this.overlay.remove();
                this.overlay = null;
                this.container = null;
            }
            
            // Resolver promesa
            if (this.currentResolve) {
                const resolve = this.currentResolve;
                this.currentResolve = null;
                try {
                    resolve(result);
                } catch (error) {
                    console.error('Error al resolver modal:', error);
                }
            }
        }, 300);
    }
}

// Crear instancia global
const modal = new CustomModal();

// Funciones globales para compatibilidad
window.showAlert = (title, message, type = 'info') => modal.alert(title, message, type);
window.showConfirm = (title, message, options = {}) => modal.confirm(title, message, options);
window.showPrompt = (title, message, defaultValue = '') => modal.prompt(title, message, defaultValue);

// Reemplazar funciones nativas con versiones mejoradas
window.customAlert = window.showAlert;
window.customConfirm = window.showConfirm;
window.customPrompt = window.showPrompt;

console.log('✨ Sistema de modales personalizados cargado');
