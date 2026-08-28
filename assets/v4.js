/**
 * Jinba Auto Export - Modern JS v5.0
 * Enhanced animations and UX
 */

function toggleNav(btn) {
  const nav = document.getElementById('navlinks');
  if (!nav) return;
  const isOpen = nav.classList.toggle('open');
  btn?.setAttribute('aria-expanded', isOpen);
}

// Close mobile nav when clicking a link
document.addEventListener('click', (e) => {
  const nav = document.querySelector('.navlinks');
  const hamb = document.querySelector('.hamb');
  if (nav && e.target.closest('.navlinks a')) {
    nav.classList.remove('open');
    hamb?.setAttribute('aria-expanded', 'false');
  }
});

// Photo gallery for detail pages
function setMain(src, btn) {
  const main = document.getElementById('mainphoto');
  if (main) {
    main.src = src;
    const alt = main.closest('.detail')?.querySelector('h1')?.textContent || 'Vehicle photo';
    main.alt = alt + ' - Photo';
  }
  document.querySelectorAll('.thumb').forEach(t => t.classList.remove('active'));
  if (btn) btn.classList.add('active');
}

// Filter functionality for inventory
function filterCars() {
  const query = document.getElementById('q')?.value.toLowerCase() || '';
  const brand = document.getElementById('brand')?.value || '';
  const fuel = document.getElementById('fuel')?.value || '';
  const year = document.getElementById('year')?.value || '';
  
  const cards = document.querySelectorAll('[data-car]');
  let visible = 0;
  
  cards.forEach(card => {
    const search = card.dataset.search || '';
    const cardBrand = card.dataset.brand || '';
    const cardFuel = card.dataset.fuel || '';
    const cardYear = card.dataset.year || '';
    
    const matchQuery = !query || search.includes(query);
    const matchBrand = !brand || cardBrand === brand;
    const matchFuel = !fuel || cardFuel === fuel;
    const matchYear = !year || cardYear === year;
    
    const show = matchQuery && matchBrand && matchFuel && matchYear;
    card.style.display = show ? '' : 'none';
    if (show) visible++;
  });
  
  const count = document.getElementById('resultCount');
  if (count) count.textContent = visible;
}

// Smooth scroll for anchor links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
  anchor.addEventListener('click', function (e) {
    e.preventDefault();
    const target = document.querySelector(this.getAttribute('href'));
    if (target) {
      target.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  });
});

// Intersection Observer for animations
const observerOptions = {
  threshold: 0.1,
  rootMargin: '0px 0px -50px 0px'
};

const observer = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      entry.target.style.opacity = '1';
      entry.target.style.transform = 'translateY(0)';
      observer.unobserve(entry.target);
    }
  });
}, observerOptions);

document.querySelectorAll('.card, .step, .linkcard').forEach(el => {
  el.style.opacity = '0';
  el.style.transform = 'translateY(30px)';
  el.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
  observer.observe(el);
});

// Add active class to header on scroll
let lastScroll = 0;
window.addEventListener('scroll', () => {
  const header = document.querySelector('.header');
  const currentScroll = window.pageYOffset;
  
  if (header) {
    if (currentScroll > 100) {
      header.classList.add('scrolled');
    } else {
      header.classList.remove('scrolled');
    }
  }
  
  lastScroll = currentScroll;
});

// WhatsApp tracking
document.querySelectorAll('[data-track="whatsapp"]').forEach(btn => {
  btn.addEventListener('click', function() {
    const market = this.dataset.market;
    if (typeof gtag !== 'undefined') {
      gtag('event', 'click', {
        'event_category': 'WhatsApp',
        'event_label': market || 'Homepage'
      });
    }
  });
});

// Form validation
document.querySelectorAll('.inquiry form').forEach(form => {
  form.addEventListener('submit', function(e) {
    const required = form.querySelectorAll('[required]');
    let valid = true;
    
    required.forEach(field => {
      if (!field.value.trim()) {
        field.style.borderColor = '#ef4444';
        valid = false;
      } else {
        field.style.borderColor = '';
      }
    });
    
    if (!valid) {
      e.preventDefault();
    }
  });
});

console.log('Jinba Auto Export - Modern UI v5.0 loaded');
