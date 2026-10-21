/* MD Viewer TY — arayüz mantığı */
(() => {
  'use strict';

  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];
  const body = document.body;
  const root = document.documentElement;
  const docEl = $('#doc');

  const APP = 'MD Viewer TY';
  const WPM = 200;
  const THEMES = ['paper', 'sepia', 'night', 'ink'];
  const DEFAULTS = {
    theme: 'paper', font: 'sitka', size: 20, width: 68, leading: 1.75,
    focus: false, ruler: false, bionic: false, toc: true, autoUpdate: true,
  };

  let api = null;
  let settings = { ...DEFAULTS };
  let current = null;        // açık belge (Python'dan gelen sözlük)
  let headings = [];         // { el, item, level, words }
  let blocks = [];           // odak modu için üst düzey bloklar
  let activeHeading = -1;
  let sessionStart = 0;
  let searchOpen = false;
  let hits = [];
  let hitIndex = -1;

  const fmt = n => n.toLocaleString('tr-TR');
  const clamp = (v, a, b) => Math.min(b, Math.max(a, v));
  const countWords = t => (t.match(/[\p{L}\p{N}]+/gu) || []).length;
  const minutes = words => Math.max(1, Math.round(words / WPM));
  const fold = s => s.replace(/[İIı]/g, 'i').toLowerCase();

  // ---------------------------------------------------------------------------
  // Ayarlar
  // ---------------------------------------------------------------------------
  function applySettings() {
    root.dataset.theme = settings.theme;
    root.dataset.font = settings.font;
    root.style.setProperty('--size', settings.size + 'px');
    root.style.setProperty('--measure', settings.width + 'ch');
    root.style.setProperty('--leading', settings.leading);

    body.classList.toggle('focus', settings.focus);
    body.classList.toggle('ruler', settings.ruler);
    body.classList.toggle('toc-open', settings.toc && hasToc());
    $('#btn-focus').classList.toggle('on', settings.focus);
    $('#btn-toc').classList.toggle('on', settings.toc && hasToc());

    $$('[data-theme-btn]').forEach(b => b.classList.toggle('on', b.dataset.themeBtn === settings.theme));
    $$('[data-font-btn]').forEach(b => b.classList.toggle('on', b.dataset.fontBtn === settings.font));
    $('#size-val').textContent = settings.size;
    $('#width').value = settings.width;
    $('#leading').value = settings.leading;
    $('#opt-focus').checked = settings.focus;
    $('#opt-ruler').checked = settings.ruler;
    $('#opt-bionic').checked = settings.bionic;
    $('#opt-autoupdate').checked = settings.autoUpdate;
  }

  let saveSettingsTimer;
  function set(key, value) {
    if (settings[key] === value) return;
    settings[key] = value;
    applySettings();
    clearTimeout(saveSettingsTimer);
    saveSettingsTimer = setTimeout(() => api && api.save_settings(settings), 400);

    if (key === 'bionic' && current) {
      preserveScroll(renderArticle);
      toast(value ? 'Hızlı okuma açık — kelime başlarına odaklan' : 'Hızlı okuma kapalı');
    }
    if (key === 'focus') {
      clearFocus();
      if (value) toast('Odak modu açık — yalnızca okuduğun paragraf parlak');
    }
    if (key === 'ruler' && value) toast('Okuma cetveli imleci takip ediyor');
    onScroll();
  }

  // ---------------------------------------------------------------------------
  // Belge gösterimi
  // ---------------------------------------------------------------------------
  function hasToc() { return !!current && current.toc.length > 1; }

  function show(doc, opts = {}) {
    if (!doc) return;
    if (doc.error) { toast(doc.error); return; }

    const sameDoc = current && current.path === doc.path;
    const keepScroll = opts.keepScroll && sameDoc;
    const prevY = scrollY;
    if (!keepScroll) flushPosition();

    current = doc;
    body.classList.remove('is-empty');
    $('#endcard').classList.remove('reached');
    renderArticle();
    buildToc();
    applySettings();

    $('#doc-name').textContent = doc.title;
    document.title = `${doc.title} — ${APP}`;

    if (keepScroll) {
      scrollTo(0, prevY);
      if (searchOpen && $('#search-input').value) runSearch($('#search-input').value, false);
    } else {
      sessionStart = Date.now();
      docEl.classList.remove('enter');
      void docEl.offsetWidth;
      docEl.classList.add('enter');
      scrollTo(0, 0);
      const pos = doc.position || 0;
      if (pos > 0.02 && pos < 0.985) {
        whenImagesReady().then(() => {
          scrollTo(0, pos * scrollRange());
          toast(`Kaldığın yerden devam ediyorsun · %${Math.round(pos * 100)}`, 'Başa dön',
            () => scrollTo({ top: 0, behavior: 'smooth' }));
        });
      }
    }
    onScroll();
  }

  function renderArticle() {
    docEl.innerHTML = current.html;
    enhance();
    if (settings.bionic && !searchOpen) bionicify(docEl);
    blocks = [...docEl.children].filter(el => !el.classList.contains('doc-meta'));
    computeSections();
  }

  function preserveScroll(fn) {
    const y = scrollY;
    fn();
    scrollTo(0, y);
  }

  function enhance() {
    // Başlık altına okuma bilgisi
    const meta = document.createElement('div');
    meta.className = 'doc-meta';
    const first = docEl.firstElementChild;
    const startsWithH1 = first && first.tagName === 'H1';
    const sections = current.toc.filter(t => t.level === 2).length;
    const updated = new Date(current.mtime * 1000).toLocaleString('tr-TR', {
      day: 'numeric', month: 'long', hour: '2-digit', minute: '2-digit',
    });
    const parts = [];
    if (!startsWithH1) parts.push(`<span class="file-label"></span>`);
    parts.push(`<span>${current.minutes} dk okuma</span>`);
    parts.push(`<span>${fmt(current.words)} kelime</span>`);
    if (sections > 1) parts.push(`<span>${sections} bölüm</span>`);
    parts.push(`<span>${updated}</span>`);
    meta.innerHTML = parts.join('');
    const label = meta.querySelector('.file-label');
    if (label) label.textContent = current.title;
    if (startsWithH1) first.after(meta); else docEl.prepend(meta);

    // Kod blokları: dil etiketi + kopyala
    $$('pre.code', docEl).forEach(pre => {
      const wrap = document.createElement('div');
      wrap.className = 'code-block';
      const head = document.createElement('div');
      head.className = 'code-head';
      const lang = document.createElement('span');
      lang.textContent = pre.dataset.lang || '';
      const btn = document.createElement('button');
      btn.innerHTML = '<svg><use href="#i-copy"/></svg><span>Kopyala</span>';
      btn.addEventListener('click', () => copyText(pre.innerText, btn));
      head.append(lang, btn);
      pre.replaceWith(wrap);
      wrap.append(head, pre);
    });

    // Geniş tablolar yatay kaysın
    $$('table', docEl).forEach(t => {
      const wrap = document.createElement('div');
      wrap.className = 'table-wrap';
      t.replaceWith(wrap);
      wrap.append(t);
    });
  }

  function computeSections() {
    const ids = new Set(current.toc.map(t => t.id));
    headings = [];
    let words = 0;
    let owner = null;
    for (const el of docEl.children) {
      if (/^H[1-4]$/.test(el.tagName) && ids.has(el.id)) {
        if (owner) owner.words = words;
        owner = { el, level: +el.tagName[1], words: 0, item: null };
        headings.push(owner);
        words = 0;
      } else if (!el.classList.contains('doc-meta') && !el.classList.contains('code-block')) {
        words += countWords(el.textContent);
      }
    }
    if (owner) owner.words = words;
  }

  function buildToc() {
    const nav = $('#toc');
    nav.innerHTML = '';
    activeHeading = -1;
    $('#toc-total').textContent = `${current.minutes} dk`;
    if (!hasToc()) return;

    const h1Count = headings.filter(h => h.level === 1).length;
    const topLevel = h1Count > 1 ? 1 : 2;

    headings.forEach((h, i) => {
      const a = document.createElement('a');
      a.className = `toc-item l${h.level}`;
      a.href = '#' + h.el.id;
      const text = document.createElement('span');
      text.className = 't-text';
      text.textContent = h.el.textContent;
      a.append(text);

      if (h.level === topLevel) {
        let w = h.words;
        for (let j = i + 1; j < headings.length && headings[j].level > h.level; j++) w += headings[j].words;
        const m = document.createElement('span');
        m.className = 't-min';
        m.textContent = `${minutes(w)} dk`;
        a.append(m);
      }
      a.addEventListener('click', e => {
        e.preventDefault();
        h.el.scrollIntoView({ behavior: 'smooth', block: 'start' });
        if (innerWidth < 1100) set('toc', false);
      });
      h.item = a;
      nav.append(a);
    });
  }

  // ---------------------------------------------------------------------------
  // Kaydırma: ilerleme, kalan süre, aktif bölüm, odak
  // ---------------------------------------------------------------------------
  const scrollRange = () => Math.max(1, docEl.offsetTop + docEl.offsetHeight - innerHeight * 0.6);
  const progress = () => clamp(scrollY / scrollRange(), 0, 1);

  let lastY = 0;
  let ticking = false;
  addEventListener('scroll', () => {
    if (ticking) return;
    ticking = true;
    requestAnimationFrame(() => { ticking = false; onScroll(); });
  }, { passive: true });
  addEventListener('resize', () => onScroll());

  function onScroll() {
    if (!current) return;
    const y = scrollY;
    const p = progress();

    $('#progress-bar').style.width = (p * 100).toFixed(2) + '%';
    body.classList.toggle('scrolled', y > 8);
    const panelOpen = $('#appearance').classList.contains('open') || searchOpen;
    if (y > lastY + 6 && y > 260 && !panelOpen) body.classList.add('bar-hidden');
    else if (y < lastY - 6 || y < 60) body.classList.remove('bar-hidden');
    lastY = y;

    const remaining = $('#doc-remaining');
    if (p >= 0.995) {
      remaining.textContent = 'Bitti ✓';
      remaining.classList.add('done');
      reachEnd();
    } else {
      const left = Math.round((current.words * (1 - p)) / WPM);
      remaining.textContent = `${left < 1 ? '1 dk’dan az' : left + ' dk'} kaldı · %${Math.round(p * 100)}`;
      remaining.classList.remove('done');
    }

    updateActiveHeading();
    if (settings.focus) updateFocus();
    schedulePosition(p);
  }

  function updateActiveHeading() {
    const line = innerHeight * 0.3;
    let idx = -1;
    for (let i = 0; i < headings.length; i++) {
      if (headings[i].el.getBoundingClientRect().top <= line) idx = i; else break;
    }
    if (idx === activeHeading) return;
    activeHeading = idx;
    headings.forEach((h, i) => {
      if (!h.item) return;
      h.item.classList.toggle('active', i === idx);
      h.item.classList.toggle('done', i < idx);
    });
    // scrollIntoView ana belgeyi de kaydırabildiği için yalnızca kenar paneli kaydır.
    const item = headings[idx] && headings[idx].item;
    const side = $('#sidebar');
    if (item) {
      const top = item.offsetTop - side.clientHeight * 0.35;
      if (item.offsetTop < side.scrollTop || item.offsetTop + item.offsetHeight > side.scrollTop + side.clientHeight) {
        side.scrollTo({ top, behavior: 'smooth' });
      }
    }
  }

  let focused = null;
  function clearFocus() {
    blocks.forEach(b => b.classList.remove('is-current', 'is-near'));
    focused = null;
  }
  function updateFocus() {
    const line = innerHeight * 0.42;
    let best = null;
    let bestDist = Infinity;
    for (const b of blocks) {
      const r = b.getBoundingClientRect();
      if (r.bottom < 0) continue;
      if (r.top > innerHeight) break;
      const d = r.top <= line && r.bottom >= line ? 0 : Math.min(Math.abs(r.top - line), Math.abs(r.bottom - line));
      if (d < bestDist) { bestDist = d; best = b; }
    }
    if (!best || best === focused) return;
    clearFocus();
    focused = best;
    best.classList.add('is-current');
    // Başlık hemen üstündeyse onu da aydınlat; bağlam kaybolmasın.
    const prev = best.previousElementSibling;
    if (prev && /^H\d$/.test(prev.tagName)) prev.classList.add('is-current');
    else if (prev) prev.classList.add('is-near');
    if (best.nextElementSibling) best.nextElementSibling.classList.add('is-near');
  }

  function nextSection(dir) {
    const list = headings.filter(h => h.level <= 3);
    if (!list.length) return;
    const line = innerHeight * 0.3 + 2;
    let target;
    if (dir > 0) target = list.find(h => h.el.getBoundingClientRect().top > line);
    else target = [...list].reverse().find(h => h.el.getBoundingClientRect().top < -2);
    if (target) target.el.scrollIntoView({ behavior: 'smooth', block: 'start' });
    else if (dir < 0) scrollTo({ top: 0, behavior: 'smooth' });
  }

  function reachEnd() {
    const card = $('#endcard');
    const spent = Math.round((Date.now() - sessionStart) / 60000);
    $('#end-stats').textContent =
      `${fmt(current.words)} kelime · tahmini ${current.minutes} dk · bu oturumda ` +
      (spent < 1 ? 'bir dakikadan az' : `${spent} dk`) + ' okudun';
    card.classList.add('reached');
  }

  // Okuma konumunu hatırla
  let positionTimer;
  let pendingPosition = null;
  function schedulePosition(p) {
    pendingPosition = p;
    current.position = p;
    clearTimeout(positionTimer);
    positionTimer = setTimeout(flushPosition, 700);
  }
  function flushPosition() {
    clearTimeout(positionTimer);
    if (current && pendingPosition !== null && api) api.save_position(current.path, pendingPosition);
    pendingPosition = null;
  }

  function whenImagesReady() {
    const pending = $$('img', docEl).filter(i => !i.complete).map(i => i.decode().catch(() => {}));
    return Promise.race([Promise.all(pending), new Promise(r => setTimeout(r, 900))])
      .then(() => new Promise(r => requestAnimationFrame(r)));
  }

  // ---------------------------------------------------------------------------
  // Hızlı okuma (biyonik)
  // ---------------------------------------------------------------------------
  function bionicify(scope) {
    const walker = document.createTreeWalker(scope, NodeFilter.SHOW_TEXT, {
      acceptNode(n) {
        const p = n.parentElement;
        if (!p || p.closest('pre, code, kbd, h1, h2, h3, h4, h5, h6, .doc-meta, .code-head, .callout-title')) {
          return NodeFilter.FILTER_REJECT;
        }
        return /\p{L}/u.test(n.nodeValue) ? NodeFilter.FILTER_ACCEPT : NodeFilter.FILTER_REJECT;
      },
    });
    const nodes = [];
    while (walker.nextNode()) nodes.push(walker.currentNode);

    for (const node of nodes) {
      const text = node.nodeValue;
      const frag = document.createDocumentFragment();
      let last = 0;
      for (const m of text.matchAll(/\p{L}[\p{L}\p{M}]*/gu)) {
        const w = m[0];
        const k = w.length <= 3 ? 1 : Math.ceil(w.length * 0.45);
        if (m.index > last) frag.append(text.slice(last, m.index));
        const b = document.createElement('b');
        b.className = 'bio';
        b.textContent = w.slice(0, k);
        frag.append(b, w.slice(k));
        last = m.index + w.length;
      }
      if (last < text.length) frag.append(text.slice(last));
      node.replaceWith(frag);
    }
  }

  // ---------------------------------------------------------------------------
  // Arama
  // ---------------------------------------------------------------------------
  const searchInput = $('#search-input');

  function openSearch() {
    if (!current) return;
    if (!searchOpen) {
      searchOpen = true;
      $('#searchbar').classList.add('open');
      body.classList.remove('bar-hidden');
      if (settings.bionic) preserveScroll(renderArticle);
    }
    searchInput.focus();
    searchInput.select();
    if (searchInput.value) runSearch(searchInput.value);
  }

  function closeSearch() {
    if (!searchOpen) return;
    searchOpen = false;
    $('#searchbar').classList.remove('open');
    clearHits();
    if (settings.bionic) preserveScroll(renderArticle);
  }

  function clearHits() {
    const parents = new Set();
    $$('mark.hit', docEl).forEach(m => {
      parents.add(m.parentNode);
      m.replaceWith(m.textContent);
    });
    parents.forEach(p => p.normalize());
    hits = [];
    hitIndex = -1;
    $('#search-count').textContent = '';
  }

  function runSearch(query, jump = true) {
    clearHits();
    const q = fold(query.trim());
    if (q.length < 2) return;

    const walker = document.createTreeWalker(docEl, NodeFilter.SHOW_TEXT, {
      acceptNode: n => n.parentElement.closest('.code-head') ? NodeFilter.FILTER_REJECT : NodeFilter.FILTER_ACCEPT,
    });
    const nodes = [];
    while (walker.nextNode()) nodes.push(walker.currentNode);

    for (const node of nodes) {
      const text = node.nodeValue;
      const hay = fold(text);
      if (hay.length !== text.length) continue;
      let i = hay.indexOf(q);
      if (i < 0) continue;
      const frag = document.createDocumentFragment();
      let last = 0;
      while (i >= 0) {
        if (i > last) frag.append(text.slice(last, i));
        const mark = document.createElement('mark');
        mark.className = 'hit';
        mark.textContent = text.slice(i, i + q.length);
        frag.append(mark);
        hits.push(mark);
        last = i + q.length;
        i = hay.indexOf(q, last);
      }
      if (last < text.length) frag.append(text.slice(last));
      node.replaceWith(frag);
    }

    if (!hits.length) { $('#search-count').textContent = 'Yok'; return; }
    if (jump) gotoHit(0); else updateCount();
  }

  function updateCount() {
    $('#search-count').textContent = hits.length ? `${Math.max(1, hitIndex + 1)}/${hits.length}` : '';
  }

  function gotoHit(i) {
    if (!hits.length) return;
    if (hits[hitIndex]) hits[hitIndex].classList.remove('current');
    hitIndex = (i + hits.length) % hits.length;
    const m = hits[hitIndex];
    m.classList.add('current');
    m.scrollIntoView({ block: 'center', behavior: 'smooth' });
    updateCount();
  }

  let searchTimer;
  searchInput.addEventListener('input', () => {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(() => runSearch(searchInput.value), 160);
  });
  searchInput.addEventListener('keydown', e => {
    if (e.key === 'Enter') { e.preventDefault(); gotoHit(hitIndex + (e.shiftKey ? -1 : 1)); }
    if (e.key === 'Escape') { e.preventDefault(); closeSearch(); }
  });
  $('#search-next').addEventListener('click', () => gotoHit(hitIndex + 1));
  $('#search-prev').addEventListener('click', () => gotoHit(hitIndex - 1));
  $('#search-close').addEventListener('click', closeSearch);

  // ---------------------------------------------------------------------------
  // Başlangıç ekranı
  // ---------------------------------------------------------------------------
  function relTime(ts) {
    const diff = (Date.now() / 1000 - ts) / 86400;
    if (diff < 1 / 24) return 'az önce';
    if (diff < 1) return 'bugün';
    if (diff < 2) return 'dün';
    if (diff < 30) return `${Math.floor(diff)} gün önce`;
    return new Date(ts * 1000).toLocaleDateString('tr-TR', { day: 'numeric', month: 'short' });
  }

  function renderRecent(list) {
    const ul = $('#recent');
    ul.innerHTML = '';
    $('#recent-wrap').classList.toggle('empty', !list.length);
    for (const r of list) {
      const p = r.progress || 0;
      const li = document.createElement('li');
      li.className = 'recent-item';
      li.innerHTML = `
        <span class="r-title"></span>
        <span class="r-meta"></span>
        <span class="r-path"></span>
        <span class="r-bar"><i style="width:${(p * 100).toFixed(1)}%"></i></span>
        <button class="icon sm r-remove" title="Listeden kaldır"><svg><use href="#i-close"/></svg></button>`;
      li.querySelector('.r-title').textContent = r.title;
      li.querySelector('.r-path').textContent = r.path;
      const meta = li.querySelector('.r-meta');
      if (p >= 0.985) meta.innerHTML = `<b>Bitti ✓</b>${relTime(r.opened)}`;
      else if (p > 0.01) {
        const left = Math.max(1, Math.ceil((r.minutes || 1) * (1 - p)));
        meta.innerHTML = `<b>%${Math.round(p * 100)}</b>${left} dk kaldı`;
      } else meta.innerHTML = `<b>${r.minutes || 1} dk</b>${relTime(r.opened)}`;

      li.addEventListener('click', async () => show(await api.load(r.path)));
      li.querySelector('.r-remove').addEventListener('click', async e => {
        e.stopPropagation();
        renderRecent(await api.remove_recent(r.path));
      });
      ul.append(li);
    }
  }

  async function goHome() {
    flushPosition();
    closeSearch();
    current = null;
    headings = [];
    blocks = [];
    docEl.innerHTML = '';
    body.classList.add('is-empty');
    body.classList.remove('bar-hidden', 'scrolled', 'toc-open');
    $('#doc-name').textContent = APP;
    document.title = APP;
    scrollTo(0, 0);
    api.close_document();
    renderRecent(await api.get_recent());
  }

  async function openDialog() {
    const doc = await api.open_dialog();
    if (doc) show(doc);
  }

  // ---------------------------------------------------------------------------
  // Yardımcılar
  // ---------------------------------------------------------------------------
  let toastTimer;
  function toast(message, actionLabel, action) {
    const t = $('#toast');
    t.innerHTML = '';
    const span = document.createElement('span');
    span.textContent = message;
    t.append(span);
    if (actionLabel) {
      const b = document.createElement('button');
      b.textContent = actionLabel;
      b.addEventListener('click', () => { action(); t.classList.remove('show'); });
      t.append(b);
    }
    t.classList.add('show');
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => t.classList.remove('show'), actionLabel ? 6500 : 2600);
  }

  async function copyText(text, btn) {
    try {
      await navigator.clipboard.writeText(text);
    } catch {
      const ta = document.createElement('textarea');
      ta.value = text;
      document.body.append(ta);
      ta.select();
      document.execCommand('copy');
      ta.remove();
    }
    const label = btn.querySelector('span');
    btn.classList.add('copied');
    btn.querySelector('use').setAttribute('href', '#i-check');
    label.textContent = 'Kopyalandı';
    setTimeout(() => {
      btn.classList.remove('copied');
      btn.querySelector('use').setAttribute('href', '#i-copy');
      label.textContent = 'Kopyala';
    }, 1600);
  }

  function openLightbox(src) {
    const lb = $('#lightbox');
    lb.querySelector('img').src = src;
    lb.classList.add('open');
  }

  // ---------------------------------------------------------------------------
  // Olaylar
  // ---------------------------------------------------------------------------
  docEl.addEventListener('click', async e => {
    const img = e.target.closest('img');
    if (img && !img.closest('a')) { openLightbox(img.src); return; }
    const a = e.target.closest('a');
    if (!a) return;
    const href = a.getAttribute('href') || '';
    e.preventDefault();
    if (href.startsWith('#')) {
      const target = document.getElementById(decodeURIComponent(href.slice(1)));
      if (target) target.scrollIntoView({ behavior: 'smooth', block: 'start' });
      return;
    }
    const doc = await api.follow_link(href);
    if (doc) show(doc);
  });

  $('#lightbox').addEventListener('click', () => $('#lightbox').classList.remove('open'));
  $('#btn-open').addEventListener('click', openDialog);
  $('#btn-open-welcome').addEventListener('click', openDialog);
  $('#btn-open-end').addEventListener('click', openDialog);
  $('#btn-home').addEventListener('click', goHome);
  $('#btn-top').addEventListener('click', () => scrollTo({ top: 0, behavior: 'smooth' }));
  $('#btn-toc').addEventListener('click', () => set('toc', !settings.toc));
  $('#btn-focus').addEventListener('click', () => set('focus', !settings.focus));
  $('#btn-search').addEventListener('click', () => (searchOpen ? closeSearch() : openSearch()));
  $('#btn-full').addEventListener('click', () => api.toggle_fullscreen());

  const panel = $('#appearance');
  $('#btn-appearance').addEventListener('click', e => {
    e.stopPropagation();
    panel.classList.toggle('open');
    $('#btn-appearance').classList.toggle('on', panel.classList.contains('open'));
  });
  document.addEventListener('click', e => {
    if (panel.classList.contains('open') && !panel.contains(e.target)) {
      panel.classList.remove('open');
      $('#btn-appearance').classList.remove('on');
    }
  });
  $$('[data-theme-btn]').forEach(b => b.addEventListener('click', () => set('theme', b.dataset.themeBtn)));
  $$('[data-font-btn]').forEach(b => b.addEventListener('click', () => set('font', b.dataset.fontBtn)));
  $('#size-down').addEventListener('click', () => set('size', clamp(settings.size - 1, 14, 32)));
  $('#size-up').addEventListener('click', () => set('size', clamp(settings.size + 1, 14, 32)));
  $('#width').addEventListener('input', e => set('width', +e.target.value));
  $('#leading').addEventListener('input', e => set('leading', +e.target.value));
  $('#opt-focus').addEventListener('change', e => set('focus', e.target.checked));
  $('#opt-ruler').addEventListener('change', e => set('ruler', e.target.checked));
  $('#opt-bionic').addEventListener('change', e => set('bionic', e.target.checked));

  // Okuma cetveli imleci takip eder
  const ruler = $('#ruler');
  addEventListener('mousemove', e => {
    if (!settings.ruler) return;
    ruler.style.transform = `translateY(${e.clientY - ruler.offsetHeight / 2}px)`;
    ruler.classList.add('live');
  });
  document.addEventListener('mouseleave', () => ruler.classList.remove('live'));

  // Sürükle-bırak (yolu Python tarafı yakalar)
  let dragDepth = 0;
  addEventListener('dragenter', e => { e.preventDefault(); dragDepth++; body.classList.add('dragging'); });
  addEventListener('dragover', e => e.preventDefault());
  addEventListener('dragleave', () => { if (--dragDepth <= 0) { dragDepth = 0; body.classList.remove('dragging'); } });
  addEventListener('drop', e => { e.preventDefault(); dragDepth = 0; body.classList.remove('dragging'); });

  addEventListener('keydown', e => {
    const key = e.key.toLowerCase();
    const typing = e.target.matches('input[type="text"]');

    if (e.ctrlKey && key === 'o') { e.preventDefault(); openDialog(); return; }
    if (e.ctrlKey && key === 'f') { e.preventDefault(); openSearch(); return; }
    if (e.ctrlKey && (key === '+' || key === '=')) { e.preventDefault(); set('size', clamp(settings.size + 1, 14, 32)); return; }
    if (e.ctrlKey && key === '-') { e.preventDefault(); set('size', clamp(settings.size - 1, 14, 32)); return; }
    if (e.ctrlKey && key === '0') { e.preventDefault(); set('size', DEFAULTS.size); return; }
    if (e.key === 'F11') { e.preventDefault(); api.toggle_fullscreen(); return; }
    if (e.key === 'Escape') {
      if ($('#lightbox').classList.contains('open')) $('#lightbox').classList.remove('open');
      else if (panel.classList.contains('open')) { panel.classList.remove('open'); $('#btn-appearance').classList.remove('on'); }
      else closeSearch();
      return;
    }
    if (typing || e.ctrlKey || e.altKey || e.metaKey) return;

    switch (key) {
      case 'f': set('focus', !settings.focus); break;
      case 'r': set('ruler', !settings.ruler); break;
      case 'b': set('bionic', !settings.bionic); break;
      case 's': set('toc', !settings.toc); break;
      case 'n': nextSection(1); break;
      case 'p': nextSection(-1); break;
      case 't': {
        const next = THEMES[(THEMES.indexOf(settings.theme) + 1) % THEMES.length];
        set('theme', next);
        toast(`Tema: ${{ paper: 'Kâğıt', sepia: 'Sepya', night: 'Gece', ink: 'Mürekkep' }[next]}`);
        break;
      }
      default: return;
    }
    e.preventDefault();
  });

  addEventListener('beforeunload', flushPosition);
  document.addEventListener('visibilitychange', () => { if (document.hidden) flushPosition(); });

  // Dosya değişince canlı yenile
  let polling = false;
  async function poll() {
    if (!current || polling || document.hidden) return;
    polling = true;
    try {
      const doc = await api.check_changed();
      if (doc && current && doc.path === current.path) {
        show(doc, { keepScroll: true });
        toast('Belge güncellendi');
      }
    } finally {
      polling = false;
    }
  }

  // ---------------------------------------------------------------------------
  // Güncellemeler
  // ---------------------------------------------------------------------------
  const updateCard = $('#update');
  let updateInfo = null;

  async function checkForUpdate(manual) {
    const btn = $('#btn-check-update');
    if (manual) { btn.disabled = true; btn.textContent = 'Denetleniyor…'; }
    try {
      const info = await api.check_update();
      if (info.error) { if (manual) toast(info.error); return; }
      if (info.available) showUpdate(info);
      else if (manual) toast(`En güncel sürümü kullanıyorsun (${info.current})`);
    } finally {
      btn.disabled = false;
      btn.textContent = 'Güncellemeleri denetle';
    }
  }

  function showUpdate(info) {
    updateInfo = info;
    $('#up-versions').textContent = `${info.current} → ${info.latest}`;
    $('#up-notes').textContent = info.notes.replace(/^#+\s*/gm, '').replace(/\*\*/g, '');
    $('#up-install').textContent = appInfo.canSelfUpdate ? 'Şimdi güncelle' : 'İndirme sayfası';
    updateCard.classList.remove('busy');
    updateCard.classList.add('open');
  }

  $('#up-close').addEventListener('click', () => updateCard.classList.remove('open'));
  $('#up-page').addEventListener('click', () => updateInfo && api.open_url(updateInfo.page));
  $('#up-install').addEventListener('click', () => {
    if (!appInfo.canSelfUpdate) { api.open_url(updateInfo.page); return; }
    flushPosition();
    updateCard.classList.add('busy');
    $('#up-bar').style.width = '0%';
    $('#up-install').textContent = 'İndiriliyor…';
    api.install_update();
  });
  $('#btn-check-update').addEventListener('click', () => checkForUpdate(true));
  $('#opt-autoupdate').addEventListener('change', e => set('autoUpdate', e.target.checked));

  function updateProgress(p) {
    $('#up-bar').style.width = (p * 100).toFixed(1) + '%';
    $('#up-install').textContent = p >= 1 ? 'Kuruluyor…' : `İndiriliyor… %${Math.round(p * 100)}`;
  }

  function updateFailed(message) {
    updateCard.classList.remove('busy');
    $('#up-install').textContent = 'Tekrar dene';
    toast(message, 'Sürüm sayfası', () => api.open_url(updateInfo.page));
  }

  // ---------------------------------------------------------------------------
  let appInfo = { canSelfUpdate: false };

  async function init() {
    api = window.pywebview.api;
    const [state, info] = await Promise.all([api.get_state(), api.get_info()]);
    appInfo = info;
    $('#app-version').textContent = `Sürüm ${info.version}`;
    settings = { ...DEFAULTS, ...(state.settings || {}) };
    applySettings();
    renderRecent(state.recent || []);
    if (state.initial) show(state.initial);
    setInterval(poll, 1000);
    requestAnimationFrame(() => requestAnimationFrame(() => root.classList.remove('preload')));
    if (settings.autoUpdate && info.canSelfUpdate) setTimeout(() => checkForUpdate(false), 2500);
  }

  window.MDV = { show, updateProgress, updateFailed };
  applySettings();
  if (window.pywebview && window.pywebview.api) init();
  else addEventListener('pywebviewready', init, { once: true });
})();
