var LANG_MAP = {zh:'中文',en:'English',ru:'Русский',ar:'العربية'};
var currentLang = localStorage.getItem('jinba-lang') || 'zh';

function applyLang(lang) {
  currentLang = lang;
  localStorage.setItem('jinba-lang', lang);
  document.documentElement.lang = lang === 'zh' ? 'zh-CN' : lang;
  document.documentElement.dir = lang === 'ar' ? 'rtl' : 'ltr';
  var els = document.querySelectorAll('[data-lang]');
  for (var i = 0; i < els.length; i++) {
    els[i].style.display = els[i].getAttribute('data-lang') === lang ? '' : 'none';
  }
  var label = document.querySelector('.lang-current');
  if (label) label.textContent = LANG_MAP[lang] || '中文';
  var dd = document.querySelector('.lang-dropdown');
  if (dd) dd.style.display = 'none';
  if (typeof window.onLangChange === 'function') window.onLangChange(lang);
}

function toggleLang() {
  var dd = document.querySelector('.lang-dropdown');
  if (dd) dd.style.display = dd.style.display === 'block' ? 'none' : 'block';
}

window.setLang = applyLang;
window.toggleLang = toggleLang;

document.addEventListener('click', function(e){
  if (!e.target.closest('.lang-switcher')) {
    var dd = document.querySelector('.lang-dropdown');
    if (dd) dd.style.display = 'none';
  }
});

if (currentLang !== 'zh') {
  (function(){ applyLang(currentLang); })();
}
