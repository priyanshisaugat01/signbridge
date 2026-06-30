/* shared: scroll reveal + hero ticker + smooth scroll */
(function () {
  // reveal on scroll
  var io = new IntersectionObserver(function (entries) {
    entries.forEach(function (e) { if (e.isIntersecting) e.target.classList.add('in'); });
  }, { threshold: 0.08, rootMargin: '0px 0px -30px 0px' });
  document.querySelectorAll('.r').forEach(function (el) { io.observe(el); });

  // hero prediction ticker (only on home)
  var hChar = document.getElementById('h-char');
  if (hChar) {
    var L = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'.split('');
    var i = 0, word = '';
    var hWord = document.getElementById('h-word');
    var hConf = document.getElementById('h-conf');
    var hBar = document.getElementById('h-bar');
    setInterval(function () {
      i = (i + 1) % L.length;
      word += L[i];
      if (word.length > 5) word = L[i];
      hChar.textContent = L[i];
      hWord.textContent = word.split('').join(' ');
      var c = 86 + Math.floor(Math.random() * 13);
      hConf.textContent = c;
      hBar.style.width = c + '%';
    }, 850);
  }
})();
