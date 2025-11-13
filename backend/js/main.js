// Main Application JavaScript

// DOM Ready
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

// Initialize App
function initializeApp() {
    initializeAnimations();
    initializeMenuHandlers();
    initializeNeuralToggle();
    initializeGlassCardEffects();
    initializeAchievements();
    initializeResponsive();
}

// Animations on Load
function initializeAnimations() {
    // Animate XP progress bar
    setTimeout(() => {
        const xpProgress = document.getElementById('xpProgress');
        const percentage = (3247 / 5000) * 100;
        xpProgress.style.width = percentage + '%';
    }, 300);

    // Animate DNA bars
    setTimeout(() => {
        const dnaBars = document.querySelectorAll('.dna-bar-fill');
        dnaBars.forEach(bar => {
            const width = bar.getAttribute('data-width');
            bar.style.width = width + '%';
        });
    }, 500);

    // Animate chart bars
    setTimeout(() => {
        const chartBars = document.querySelectorAll('.chart-bar');
        chartBars.forEach((bar, index) => {
            setTimeout(() => {
                const height = bar.getAttribute('data-height');
                bar.style.height = height + '%';
            }, index * 100);
        });
    }, 700);
}

// Menu Navigation
function initializeMenuHandlers() {
    const menuItems = document.querySelectorAll('.menu-item');
    const bottomNavItems = document.querySelectorAll('.bottom-nav-item');

    menuItems.forEach(item => {
        item.addEventListener('click', function() {
            handleMenuClick(this, menuItems);
        });
    });

    bottomNavItems.forEach(item => {
        item.addEventListener('click', function() {
            handleMenuClick(this, bottomNavItems);
        });
    });
}

function handleMenuClick(element, collection) {
    collection.forEach(item => item.classList.remove('active'));
    element.classList.add('active');

    const page = element.getAttribute('data-page');
    if (page) {
        navigateTo(page);
    }
}

// Navigate to Page
function navigateTo(page) {
    const baseUrl = '../pages/';
    const pages = {
        'dashboard': 'index.html',
        'lessons': 'lessons.html',
        'dictionary': 'dictionary.html',
        'quizzes': 'quizzes.html',
        'progress': 'progress.html',
        'profile': 'profile.html'
    };

    if (pages[page]) {
        window.location.href = baseUrl + pages[page];
    }
}

// Set Active Page
function setActivePage(page) {
    const menuItems = document.querySelectorAll('.menu-item');
    const bottomNavItems = document.querySelectorAll('.bottom-nav-item');

    menuItems.forEach(item => {
        if (item.getAttribute('data-page') === page) {
            item.classList.add('active');
        } else {
            item.classList.remove('active');
        }
    });

    bottomNavItems.forEach((item, index) => {
        const pages = ['dashboard', 'lessons', 'quizzes', 'profile'];
        if (pages[index] === page) {
            item.classList.add('active');
        } else {
            item.classList.remove('active');
        }
    });
}

// Neural Mode Toggle
function initializeNeuralToggle() {
    const neuralToggle = document.getElementById('neuralToggle');
    const toggleSwitch = document.getElementById('toggleSwitch');
    let isNeuralMode = localStorage.getItem('neuralMode') !== 'false';

    if (!isNeuralMode) {
        toggleSwitch.classList.add('off');
    }

    neuralToggle.addEventListener('click', function() {
        isNeuralMode = !isNeuralMode;
        localStorage.setItem('neuralMode', isNeuralMode);

        if (isNeuralMode) {
            toggleSwitch.classList.remove('off');
        } else {
            toggleSwitch.classList.add('off');
        }
    });
}

