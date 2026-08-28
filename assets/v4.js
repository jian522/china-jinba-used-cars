/**
 * Jinba Auto Export - Modern JS v6.0
 * Enhanced gallery and UX
 */

function toggleNav(btn) {
  const nav = document.getElementById('navlinks');
  if (!nav) return;
  const isOpen = nav.classList.toggle('open');
  btn?.setAttribute('aria-expanded', isOpen);
}

document.addEventListener('click', (e) => {
  const nav = document.querySelector('.navlinks');
  const hamb = document.querySelector('.hamb');
  if (nav && e.target.closest('.navlinks a')) {
    nav.classList.remove('open');
    hamb?.setAttribute('aria-expanded', 'false');
  }
});

// Photo gallery with lightbox
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

// Lightbox functionality
function openLightbox(src, title) {
  let lb = document.getElementById('lightbox');
  if (!lb) {
    lb = document.createElement('div');
    lb.id = 'lightbox';
    lb.innerHTML = '<div class="lb-content"><button class="lb-close" onclick="closeLightbox()">&times;</button><button class="lb-prev" onclick="prevPhoto()">&#10094;</button><button class="lb-next" onclick="nextPhoto()">&#10095;</button><img src="" alt=""><p class="lb-caption"></p></div>';
    document.body.appendChild(lb);
  }
  lb.style.display = 'flex';
  const img = lb.querySelector('img');
  const caption = lb.querySelector('.lb-caption');
  img.src = src;
  caption.textContent = title || '';
  window.currentPhotoIndex = getCurrentIndex(src);
  window.currentPhotos = getAllPhotos();
}

function closeLightbox() {
  const lb = document.getElementById('lightbox');
  if (lb) lb.style.display = 'none';
}

function prevPhoto() {
  const idx = window.currentPhotoIndex;
  if (idx > 0) {
    const newSrc = window.currentPhotos[idx - 1].src;
    const newAlt = window.currentPhotos[idx - 1].alt;
    document.getElementById('mainphoto').src = newSrc;
    document.querySelectorAll('.thumb').forEach((t, i) => t.classList.toggle('active', i === idx - 1));
    openLightbox(newSrc, newAlt);
  }
}

function nextPhoto() {
  const idx = window.currentPhotoIndex;
  if (idx < window.currentPhotos.length - 1) {
    const newSrc = window.currentPhotos[idx + 1].src;
    const newAlt = window.currentPhotos[idx + 1].alt;
    document.getElementById('mainphoto').src = newSrc;
    document.querySelectorAll('.thumb').forEach((t, i) => t.classList.toggle('active', i === idx + 1));
    openLightbox(newSrc, newAlt);
  }
}

function getCurrentIndex(src) {
  return window.currentPhotos?.findIndex(p => p.src === src) ?? 0;
}

function getAllPhotos() {
  const photos = [];
  document.querySelectorAll('.thumb img').forEach(img => {
    photos.push({ src: img.src, alt: img.alt });
  });
  const main = document.getElementById('mainphoto');
  if (main && photos.length > 0 && main.src !== photos[0]?.src) {
    photos.unshift({ src: main.src, alt: main.alt });
  }
  return photos;
}

// Close lightbox on escape
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') closeLightbox();
  if (e.key === 'ArrowLeft') prevPhoto();
  if (e.key === 'ArrowRight') nextPhoto();
});

// Click outside to close lightbox
document.getElementById('lightbox')?.addEventListener('click', (e) => {
  if (e.target.id === 'lightbox') closeLightbox();
});

// Click main photo to open lightbox
document.getElementById('mainphoto')?.addEventListener('click', function() {
  const thumbs = document.querySelectorAll('.thumb img');
  const activeThumb = document.querySelector('.thumb.active img');
  if (activeThumb) {
    openLightbox(activeThumb.src, activeThumb.alt);
  }
});

// Filter functionality
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

// Smooth scroll
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
  anchor.addEventListener('click', function (e) {
    e.preventDefault();
    const target = document.querySelector(this.getAttribute('href'));
    if (target) target.scrollIntoView({ behavior: 'smooth', block: 'start' });
  });
});

// Intersection Observer for animations
const observerOptions = { threshold: 0.1, rootMargin: '0px 0px -30px 0px' };
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
  el.style.transform = 'translateY(20px)';
  el.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
  observer.observe(el);
});

// Header scroll effect
let lastScroll = 0;
window.addEventListener('scroll', () => {
  const header = document.querySelector('.header');
  if (header) {
    header.classList.toggle('scrolled', window.pageYOffset > 50);
  }
  lastScroll = window.pageYOffset;
});

// WhatsApp tracking
document.querySelectorAll('[data-track="whatsapp"]').forEach(btn => {
  btn.addEventListener('click', function() {
    const market = this.dataset.market;
    if (typeof gtag !== 'undefined') {
      gtag('event', 'click', { event_category: 'WhatsApp', event_label: market || 'Homepage' });
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
    if (!valid) e.preventDefault();
  });
});

console.log('Jinba Auto Export - Premium UI v6.0 loaded');
