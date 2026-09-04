/* =========================================================================
   金霸二手车出口 · 交互脚本 (app.js)
   功能：移动端导航抽屉、库存筛选、详情页缩略图 + Lightbox、入场动画
   所有模块包在 safe() 中，单点失败不影响其余功能。
   ========================================================================= */
(function () {
  'use strict';
  function ready(fn) {
    if (document.readyState !== 'loading') fn();
    else document.addEventListener('DOMContentLoaded', fn);
  }
  function safe(fn) { try { return fn(); } catch (e) { if (window.console) console.error(e); } }

  ready(function () {
    safe(navDrawer);
    safe(setupFilter);
    safe(setupGallery);
    safe(setupReveal);
  });

  /* 1. 移动端导航抽屉 */
  function navDrawer() {
    var nav = document.getElementById('navlinks');
    if (!nav) return;
    window.toggleNav = function (btn) {
      var open = nav.classList.toggle('open');
      if (btn) btn.setAttribute('aria-expanded', open ? 'true' : 'false');
      document.body.style.overflow = open ? 'hidden' : '';
    };
    document.addEventListener('click', function (e) {
      if (!nav.classList.contains('open')) return;
      if (e.target.closest('.hamb') || nav.contains(e.target)) return;
      nav.classList.remove('open');
      document.body.style.overflow = '';
      var h = document.querySelector('.hamb');
      if (h) h.setAttribute('aria-expanded', 'false');
    });
  }

  /* 2. 库存筛选（搜索 + 品牌/燃料/年份下拉，结果数 + 空状态） */
  function setupFilter() {
    var grid = document.querySelector('.grid');
    var q = document.getElementById('q');
    var brand = document.getElementById('brand');
    var fuel = document.getElementById('fuel');
    var year = document.getElementById('year');
    if (!grid) return;
    function filterCars() {
      var qv = (q ? q.value : '').trim().toLowerCase();
      var bv = brand ? brand.value : '';
      var fv = fuel ? fuel.value : '';
      var yv = year ? year.value : '';
      var n = 0;
      grid.querySelectorAll('[data-car]').forEach(function (c) {
        var s = (c.getAttribute('data-search') || '').toLowerCase();
        var ok = (!qv || s.indexOf(qv) > -1) &&
                 (!bv || c.getAttribute('data-brand') === bv) &&
                 (!fv || c.getAttribute('data-fuel') === fv) &&
                 (!yv || c.getAttribute('data-year') === yv);
        c.style.display = ok ? '' : 'none';
        if (ok) n++;
      });
      var rc = document.getElementById('resultCount');
      if (rc) rc.textContent = n;
      var empty = grid.parentNode.querySelector('.empty-state');
      if (n === 0 && !empty) {
        empty = document.createElement('p');
        empty.className = 'empty-state';
        empty.textContent = 'No vehicles match your filters.';
        grid.insertAdjacentElement('afterend', empty);
      } else if (n > 0 && empty) {
        empty.remove();
      }
    }
    window.filterCars = filterCars;
    if (q) q.addEventListener('input', filterCars);
    [brand, fuel, year].forEach(function (el) { if (el) el.addEventListener('change', filterCars); });
  }

  /* 3. 详情页缩略图 + Lightbox（动态创建，无需改模板） */
  function setupGallery() {
    var main = document.getElementById('mainphoto');
    if (!main) return;
    window.setMain = function (src, btn) {
      main.src = src;
      document.querySelectorAll('.thumb').forEach(function (t) { t.classList.remove('active'); });
      if (btn) btn.classList.add('active');
    };
    var lb = document.createElement('div');
    lb.id = 'lightbox';
    lb.setAttribute('role', 'dialog');
    lb.setAttribute('aria-modal', 'true');
    lb.innerHTML = '<button class="lb-close" aria-label="Close">×</button>' +
                   '<button class="lb-prev" aria-label="Previous">‹</button>' +
                   '<img class="lb-img" alt="">' +
                   '<button class="lb-next" aria-label="Next">›</button>' +
                   '<div class="lb-cap"></div>';
    document.body.appendChild(lb);
    var lbImg = lb.querySelector('.lb-img');
    var lbCap = lb.querySelector('.lb-cap');
    var imgs = [], idx = 0;
    function show() { lbImg.src = imgs[idx]; lbCap.textContent = (idx + 1) + ' / ' + imgs.length; }
    function indexOfSrc(src) { var i = imgs.indexOf(src); return i < 0 ? 0 : i; }
    function open(i) {
      imgs = Array.prototype.map.call(document.querySelectorAll('.thumb img'), function (im) { return im.src; });
      if (!imgs.length) return;
      idx = i < 0 ? 0 : (i >= imgs.length ? imgs.length - 1 : i);
      show();
      lb.classList.add('open');
      document.body.style.overflow = 'hidden';
    }
    function close() { lb.classList.remove('open'); document.body.style.overflow = ''; }
    lb.querySelector('.lb-close').addEventListener('click', close);
    lb.querySelector('.lb-prev').addEventListener('click', function () { idx = (idx - 1 + imgs.length) % imgs.length; show(); });
    lb.querySelector('.lb-next').addEventListener('click', function () { idx = (idx + 1) % imgs.length; show(); });
    lb.addEventListener('click', function (e) { if (e.target === lb) close(); });
    document.addEventListener('keydown', function (e) {
      if (!lb.classList.contains('open')) return;
      if (e.key === 'Escape') close();
      else if (e.key === 'ArrowLeft') { idx = (idx - 1 + imgs.length) % imgs.length; show(); }
      else if (e.key === 'ArrowRight') { idx = (idx + 1) % imgs.length; show(); }
    });
    main.style.cursor = 'zoom-in';
    main.addEventListener('click', function () { open(indexOfSrc(main.src)); });
    document.querySelectorAll('.thumb').forEach(function (t) {
      var im = t.querySelector('img');
      t.addEventListener('click', function () { open(indexOfSrc(im ? im.src : '')); });
    });
  }

  /* 4. 入场动画（无障碍：无 IO 时直接显示） */
  function setupReveal() {
    var els = document.querySelectorAll('.reveal');
    if (!els.length) return;
    if (!('IntersectionObserver' in window)) {
      els.forEach(function (el) { el.classList.add('is-in'); });
      return;
    }
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting) { en.target.classList.add('is-in'); io.unobserve(en.target); }
      });
    }, { threshold: 0.12 });
    els.forEach(function (el) { io.observe(el); });
  }
})();