// Glass Card 3D Effect
function initializeGlassCardEffects() {
    const glassCards = document.querySelectorAll('.glass-card');

    glassCards.forEach(card => {
        card.addEventListener('mousemove', function(e) {
            const rect = card.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;

            const centerX = rect.width / 2;
            const centerY = rect.height / 2;

            const rotateX = (y - centerY) / 30;
            const rotateY = (centerX - x) / 30;

            card.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) scale(1.02)`;
        });

        card.addEventListener('mouseleave', function() {
            card.style.transform = 'perspective(1000px) rotateX(0) rotateY(0) scale(1)';
        });
    });
}

// Achievement Unlock
function initializeAchievements() {
    const achievementItems = document.querySelectorAll('.achievement-item');

    achievementItems.forEach(item => {
        item.addEventListener('click', function() {
            if (!this.classList.contains('unlocked')) {
                this.classList.add('unlocked');
                const icon = this.querySelector('.achievement-icon');
                icon.style.animation = 'bounce 0.6s ease';

                setTimeout(() => {
                    icon.style.animation = '';
                }, 600);
            }
        });
    });
}

// Responsive Handlers
function initializeResponsive() {
    const sidebar = document.getElementById('sidebar');
    let sidebarOpen = false;

    // Create menu toggle button for mobile
    if (window.innerWidth <= 768) {
        createMenuToggle(sidebar);
    }

    window.addEventListener('resize', () => {
        if (window.innerWidth > 768) {
            sidebar.classList.remove('open');
            sidebarOpen = false;
        }
    });
}

function createMenuToggle(sidebar) {
    const toggle = document.createElement('button');
    toggle.className = 'menu-toggle';
    toggle.innerHTML = '<span class="menu-toggle-icon">☰</span>';
    toggle.style.position = 'fixed';
    toggle.style.top = '16px';
    toggle.style.right = '16px';
    toggle.style.zIndex = '999';
    toggle.style.backgroundColor = 'rgba(52, 73, 94, 0.25)';
    toggle.style.border = '1px solid rgba(255, 255, 255, 0.1)';
    toggle.style.borderRadius = '12px';
    toggle.style.padding = '12px';
    toggle.style.cursor = 'pointer';
    toggle.style.color = '#ffffff';
    toggle.style.fontSize = '1.5rem';
    toggle.style.display = 'none';

    if (window.innerWidth <= 768) {
        toggle.style.display = 'block';
    }

    toggle.addEventListener('click', () => {
        sidebar.classList.toggle('open');
    });

    document.body.appendChild(toggle);

    // Close sidebar when clicking outside
    document.addEventListener('click', (e) => {
        if (!sidebar.contains(e.target) && !toggle.contains(e.target)) {
            sidebar.classList.remove('open');
        }
    });
}

// Ripple Effect for Buttons
function createRipple(event) {
    const button = event.currentTarget;
    const ripple = document.createElement('span');
    const rect = button.getBoundingClientRect();
    const size = Math.max(rect.width, rect.height);
    const x = event.clientX - rect.left - size / 2;
    const y = event.clientY - rect.top - size / 2;

    ripple.style.width = ripple.style.height = size + 'px';
    ripple.style.left = x + 'px';
    ripple.style.top = y + 'px';
    ripple.classList.add('ripple');

    button.appendChild(ripple);

    setTimeout(() => {
        ripple.remove();
    }, 600);
}

// Add ripple effect to action buttons
document.addEventListener('click', function(e) {
    if (e.target.closest('.action-button')) {
        createRipple(e);
    }
});

// Utility: Scroll to Top
function scrollToTop() {
    window.scrollTo({
        top: 0,
        behavior: 'smooth'
    });
}

// Utility: Get Random Color
function getRandomGradient() {
    const gradients = [
        'linear-gradient(135deg, var(--purple), var(--pink))',
        'linear-gradient(135deg, var(--blue), var(--cyan))',
        'linear-gradient(135deg, var(--green), var(--cyan))',
        'linear-gradient(135deg, var(--purple), var(--blue))',
        'linear-gradient(135deg, var(--pink), var(--red))'
    ];
    return gradients[Math.floor(Math.random() * gradients.length)];
}

// Performance: Lazy Loading
function setupLazyLoading() {
    const images = document.querySelectorAll('img[data-src]');

    const imageObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                img.src = img.getAttribute('data-src');
                img.removeAttribute('data-src');
                observer.unobserve(img);
            }
        });
    });

    images.forEach(img => imageObserver.observe(img));
}

// Call lazy loading on init
setupLazyLoading();

console.log('Hebrew AI 2025 - Dashboard Loaded Successfully ✨');
