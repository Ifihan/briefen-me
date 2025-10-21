// Global JavaScript functions

// Set current year in footer
document.addEventListener('DOMContentLoaded', () => {
    const yearElement = document.getElementById('current-year');
    if (yearElement) {
        yearElement.textContent = new Date().getFullYear();
    }

    // Fetch GitHub stars
    const starCountHeaderElement = document.getElementById('star-count-header');
    if (starCountHeaderElement) {
        fetch('https://api.github.com/repos/Ifihan/briefen-me')
            .then(response => response.json())
            .then(data => {
                const stars = data.stargazers_count || 0;
                starCountHeaderElement.textContent = stars;
            })
            .catch(() => {
                starCountHeaderElement.textContent = '0';
            });
    }

    // Password toggle functionality
    const passwordToggles = document.querySelectorAll('.password-toggle');
    passwordToggles.forEach(toggle => {
        toggle.addEventListener('click', function() {
            const wrapper = this.closest('.password-input-wrapper');
            const input = wrapper.querySelector('input');

            if (input.type === 'password') {
                input.type = 'text';
                this.classList.add('showing');
            } else {
                input.type = 'password';
                this.classList.remove('showing');
            }
        });
    });

    // Auto-hide flash messages after 5 seconds
    const flashMessages = document.querySelectorAll('.flash');
    flashMessages.forEach(flash => {
        setTimeout(() => {
            flash.style.transition = 'opacity 0.5s';
            flash.style.opacity = '0';
            setTimeout(() => flash.remove(), 500);
        }, 5000);
    });
});