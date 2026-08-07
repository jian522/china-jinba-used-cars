(function(){
  var trust='<section class="jinba-trust" aria-label="Export service assurances"><div class="jinba-trust-inner">'+
    '<div class="jinba-trust-item"><span class="jinba-trust-icon">01</span><span><b>Verified Vehicles</b>Inspection details before purchase</span></div>'+
    '<div class="jinba-trust-item"><span class="jinba-trust-icon">02</span><span><b>Export Documents</b>Complete customs support</span></div>'+
    '<div class="jinba-trust-item"><span class="jinba-trust-icon">03</span><span><b>Global Shipping</b>Port-to-port logistics</span></div>'+
    '<div class="jinba-trust-item"><span class="jinba-trust-icon">04</span><span><b>Direct Support</b>Fast WhatsApp response</span></div></div></section>';
  var hero=document.querySelector('.hero');
  if(hero&&!document.querySelector('.jinba-trust'))hero.insertAdjacentHTML('afterend',trust);
  if(!document.querySelector('.jinba-float'))document.body.insertAdjacentHTML('beforeend','<a class="jinba-float" href="https://wa.me/8618079089999?text=Hello%20Jinba%20Auto%20Export%2C%20I%20would%20like%20a%20vehicle%20quotation." target="_blank" rel="noopener">WhatsApp Quote</a>');
  document.querySelectorAll('img').forEach(function(img){if(!img.loading)img.loading='lazy';});
})();
