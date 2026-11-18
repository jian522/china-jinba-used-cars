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
      var stockId = link.getAttribute('data-stock') || '';
      var payload = {
        page_path: location.pathname,
        language: lang,
        stock_id: stockId,
        topic: link.getAttribute('data-topic') || '',
        placement: link.getAttribute('data-placement') || 'page_link',
        transport_type: 'beacon'
      };
      if (typeof window.gtag === 'function') {
        window.gtag('event', 'whatsapp_click', payload);
        // 统一询盘事件（GA4 关键事件）：whatsapp 渠道入口。
        window.gtag('event', 'inquiry', Object.assign({ inquiry_type: 'whatsapp' }, payload));
      }
    });
    // Telegram 频道点击追踪占位：事件名/频道地址来自 data-track / href，
    // 后续接 GA4 只需在 gtag 里登记同名事件，无需改页面。
    document.addEventListener('click', function (event) {
      var link = event.target.closest('a[data-track]');
      if (!link || !link.href.startsWith('https://t.me/')) return;
      if (typeof window.gtag === 'function') {
        window.gtag('event', link.getAttribute('data-track') || 'telegram_click', {
          page_path: location.pathname,
          language: link.getAttribute('data-lang') || lang,
          placement: link.getAttribute('data-placement') || 'page_link',
          destination: 'telegram',
          transport_type: 'beacon'
        });
      }
    });
    // 邮箱链接点击追踪 + 统一 inquiry 事件（覆盖 wa/telegram/mailto 三类询盘入口）。
    // inquiry 事件是 GA4 关键事件（转化）的载体：在 GA4 后台把它登记为 key event，
    // 就能在「获取 / 转化」里看到真实询盘量，而不只是零散的渠道点击。
    document.addEventListener('click', function (event) {
      var link = event.target.closest('a[href]');
      if (!link) return;
      var href = link.href || '';
      var isMail = href.startsWith('mailto:');
      if (!isMail) return;
      var channel = 'email';
      var payload = {
        inquiry_type: channel,
        page_path: location.pathname,
        language: lang,
        stock_id: link.getAttribute('data-stock') || '',
        placement: link.getAttribute('data-placement') || 'page_link',
        transport_type: 'beacon'
      };
      if (typeof window.gtag === 'function') {
        window.gtag('event', 'email_click', payload);
        // 统一询盘事件：GA4 关键事件追踪的入口。
        window.gtag('event', 'inquiry', payload);
      }
    });
  }
  var style = document.createElement('style');
  style.textContent = '.seo-whatsapp{position:fixed;right:16px;bottom:calc(16px + env(safe-area-inset-bottom));z-index:30;background:#146c37;color:white;padding:12px 16px;border-radius:28px;box-shadow:0 4px 18px #0003;font:600 14px/1.4 system-ui;text-decoration:none;max-width:calc(100vw - 32px)}.seo-whatsapp:focus-visible{outline:3px solid #ff6b2c;outline-offset:3px}[dir=rtl] .seo-whatsapp{right:auto;left:16px}.seo-linklist{columns:2;column-gap:24px}.seo-linklist li{break-inside:avoid;margin-bottom:8px}@media(max-width:480px){.seo-linklist{columns:1}}';
  document.head.appendChild(style);
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', initialize);
  else initialize();
})();
