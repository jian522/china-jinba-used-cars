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

  /* 2. 库存筛选（v8：搜索 + 车身/燃料/价格/品牌/港口 五维，结果数 + 空状态） */
  function setupFilter() {
    var grid = document.querySelector('.grid');
    var q = document.getElementById('q');
    var brand = document.getElementById('brand');
    var fuel = document.getElementById('fuel');
    var year = document.getElementById('year');
    var body = document.getElementById('body');
    var price = document.getElementById('price');
    var port = document.getElementById('port');
    if (!grid) return;
    function filterCars() {
      var qv = (q ? q.value : '').trim().toLowerCase();
      var bv = brand ? brand.value : '';
      var fv = fuel ? fuel.value : '';
      var yv = year ? year.value : '';
      var bodyv = body ? body.value : '';
      var portv = port ? port.value : '';
      var pv = price ? price.value : '';
      var pmin = 0, pmax = Infinity;
      if (pv) { var seg = pv.split('-'); pmin = +seg[0] || 0; pmax = +seg[1] || Infinity; }
      var n = 0;
      grid.querySelectorAll('[data-car]').forEach(function (c) {
        var s = (c.getAttribute('data-search') || '').toLowerCase();
        var pr = +c.getAttribute('data-price') || 0;
        var ok = (!qv || s.indexOf(qv) > -1) &&
                 (!bv || c.getAttribute('data-brand') === bv) &&
                 (!fv || c.getAttribute('data-fuel') === fv) &&
                 (!yv || c.getAttribute('data-year') === yv) &&
                 (!bodyv || c.getAttribute('data-body') === bodyv) &&
                 (!portv || c.getAttribute('data-port') === portv) &&
                 (pr >= pmin && pr <= pmax);
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
    [brand, fuel, year, body, price, port].forEach(function (el) { if (el) el.addEventListener('change', filterCars); });
  }

  /* 3. 详情页画廊（v8 规范）：缩略图点击直接替换主图，禁止任何弹窗预览器 */
  function setupGallery() {
    var main = document.getElementById('mainphoto');
    if (!main) return;
    window.setMain = function (src, btn) {
      if (!src) return;
      main.src = src;
      main.removeAttribute('srcset');
      document.querySelectorAll('.thumb').forEach(function (t) { t.classList.remove('active'); });
      if (btn) btn.classList.add('active');
    };
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
