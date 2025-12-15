/**
 * Scroll-Based Animations for Modern Hebrew AI 2025 Design
 * Handles parallax effects, scroll reveals, and dynamic animations
 */

class ScrollAnimations {
    constructor() {
        this.elements = document.querySelectorAll('[data-scroll]');
        this.parallaxElements = document.querySelectorAll('[data-parallax]');
        this.observerOptions = {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        };

        this.init();
    }

    init() {
        this.setupIntersectionObserver();
        this.setupParallax();
        this.setupScrollProgress();
    }

    setupIntersectionObserver() {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('reveal-on-scroll');
                    entry.target.style.animationPlayState = 'running';
                    observer.unobserve(entry.target);
                }
            });
        }, this.observerOptions);

        this.elements.forEach(element => {
            observer.observe(element);
        });
    }

    setupParallax() {
        window.addEventListener('scroll', () => {
            this.parallaxElements.forEach(element => {
                const scrollPosition = window.pageYOffset;
                const yPosition = scrollPosition * 0.5;
                element.style.transform = `translateY(${yPosition}px)`;
            });
        }, { passive: true });
    }

    setupScrollProgress() {
        const progressBar = document.querySelector('[data-scroll-progress]');
        if (!progressBar) return;

        window.addEventListener('scroll', () => {
            const windowHeight = document.documentElement.scrollHeight - window.innerHeight;
            const scrolled = (window.pageYOffset / windowHeight) * 100;
            progressBar.style.width = `${scrolled}%`;
        }, { passive: true });
    }
}

/**
 * Lazy Load Images with Fade-In Effect
 */
class LazyLoadImages {
    constructor() {
        this.images = document.querySelectorAll('img[data-lazy]');
        this.init();
    }

    init() {
        if ('IntersectionObserver' in window) {
            const imageObserver = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const img = entry.target;
                        img.src = img.dataset.lazy;
                        img.classList.add('fade-and-lift');
                        img.removeAttribute('data-lazy');
                        imageObserver.unobserve(img);
                    }
                });
            });

            this.images.forEach(img => imageObserver.observe(img));
        } else {
            // Fallback for browsers without IntersectionObserver
            this.images.forEach(img => {
                img.src = img.dataset.lazy;
            });
        }
    }
}

/**
 * Dynamic Gradient Background Animation
 */
class DynamicGradient {
    constructor(elementSelector) {
        this.element = document.querySelector(elementSelector);
        if (this.element) {
            this.init();
        }
    }

    init() {
        const colors = [
            'rgba(255, 107, 53, 0.1)',
            'rgba(0, 212, 212, 0.1)',
            'rgba(126, 255, 0, 0.05)'
        ];

        let colorIndex = 0;

        const updateGradient = () => {
            const nextColorIndex = (colorIndex + 1) % colors.length;
            const angles = [
                `radial-gradient(circle at 20% 50%, ${colors[colorIndex]} 0%, transparent 50%)`,
                `radial-gradient(circle at 80% 80%, ${colors[nextColorIndex]} 0%, transparent 50%)`
            ];

            this.element.style.background = angles.join(',');
            colorIndex = (colorIndex + 1) % colors.length;
        };

        setInterval(updateGradient, 3000);
    }
}

/**
 * Smooth Scroll Navigation
 */
class SmoothScroll {
    constructor() {
        this.links = document.querySelectorAll('a[href^="#"]');
        this.init();
    }

    init() {
        this.links.forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const targetId = link.getAttribute('href');
                const targetElement = document.querySelector(targetId);

                if (targetElement) {
                    targetElement.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            });
        });
    }
}

/**
 * Counter Animation on Scroll
 */
class CounterAnimation {
    constructor(elementSelector = '[data-counter]') {
        this.elements = document.querySelectorAll(elementSelector);
        this.init();
    }

    init() {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting && !entry.target.dataset.counted) {
                    this.animateCounter(entry.target);
                    entry.target.dataset.counted = 'true';
                }
            });
        }, { threshold: 0.5 });

        this.elements.forEach(el => observer.observe(el));
    }

    animateCounter(element) {
        const target = parseInt(element.dataset.counter);
        const duration = 1000; // 1 second
        const step = target / (duration / 16);
        let current = 0;

        const counter = setInterval(() => {
            current += step;
            if (current >= target) {
                element.textContent = target;
                clearInterval(counter);
            } else {
                element.textContent = Math.floor(current);
            }
        }, 16);
    }
}

