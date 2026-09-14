/* 5 TINTAS — the small bits of behaviour the pages need.
   No libraries, nothing to install. Every feature here is an extra: with the script switched
   off the links still open the pictures, the menu is still a list, and the site still reads. */

(function () {
  'use strict';

  var STORAGE_KEY = '5tintas.language';
  var SLIDE_GAP = 14;
  var finePointer = window.matchMedia ? window.matchMedia('(pointer: fine)') : null;

  function all(selector, root) {
    return Array.prototype.slice.call((root || document).querySelectorAll(selector));
  }

  function plainClick(event) {
    return !(event.metaKey || event.ctrlKey || event.shiftKey || event.altKey || event.button);
  }

  /* ---- language ---------------------------------------------------------------------- */

  function currentLanguage() {
    return document.documentElement.getAttribute('data-language') === 'es' ? 'es' : 'en';
  }

  function setLanguage(language) {
    var chosen = language === 'es' ? 'es' : 'en';
    document.documentElement.setAttribute('data-language', chosen);
    document.documentElement.setAttribute('lang', chosen);
    try { localStorage.setItem(STORAGE_KEY, chosen); } catch (error) { /* private browsing */ }
  }

  function wireLanguageToggle() {
    all('[data-language-toggle]').forEach(function (button) {
      button.addEventListener('click', function () {
        setLanguage(currentLanguage() === 'en' ? 'es' : 'en');
      });
    });
  }

  /* ---- header ------------------------------------------------------------------------ */

  function wireMenu() {
    var toggle = document.querySelector('[data-menu-toggle]');
    var nav = document.querySelector('[data-nav]');
    if (!toggle || !nav) { return; }
    toggle.addEventListener('click', function () {
      var open = nav.classList.toggle('is-open');
      toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
    });
  }

  function closeDrop(group) {
    group.classList.remove('is-open');
    var toggle = group.querySelector('[data-drop-toggle]');
    if (toggle) { toggle.setAttribute('aria-expanded', 'false'); }
  }

  /* On a desktop the menus open on hover (that is CSS); a finger needs something to tap. */
  function wireDropdowns() {
    all('[data-drop]').forEach(function (group) {
      var toggle = group.querySelector('[data-drop-toggle]');
      if (!toggle) { return; }
      toggle.addEventListener('click', function () {
        var open = !group.classList.contains('is-open');
        all('[data-drop]').forEach(closeDrop);
        group.classList.toggle('is-open', open);
        toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
      });
    });
    document.addEventListener('click', function (event) {
      all('[data-drop].is-open').forEach(function (group) {
        if (!group.contains(event.target)) { closeDrop(group); }
      });
    });
  }

  /* ---- carousels --------------------------------------------------------------------- */

  function wireCarousels() {
    all('[data-carousel]').forEach(function (carousel) {
      var track = carousel.querySelector('[data-carousel-track]');
      var previous = carousel.querySelector('[data-carousel-prev]');
      var next = carousel.querySelector('[data-carousel-next]');
      if (!track || !previous || !next) { return; }

      function step() {
        var slide = track.querySelector('.carousel__slide');
        return slide ? slide.offsetWidth + SLIDE_GAP : Math.round(track.clientWidth * 0.8);
      }

      function update() {
        var room = track.scrollWidth - track.clientWidth;
        carousel.classList.toggle('is-scrollable', room > 4);
        previous.disabled = track.scrollLeft <= 2;
        next.disabled = track.scrollLeft >= room - 2;
      }

      previous.addEventListener('click', function () { track.scrollBy({ left: -step(), behavior: 'smooth' }); });
      next.addEventListener('click', function () { track.scrollBy({ left: step(), behavior: 'smooth' }); });
      track.addEventListener('scroll', update);
      window.addEventListener('resize', update);
      window.addEventListener('load', update);
      update();
    });
  }

  /* ---- the big-picture view ---------------------------------------------------------- */

  function wireLightbox() {
    var dialog = document.querySelector('[data-lightbox-dialog]');
    var image = dialog && dialog.querySelector('[data-lightbox-img]');
    var links = all('[data-lightbox]');
    if (!dialog || !image || !links.length || typeof dialog.showModal !== 'function') { return; }

    var at = 0;
    function show(index) {
      at = (index + links.length) % links.length;
      var thumbnail = links[at].querySelector('img');
      image.src = links[at].getAttribute('href');
      image.alt = thumbnail ? thumbnail.alt : '';
    }

    links.forEach(function (link, index) {
      link.addEventListener('click', function (event) {
        if (!plainClick(event)) { return; }
        event.preventDefault();
        show(index);
        dialog.showModal();
      });
    });

    var previous = dialog.querySelector('[data-lightbox-prev]');
    var next = dialog.querySelector('[data-lightbox-next]');
    var close = dialog.querySelector('[data-lightbox-close]');
    if (previous) { previous.addEventListener('click', function () { show(at - 1); }); }
    if (next) { next.addEventListener('click', function () { show(at + 1); }); }
    if (close) { close.addEventListener('click', function () { dialog.close(); }); }
    dialog.addEventListener('keydown', function (event) {
      if (event.key === 'ArrowLeft') { show(at - 1); }
      if (event.key === 'ArrowRight') { show(at + 1); }
    });
    dialog.addEventListener('click', function (event) {
      if (event.target === dialog) { dialog.close(); }
    });
  }

  /* ---- product page ------------------------------------------------------------------ */

  function wireThumbnails() {
    var main = document.querySelector('[data-product-main]');
    var thumbnails = all('[data-product-thumb]');
    if (!main || !thumbnails.length) { return; }
    thumbnails.forEach(function (thumbnail) {
      thumbnail.addEventListener('click', function (event) {
        if (!plainClick(event)) { return; }
        event.preventDefault();
        main.src = thumbnail.getAttribute('href');
        main.alt = thumbnail.getAttribute('data-alt') || main.alt;
        thumbnails.forEach(function (other) {
          other.setAttribute('aria-current', other === thumbnail ? 'true' : 'false');
        });
      });
    });
  }

  /* A closer look, following the pointer. Only where there is a pointer to follow. */
  function wireZoom() {
    var stage = document.querySelector('[data-zoom]');
    var image = stage && stage.querySelector('img');
    if (!stage || !image || !finePointer || !finePointer.matches) { return; }
    stage.addEventListener('mousemove', function (event) {
      var box = stage.getBoundingClientRect();
      if (!box.width || !box.height) { return; }
      image.style.transformOrigin =
        ((event.clientX - box.left) / box.width * 100).toFixed(1) + '% ' +
        ((event.clientY - box.top) / box.height * 100).toFixed(1) + '%';
    });
    stage.addEventListener('mouseenter', function () { stage.classList.add('is-zoomed'); });
    stage.addEventListener('mouseleave', function () { stage.classList.remove('is-zoomed'); });
  }

  function wireSizes() {
    var sizes = all('[data-size]');
    sizes.forEach(function (size) {
      size.addEventListener('click', function () {
        var chosen = size.getAttribute('aria-pressed') !== 'true';
        sizes.forEach(function (other) { other.setAttribute('aria-pressed', 'false'); });
        size.setAttribute('aria-pressed', chosen ? 'true' : 'false');
      });
    });
  }

  function wireBee() {
    var cta = document.querySelector('[data-cta]');
    if (!cta) { return; }
    cta.addEventListener('click', function () {
      cta.classList.remove('is-flying');
      void cta.offsetWidth;
      cta.classList.add('is-flying');
    });
  }

  /* ---- back to the top --------------------------------------------------------------- */

  function wireFloatingTop() {
    var floating = document.querySelector('[data-floating-top]');
    var sentinel = document.getElementById('top');
    if (!floating || !sentinel || !('IntersectionObserver' in window)) { return; }
    new IntersectionObserver(function (entries) {
      floating.hidden = entries[entries.length - 1].isIntersecting;
    }).observe(sentinel);
  }

  function ready(callback) {
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', callback);
    } else {
      callback();
    }
  }

  ready(function () {
    setLanguage(currentLanguage());
    wireLanguageToggle();
    wireMenu();
    wireDropdowns();
    wireCarousels();
    wireLightbox();
    wireThumbnails();
    wireZoom();
    wireSizes();
    wireBee();
    wireFloatingTop();
  });
})();
