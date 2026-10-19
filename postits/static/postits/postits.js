/* Notas post-it flotantes. Autocontenido: sin dependencias del proyecto anfitrión.
   API pública: window.Postits.setContexto({tipo: 'app.model', id: 1, etiqueta: '…'} | null) */
(function () {
  const root = document.getElementById('postits-root');
  if (!root) return;
  const CSRF = root.dataset.csrf, BASE = root.dataset.base;
  const $ = id => document.getElementById(id);
  const COLORES = ['amarillo', 'rosa', 'verde', 'azul', 'naranja'];
  const ST = { abierto: false, tab: 'gen', ctx: null, arch: false, notas: [] };
  const timers = {};

  const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g,
    c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const aviso = (m, t) => (window.Alert ? window.Alert.show(m, t || 'error', { autoHide: 4000 }) : console.warn(m));

  async function api(ruta, cuerpo) {
    try {
      const r = await fetch(BASE + ruta, cuerpo === undefined ? {} : {
        method: 'POST', headers: { 'Content-Type': 'application/json', 'X-CSRFToken': CSRF },
        body: JSON.stringify(cuerpo),
      });
      const d = await r.json();
      if (!r.ok) { aviso(d.error || 'Error'); return null; }
      return d;
    } catch (e) { aviso('No se pudo conectar.'); return null; }
  }

  async function badge() {
    const d = await api('resumen/');
    const b = $('postits-badge');
    if (!d) return;
    const n = d.vencidas || 0, a = d.activas || 0;
    b.textContent = n; b.classList.toggle('hidden', !n);
    $('postits-count').textContent = a; $('postits-count').classList.toggle('hidden', !a);
    $('postits-fab').classList.toggle('alerta', n > 0);
  }

  function tabs() {
    const tieneCtx = !!ST.ctx;
    $('postits-tab-obj').classList.toggle('hidden', !tieneCtx);
    if (!tieneCtx && ST.tab === 'obj') ST.tab = 'gen';
    $('postits-tab-obj').textContent = tieneCtx && ST.ctx.etiqueta ? ST.ctx.etiqueta : 'Este proyecto';
    $('postits-tab-obj').classList.toggle('tab-active', ST.tab === 'obj');
    $('postits-tab-gen').classList.toggle('tab-active', ST.tab === 'gen');
  }

  async function cargar() {
    tabs();
    if (!ST.abierto) return;
    let q = '?archivadas=' + (ST.arch ? 1 : 0);
    if (ST.tab === 'obj') q += '&tipo=' + encodeURIComponent(ST.ctx.tipo) + '&id=' + encodeURIComponent(ST.ctx.id);
    const d = await api(q);
    if (!d) return;
    ST.notas = d.postits;
    pintar();
  }

  function pintarItems(p) {
    const items = p.items.map(i => `
      <div class="postit-item ${i.hecho ? 'hecho' : ''}" data-item="${i.id}">
        <input type="checkbox" ${i.hecho ? 'checked' : ''} ${p.es_mio ? '' : 'disabled'} data-act="item-hecho">
        <span>${esc(i.texto)}</span>
        ${p.es_mio ? '<button type="button" data-act="item-borrar" aria-label="Quitar">×</button>' : ''}
      </div>`).join('');
    return items + (p.es_mio ? '<input type="text" placeholder="+ ítem (Enter)" data-act="item-nuevo">' : '');
  }

  function pintarNota(p) {
    const tools = !p.es_mio ? '' : `
      <div class="postit-tools">
        ${COLORES.map(c => `<button type="button" class="postit-dot" data-act="color" data-color="${c}" title="${c}" data-bg="${c}"></button>`).join('')}
        <button type="button" data-act="fijar" class="${p.fijada ? 'on' : ''}" title="Fijar"><i class="fa-solid fa-thumbtack"></i></button>
        ${ST.tab === 'obj' ? `<button type="button" data-act="compartir" class="${p.compartida ? 'on' : ''}" title="Compartir con quienes ven el proyecto"><i class="fa-solid fa-share-nodes"></i></button>` : ''}
        <button type="button" data-act="archivar" title="${p.archivada ? 'Desarchivar' : 'Archivar'}"><i class="fa-solid fa-box-archive"></i></button>
        <button type="button" data-act="borrar" title="Borrar"><i class="fa-solid fa-trash"></i></button>
      </div>`;
    return `
      <article class="postit ${p.vencida ? 'vencida' : ''}" data-id="${p.id}" data-color="${p.color}">
        <textarea ${p.es_mio ? '' : 'readonly'} placeholder="Escribe una nota…" data-act="texto">${esc(p.texto)}</textarea>
        <div class="postit-items">${pintarItems(p)}</div>
        <div class="postit-meta">
          ${p.fijada ? '<i class="fa-solid fa-thumbtack"></i>' : ''}
          ${p.compartida ? '<i class="fa-solid fa-share-nodes" title="Compartida"></i>' : ''}
          ${p.es_mio ? '' : `<span>de ${esc(p.autor)}</span>`}
          ${p.es_mio
            ? `<input type="date" value="${esc(p.recordatorio)}" data-act="fecha" title="Recordatorio">`
            : (p.recordatorio ? `<span>⏰ ${esc(p.recordatorio)}</span>` : '')}
          ${p.vencida ? '<strong>vencida</strong>' : ''}
        </div>
        ${tools}
      </article>`;
  }

  function pintar() {
    const l = $('postits-lista');
    l.innerHTML = ST.notas.length ? ST.notas.map(pintarNota).join('')
      : '<div class="postit-vacio">Sin notas todavía.</div>';
    const pal = { amarillo: '#fde68a', rosa: '#fbcfe8', verde: '#bbf7d0', azul: '#bfdbfe', naranja: '#fed7aa' };
    l.querySelectorAll('[data-bg]').forEach(b => { b.style.background = pal[b.dataset.bg]; });
  }

  const nota = el => ST.notas.find(n => n.id === +el.closest('.postit').dataset.id);

  async function editar(p, campos, repintar) {
    const d = await api(p.id + '/editar/', campos);
    if (!d) return;
    Object.assign(p, d.postit);
    if (repintar) cargar(); else badge();
  }

  $('postits-lista').addEventListener('click', async e => {
    const b = e.target.closest('[data-act]');
    if (!b || b.tagName === 'TEXTAREA' || b.tagName === 'INPUT') return;
    const p = nota(b); if (!p) return;
    const act = b.dataset.act;
    if (act === 'color') editar(p, { color: b.dataset.color }, false).then(() => {
      b.closest('.postit').dataset.color = p.color; });
    else if (act === 'fijar') editar(p, { fijada: !p.fijada }, true);
    else if (act === 'compartir') editar(p, { compartida: !p.compartida }, true);
    else if (act === 'archivar') editar(p, { archivada: !p.archivada }, true);
    else if (act === 'borrar') {
      if (!confirm('¿Borrar esta nota?')) return;
      if (await api(p.id + '/borrar/', {})) { cargar(); badge(); }
    } else if (act === 'item-borrar') {
      const id = b.closest('.postit-item').dataset.item;
      if (await api('item/' + id + '/borrar/', {})) { p.items = p.items.filter(i => i.id !== +id); pintar(); }
    }
  });

  $('postits-lista').addEventListener('input', e => {
    if (e.target.dataset.act !== 'texto') return;
    const p = nota(e.target);
    clearTimeout(timers[p.id]);
    timers[p.id] = setTimeout(() => editar(p, { texto: e.target.value }, false), 600);
  });

  $('postits-lista').addEventListener('change', async e => {
    const act = e.target.dataset.act, p = nota(e.target);
    if (!p) return;
    if (act === 'fecha') editar(p, { recordatorio: e.target.value }, true);
    else if (act === 'item-hecho') {
      const id = +e.target.closest('.postit-item').dataset.item;
      const d = await api('item/' + id + '/editar/', { hecho: e.target.checked });
      if (d) { p.items.find(i => i.id === id).hecho = d.item.hecho; pintar(); }
    }
  });

  $('postits-lista').addEventListener('keydown', async e => {
    if (e.key !== 'Enter' || e.target.dataset.act !== 'item-nuevo') return;
    e.preventDefault();
    const texto = e.target.value.trim(), p = nota(e.target);
    if (!texto) return;
    const d = await api(p.id + '/item/crear/', { texto });
    if (d) { p.items.push(d.item); pintar(); }
  });

  $('postits-nueva').addEventListener('click', async () => {
    const cuerpo = ST.tab === 'obj' ? { tipo: ST.ctx.tipo, id: ST.ctx.id } : {};
    const d = await api('crear/', cuerpo);
    if (d) { ST.arch = false; $('postits-arch').checked = false; await cargar(); }
  });
  $('postits-arch').addEventListener('change', e => { ST.arch = e.target.checked; cargar(); });
  document.querySelectorAll('#postits-panel [data-tab]').forEach(b =>
    b.addEventListener('click', () => { ST.tab = b.dataset.tab; cargar(); }));

  function abrir(v) {
    ST.abierto = v;
    $('postits-panel').classList.toggle('hidden', !v);
    if (v) cargar();
  }
  $('postits-fab').addEventListener('click', () => abrir(!ST.abierto));
  $('postits-cerrar').addEventListener('click', () => abrir(false));
  document.addEventListener('keydown', e => { if (e.key === 'Escape' && ST.abierto) abrir(false); });

  function setContexto(ctx) {
    const igual = JSON.stringify(ctx) === JSON.stringify(ST.ctx);
    ST.ctx = ctx && ctx.tipo && ctx.id != null ? ctx : null;
    if (ST.ctx && !igual) ST.tab = 'obj';
    if (!igual) cargar(); else tabs();
  }
  window.Postits = { setContexto, abrir: () => abrir(true) };
  document.addEventListener('postits:contexto', e => setContexto(e.detail));
  tabs(); badge();
})();
