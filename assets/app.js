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
    // 必须在 setupFilter 之后：它会包装 window.filterCars 以支持筛选时全量展开
    safe(setupProgressiveGrid);
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
        empty.textContent = (function () {
          var l = (document.documentElement.getAttribute('lang') || 'en').toLowerCase();
          if (l.indexOf('zh') === 0) return '没有符合筛选条件的车辆。';
          if (l.indexOf('ru') === 0) return 'Нет автомобилей, подходящих под фильтры.';
          if (l.indexOf('ar') === 0) return 'لا توجد سيارات مطابقة للفلاتر.';
          return 'No vehicles match your filters.';
        })();
        grid.insertAdjacentElement('afterend', empty);
      } else if (n > 0 && empty) {
        empty.remove();
      }
    }
    window.filterCars = filterCars;
    if (q) q.addEventListener('input', filterCars);
    [brand, fuel, year, body, price, port].forEach(function (el) { if (el) el.addEventListener('change', filterCars); });
  }

  /* 2b. 列表页渐进渲染（2026-10-08）
     问题：/cars/ 一次性渲染 175 台车，HTML 达 177KB，移动端 DCL 约 4s。
     方案：首屏只显示 PAGE_SIZE 台，其余 DOM 节点先藏起来；点「加载更多」逐批显示。
     过滤逻辑不变（仍遍历全部节点算命中数），只是分批呈现 —— 结果数仍是真实总数。 */
  function setupProgressiveGrid() {
    var PAGE_SIZE = 24, PAGE_STEP = 24;   // 就地定义：避免依赖外层作用域
    var grid = document.querySelector('.grid[data-progressive]');
    if (!grid) return;
    var cards = Array.prototype.slice.call(grid.querySelectorAll('[data-car]'));
    if (cards.length <= PAGE_SIZE) return;

    // 四语文案：从 <html lang> 判定，避免英文硬编码出现在俄/阿语页面
    var lang = (document.documentElement.getAttribute('lang') || 'en').toLowerCase();
    // 注意：变量名不要用单字母 T —— 外层作用域已有同名标识符会串味
    var MORE_TXT = {
      en: function (n) { return 'Load more vehicles (' + n + ' remaining)'; },
      zh: function (n) { return '加载更多车辆（还有 ' + n + ' 台）'; },
      ru: function (n) { return 'Показать ещё (' + n + ' осталось)'; },
      ar: function (n) { return 'عرض المزيد (' + n + ' متبقٍ)'; }
    };
    var moreTxt = lang.indexOf('zh') === 0 ? MORE_TXT.zh
                : lang.indexOf('ru') === 0 ? MORE_TXT.ru
                : lang.indexOf('ar') === 0 ? MORE_TXT.ar
                : MORE_TXT.en;

    var TOTAL = cards.length;          // 显式存一份，避免任何作用域歧义
    var shown = PAGE_SIZE;             // 分页游标：已展开到第几张
    var filtering = false;             // 筛选是否正在生效（部分命中）
    var emptyResult = false;           // 筛选后无任何命中
    var hit = [];                      // hit[i] = 该卡是否命中筛选

    // 唯一的渲染入口。三种可见性来源：
    //   无结果  → 全部隐藏（配合 setupFilter 的 .empty-state 提示）
    //   筛选态  → 命中的全部可见（用户明确要看结果，不该藏在按钮后面）
    //   浏览态  → 前 shown 张可见，其余靠「加载更多」
    function paint() {
      cards.forEach(function (c, i) {
        var ok;
        if (emptyResult) ok = false;
        else if (filtering) ok = hit[i];
        else ok = i < shown;
        c.style.display = ok ? '' : 'none';
      });
    }

    // ── 与筛选联动 ────────────────────────────────────────────────
    // ⚠️ 不能只包装 window.filterCars：#q 的 input 事件在 setupFilter 里
    //    绑的是**原始函数引用**，addEventListener 也移不掉，所以 input 时
    //    根本不会经过包装。实测表现为「清空搜索后仍停在全展开态」。
    //    稳妥做法：在同一事件上**后注册**一个监听器（原函数先跑），
    //    读它刚算完的 display 结果作为命中标记，再按当前模式重绘。
    function syncFromFilter() {
      var n = 0;
      for (var i = 0; i < TOTAL; i++) {
        // origFilter 刚跑完：命中的为 ''，未命中的为 'none' —— 据此反推
        hit[i] = cards[i].style.display !== 'none';
        if (hit[i]) n++;
      }
      filtering = n > 0 && n < TOTAL;         // 部分命中才算「筛选中」
      emptyResult = (n === 0);                 // 一个都没命中 → 全隐藏
      if (!filtering) shown = PAGE_SIZE;      // 无结果 / 全命中都回到首屏量
      paint();
      updateMoreBtn((filtering || emptyResult) ? 0 : TOTAL - shown);
    }

    var searchBox2 = document.getElementById('q');
    if (searchBox2) searchBox2.addEventListener('input', syncFromFilter);
    // 下拉筛选走 change，同样后注册一个
    ['brand', 'fuel', 'year', 'body', 'price', 'port'].forEach(function (id) {
      var el = document.getElementById(id);
      if (el) el.addEventListener('change', syncFromFilter);
    });
    // 「筛选」按钮是 onclick="filterCars()" → 走 window.filterCars，包装它
    var origFilter = window.filterCars;
    if (origFilter) {
      window.filterCars = function () { origFilter(); syncFromFilter(); };
    }

    var more = document.createElement('button');
    more.type = 'button';
    more.className = 'loadmore';
    more.textContent = '';
    grid.insertAdjacentElement('afterend', more);

    function updateMoreBtn(rest) {
      if (!(rest > 0)) {              // 同时挡住 NaN 与负数
        more.style.display = 'none';
      } else {
        more.style.display = '';
        more.textContent = moreTxt(rest);
      }
    }

    more.addEventListener('click', function () {
      shown += PAGE_STEP;
      paint();
      updateMoreBtn(TOTAL - shown);
      // 按钮消失后把焦点还给筛选框，避免键盘焦点丢失在隐藏节点上
      if (TOTAL - shown <= 0) {
        var searchBox = document.getElementById('q');
        if (searchBox) searchBox.focus({ preventScroll: true });
      }
    });

    paint();
    updateMoreBtn(TOTAL - shown);
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
