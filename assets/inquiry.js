/* WhatsApp attribution counts link clicks; it does not claim message delivery. */
(function () {
  'use strict';
  function initialize() {
    var lang = (document.documentElement.lang || 'en').split('-')[0];
    var labels = {en:'Ask on WhatsApp',zh:'WhatsApp 询价',ru:'Написать в WhatsApp',ar:'استفسر عبر واتساب'};
    var messages = {
      en:'Hello JINBA CARS, I found {page}. Model: __; quantity: __; budget USD: __; destination country / port: __.',
      zh:'您好金霸汽车，我通过{page}联系。车型：__；数量：__；美元预算：__；目的国/目的港：__。',
      ru:'Здравствуйте JINBA CARS! Я на странице {page}. Модель: __; количество: __; бюджет USD: __; страна / порт: __.',
      ar:'مرحباً JINBA CARS، وصلت من {page}. الطراز: __؛ الكمية: __؛ الميزانية USD: __؛ البلد / الميناء: __.'
    };
    var links = document.querySelectorAll('a[href^="https://wa.me/8618079089999"]');
    links.forEach(function (link) {
      var url = new URL(link.href);
      if (!url.searchParams.has('text')) {
        var title = document.querySelector('h1');
        var page = (title ? title.textContent.trim() : 'your website') + ' (' + location.origin + location.pathname + ')';
        url.searchParams.set('text', (messages[lang] || messages.en).replace('{page}',page));
        link.href = url.href;
      }
    });
    // The detail template already provides a quickbar. Add a small, accessible
    // contact shortcut elsewhere so a mobile reader need not return to the top.
    if (links.length && !document.querySelector('.quickbar')) {
      var shortcut = document.createElement('a');
      shortcut.href = links[0].href;
      shortcut.className = 'seo-whatsapp';
      shortcut.textContent = labels[lang] || labels.en;
      shortcut.setAttribute('data-placement', 'floating_contact');
      document.body.appendChild(shortcut);
    }
    document.addEventListener('click', function (event) {
      var link = event.target.closest('a[href]');
      if (!link || !link.href.startsWith('https://wa.me/8618079089999')) return;
      if (typeof window.gtag === 'function') {
        window.gtag('event', 'whatsapp_click', {
          page_path: location.pathname,
          language: lang,
          stock_id: link.getAttribute('data-stock') || '',
          topic: link.getAttribute('data-topic') || '',
          placement: link.getAttribute('data-placement') || 'page_link',
          transport_type: 'beacon'
        });
      }
    });
  }
  var style = document.createElement('style');
  style.textContent = '.seo-whatsapp{position:fixed;right:16px;bottom:calc(16px + env(safe-area-inset-bottom));z-index:30;background:#146c37;color:white;padding:12px 16px;border-radius:28px;box-shadow:0 4px 18px #0003;font:600 14px/1.4 system-ui;text-decoration:none;max-width:calc(100vw - 32px)}.seo-whatsapp:focus-visible{outline:3px solid #ff6b2c;outline-offset:3px}[dir=rtl] .seo-whatsapp{right:auto;left:16px}.seo-linklist{columns:2;column-gap:24px}.seo-linklist li{break-inside:avoid;margin-bottom:8px}@media(max-width:480px){.seo-linklist{columns:1}}';
  document.head.appendChild(style);
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', initialize);
  else initialize();
})();
