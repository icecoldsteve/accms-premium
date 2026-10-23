/* Zet het bewaarde thema vóór de eerste paint, zodat er geen flits van het verkeerde thema is. */
(function () {
  try {
    var t = localStorage.getItem('accms-theme');
    if (t === 'light' || t === 'dark') document.documentElement.setAttribute('data-theme', t);
  } catch (e) { /* opslag geblokkeerd: systeemvoorkeur geldt */ }
})();