/**
 * Parallax Background Images
 */
class ParallaxBackground {
    constructor() {
        this.elements = document.querySelectorAll('[data-parallax-bg]');
        this.init();
    }

    init() {
        window.addEventListener('scroll', () => {
            this.elements.forEach(element => {
                const scrollPosition = window.pageYOffset;
                const elementOffset = element.offsetTop;
                const distance = scrollPosition - elementOffset;
                const percentage = distance / window.innerHeight;

                element.style.backgroundPosition = `center ${-percentage * 50}px`;
            });
        }, { passive: true });
    }
}

/**
 * Staggered Animation for Lists
 */
class StaggerAnimation {
    constructor(containerSelector) {
        this.container = document.querySelector(containerSelector);
        if (this.container) {
            this.init();
        }
    }

    init() {
        const items = this.container.querySelectorAll('> *');
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const children = entry.target.querySelectorAll('> *');
                    children.forEach((child, index) => {
                        child.style.animationDelay = `${index * 0.1}s`;
                        child.classList.add('pop-in');
                    });
                    observer.unobserve(entry.target);
                }
            });
        }, { threshold: 0.1 });

        observer.observe(this.container);
    }
}

/**
 * Mouse Follower Effect for Cards
 */
class MouseFollower {
    constructor(cardSelector = '.modern-card') {
        this.cards = document.querySelectorAll(cardSelector);
        this.init();
    }

    init() {
        this.cards.forEach(card => {
            card.addEventListener('mousemove', (e) => {
                const rect = card.getBoundingClientRect();
                const x = e.clientX - rect.left;
                const y = e.clientY - rect.top;

                const centerX = rect.width / 2;
                const centerY = rect.height / 2;

                const rotateX = (y - centerY) * 0.02;
                const rotateY = (centerX - x) * 0.02;

                card.style.transform = `rotateX(${rotateX}deg) rotateY(${rotateY}deg)`;
            });

            card.addEventListener('mouseleave', () => {
                card.style.transform = 'rotateX(0) rotateY(0)';
            });
        });
    }
}

/**
 * Animated Text Effects
 */
class AnimatedText {
    constructor(elementSelector) {
        this.elements = document.querySelectorAll(elementSelector);
        this.init();
    }

    init() {
        this.elements.forEach(element => {
            const text = element.textContent;
            element.textContent = '';

            text.split('').forEach((char, index) => {
                const span = document.createElement('span');
                span.textContent = char;
                span.style.animationDelay = `${index * 0.05}s`;
                span.style.opacity = '0';
                span.style.animation = 'fadeAndLift 0.6s ease-out forwards';
                element.appendChild(span);
            });
        });
    }
}

/**
 * Initialize all animations on DOM ready
 */
document.addEventListener('DOMContentLoaded', () => {
    // Initialize scroll animations
    new ScrollAnimations();

    // Initialize lazy loading
    new LazyLoadImages();

    // Initialize smooth scroll
    new SmoothScroll();

    // Initialize counter animations
    new CounterAnimation();

    // Initialize parallax background
    new ParallaxBackground();

    // Initialize mouse follower for cards
    new MouseFollower();

    // Optional: Initialize dynamic gradient
    // new DynamicGradient('body::before');

    console.log('✨ Modern scroll animations initialized!');
});

/**
 * Utility function to trigger scroll animations on demand
 */
function triggerScrollAnimation(selector) {
    const elements = document.querySelectorAll(selector);
    elements.forEach(el => {
        el.classList.add('reveal-on-scroll');
    });
}

/**
 * Utility function to add glow effect on hover
 */
function addGlowEffect(selector, color = 'var(--orange)') {
    const elements = document.querySelectorAll(selector);
    elements.forEach(el => {
        el.addEventListener('mouseenter', () => {
            el.style.boxShadow = `0 0 20px ${color}, 0 0 40px ${color}`;
        });
        el.addEventListener('mouseleave', () => {
            el.style.boxShadow = '';
        });
    });
}
