// ==UserScript==
// @name         Google Scholar: Copy BibTeX + DOI
// @namespace    https://github.com/jintaoXue/ICCBEI2027
// @version      1.3.0
// @description  Copy BibTeX on Scholar search & author pages; add DOI (Crossref fallback)
// @author       You
// @match        https://scholar.google.com/*
// @match        https://scholar.google.com.hk/*
// @match        https://scholar.google.co.uk/*
// @match        https://scholar.google.de/*
// @match        https://scholar.google.fr/*
// @match        https://scholar.google.jp/*
// @match        https://scholar.google.ca/*
// @match        https://scholar.google.com.au/*
// @icon         https://www.google.com/s2/favicons?sz=64&domain=scholar.google.com
// @grant        GM_setClipboard
// @grant        GM_xmlhttpRequest
// @connect      api.crossref.org
// @connect      doi.org
// @connect      scholar.google.com
// @connect      scholar.googleusercontent.com
// @connect      *
// @run-at       document-idle
// ==/UserScript==

(function () {
  'use strict';

  const BTN_CLASS = 'gs-copy-bib-doi-btn';
  const STYLE_ID = 'gs-copy-bib-doi-style';

  function injectStyle() {
    if (document.getElementById(STYLE_ID)) return;
    const style = document.createElement('style');
    style.id = STYLE_ID;
    style.textContent = `
      .${BTN_CLASS}{
        margin-left:8px;padding:1px 8px;font-size:12px;line-height:1.6;cursor:pointer;
        border:1px solid #1a73e8;border-radius:4px;background:#fff;color:#1a73e8;
        vertical-align:middle;white-space:nowrap;
      }
      .${BTN_CLASS}:hover{background:#e8f0fe}
      .${BTN_CLASS}.ok{border-color:#137333;color:#137333}
      .${BTN_CLASS}.err{border-color:#c5221f;color:#c5221f}
      .${BTN_CLASS}:disabled{opacity:.65;cursor:wait}
      tr.gsc_a_tr .${BTN_CLASS}{margin-left:6px;font-size:11px}
    `;
    document.head.appendChild(style);
  }

  function isCitationsPage() {
    return /\/citations/.test(location.pathname);
  }

  function hl() {
    const m = location.search.match(/[?&]hl=([^&]+)/);
    return m ? decodeURIComponent(m[1]) : 'zh-CN';
  }

  function gmGet(url) {
    return new Promise((resolve, reject) => {
      if (typeof GM_xmlhttpRequest === 'function') {
        GM_xmlhttpRequest({
          method: 'GET',
          url,
          anonymous: false,
          withCredentials: true,
          onload: (res) => {
            if (res.status >= 200 && res.status < 300) resolve(res.responseText);
            else reject(new Error('HTTP ' + res.status + ' for ' + url));
          },
          onerror: () => reject(new Error('Network error')),
        });
        return;
      }
      fetch(url, { credentials: 'include' })
        .then(async (r) => {
          if (!r.ok) throw new Error('HTTP ' + r.status);
          return r.text();
        })
        .then(resolve)
        .catch(reject);
    });
  }

  function copyText(text) {
    if (typeof GM_setClipboard === 'function') {
      GM_setClipboard(text, 'text');
      return Promise.resolve();
    }
    return navigator.clipboard.writeText(text);
  }

  function absUrl(u) {
    if (!u) return u;
    u = u.replace(/&amp;/g, '&');
    if (u.startsWith('//')) return location.protocol + u;
    if (u.startsWith('/')) return location.origin + u;
    return u;
  }

  /** Cite URL template from page: /scholar?q=info:{id}:scholar.google.com/&output=cite&scirp={p}&hl=... */
  function citeTemplate() {
    const nodes = document.querySelectorAll('[data-u]');
    for (const n of nodes) {
      const u = n.getAttribute('data-u') || '';
      if (u.indexOf('{id}') >= 0) return u;
    }
    return '/scholar?q=info:{id}:scholar.google.com/&output=cite&scirp={p}&hl=' + encodeURIComponent(hl());
  }

  function findCiteLink(root) {
    return (
      root.querySelector('a.gs_or_cit') ||
      Array.prototype.find.call(root.querySelectorAll('a'), (a) => {
        const t = (a.textContent || '').trim();
        return t === '引用' || t === 'Cite';
      }) ||
      null
    );
  }

  function getSearchTitle(root) {
    const a = root.querySelector('h3.gs_rt a') || root.querySelector('h3.gs_rt');
    if (!a) return '';
    return (a.textContent || '').replace(/\[[^\]]*\]/g, '').trim();
  }

  function getSearchPaperId(root) {
    // New Scholar: <div class="gs_r gs_or gs_scl" data-cid="XXXX">
    const card = root.closest('div.gs_r.gs_or') || root.closest('div.gs_or') || root;
    let cid = card.getAttribute('data-cid') || card.getAttribute('data-aid') || card.getAttribute('data-did');
    if (cid && cid !== 'gs_citd' && cid !== 'gs_md_cita-l') return cid;

    const withCid = card.querySelector('[data-cid]');
    if (withCid) {
      cid = withCid.getAttribute('data-cid');
      if (cid && cid !== 'gs_citd') return cid;
    }

    // related:ID:scholar.google.com
    const links = root.querySelectorAll('a[href]');
    for (let i = 0; i < links.length; i++) {
      const href = links[i].getAttribute('href') || '';
      let m = href.match(/related:([0-9A-Za-z_-]+):scholar/);
      if (m) return m[1];
      m = href.match(/info:([0-9A-Za-z_-]+):scholar/);
      if (m) return m[1];
    }

    // legacy onclick
    const cite = findCiteLink(root);
    if (cite) {
      const oc = cite.getAttribute('onclick') || '';
      const m = oc.match(/gs_ocit\([^,]*,\s*['"]([^'"]+)['"]/);
      if (m) return m[1];
    }

    const html = root.innerHTML || '';
    const m2 = html.match(/related:([0-9A-Za-z_-]+):scholar/);
    return m2 ? m2[1] : null;
  }

  function getCitationForView(row) {
    const a = row.querySelector('a.gsc_a_at') || row.querySelector('a[href*="citation_for_view"]');
    if (!a) return null;
    const href = a.getAttribute('href') || '';
    const m = href.match(/citation_for_view=([^&]+)/);
    return m ? decodeURIComponent(m[1]) : null;
  }

  function getCitationsTitle(row) {
    const a = row.querySelector('a.gsc_a_at');
    return a ? (a.textContent || '').trim() : '';
  }

  function getDoiFromRoot(root) {
    const links = root.querySelectorAll('a[href]');
    for (let i = 0; i < links.length; i++) {
      const href = links[i].href || '';
      let m = href.match(/doi\.org\/(10\.\d{4,9}\/[-._;()/:A-Z0-9]+)/i);
      if (m) return m[1].replace(/[.,;]+$/, '');
      m = href.match(/\/doi\/(?:abs|full|pdf)?\/?(10\.\d{4,9}\/[-._;()/:A-Z0-9]+)/i);
      if (m) return m[1].replace(/[.,;]+$/, '');
    }
    return null;
  }

  function parseBibField(bib, field) {
    const re = new RegExp(field + '\\s*=\\s*\\{([\\s\\S]*?)\\}', 'i');
    const m = bib.match(re);
    return m ? m[1].replace(/\s+/g, ' ').trim() : '';
  }

  function hasDoiField(bib) {
    return /doi\s*=\s*\{/i.test(bib);
  }

  function injectDoi(bib, doi) {
    if (!doi || hasDoiField(bib)) return bib;
    const clean = doi.replace(/^https?:\/\/(dx\.)?doi\.org\//i, '');
    const trimmed = bib.trim().replace(/}\s*$/, '');
    const withComma = /,\s*$/.test(trimmed) ? trimmed : trimmed.replace(/\s*$/, ',');
    return withComma + '\n  doi={' + clean + '}\n}\n';
  }

  function normalizeBib(bib) {
    return (
      bib
        .replace(/\r\n/g, '\n')
        .replace(/\t/g, '  ')
        .replace(/month\s*=\s*\{?[^,}\n]+\}?,?\s*/gi, '')
        .replace(/url\s*=\s*\{[^}]*\},?\s*/gi, '')
        .replace(/ISSN\s*=\s*\{[^}]*\},?\s*/gi, '')
        .replace(/,\s*\n\s*}/g, '\n}')
        .trim() + '\n'
    );
  }

  function makeKey(authors, year, title) {
    const last = (authors.split(/and|,/)[0] || 'ref').trim().split(/\s+/).pop() || 'ref';
    const safe = last.toLowerCase().replace(/[^a-z0-9]/g, '') || 'ref';
    const y = year || 'xxxx';
    const tw = (title || '')
      .toLowerCase()
      .replace(/[^a-z0-9\s]/g, ' ')
      .trim()
      .split(/\s+/)
      .filter(Boolean)
      .slice(0, 2)
      .join('');
    return safe + y + (tw || 'paper');
  }

  function bibFromCrossrefItem(it) {
    const title = (it.title && it.title[0]) || 'Unknown';
    const year =
      (it.published && it.published['date-parts'] && it.published['date-parts'][0] && it.published['date-parts'][0][0]) ||
      (it.created && it.created['date-parts'] && it.created['date-parts'][0] && it.created['date-parts'][0][0]) ||
      '';
    const authors = (it.author || [])
      .map((a) => [a.family, a.given].filter(Boolean).join(', '))
      .filter(Boolean)
      .join(' and ');
    const journal = (it['container-title'] && it['container-title'][0]) || '';
    const volume = it.volume || '';
    const pages = it.page || '';
    const publisher = it.publisher || '';
    const doi = it.DOI || '';
    const type = (it.type || '').indexOf('proceedings') >= 0 ? 'inproceedings' : 'article';
    const key = makeKey(authors, String(year), title);
    let body = '@' + type + '{' + key + ',\n';
    body += '  title={' + title + '},\n';
    if (authors) body += '  author={' + authors + '},\n';
    if (journal) body += '  journal={' + journal + '},\n';
    if (volume) body += '  volume={' + volume + '},\n';
    if (pages) body += '  pages={' + pages + '},\n';
    if (year) body += '  year={' + year + '},\n';
    if (publisher) body += '  publisher={' + publisher + '},\n';
    if (doi) body += '  doi={' + doi + '}\n';
    else body = body.replace(/,\n$/, '\n');
    body += '}\n';
    return body;
  }

  async function lookupCrossref(title) {
    if (!title) return null;
    const url =
      'https://api.crossref.org/works?' +
      new URLSearchParams({
        'query.title': title,
        rows: '5',
        mailto: 'scholar-bibtex-userscript@local',
      }).toString();
    const data = JSON.parse(await gmGet(url));
    const items = data && data.message && data.message.items ? data.message.items : [];
    const norm = (s) =>
      String(s || '')
        .toLowerCase()
        .replace(/[^a-z0-9\u4e00-\u9fff]+/g, ' ')
        .trim();
    const nt = norm(title);
    for (let i = 0; i < items.length; i++) {
      const t = norm(items[i].title && items[i].title[0]);
      if (!t) continue;
      if (t === nt || t.indexOf(nt) >= 0 || nt.indexOf(t) >= 0) return items[i];
    }
    if (!items[0]) return null;
    const t = norm(items[0].title && items[0].title[0]);
    const words = nt.split(' ').filter(Boolean);
    const overlap = words.filter((w) => t.indexOf(w) >= 0).length;
    if (overlap >= Math.min(3, words.length)) return items[0];
    return items[0]; // last resort for manual check
  }

  function extractBibUrlFromCiteHtml(html) {
    let m = html.match(/href="(https:\/\/scholar\.googleusercontent\.com\/scholar\.bib[^"]+)"/i);
    if (m) return absUrl(m[1]);
    m = html.match(/href="(\/scholar\.bib[^"]+)"/i);
    if (m) return absUrl(m[1]);
    m = html.match(/href="([^"]*output=cite[^"]*scholar\.bib[^"]*)"/i);
    if (m) return absUrl(m[1]);
    // sometimes shown as plaintext link text BibTeX
    m = html.match(/<a[^>]+href="([^"]+)"[^>]*>\s*BibTeX\s*<\/a>/i);
    if (m) return absUrl(m[1]);
    return null;
  }

  async function fetchScholarBibById(paperId) {
    const tpl = citeTemplate();
    const path = tpl.replace('{id}', paperId).replace('{p}', '0');
    const citeUrl = absUrl(path);
    const citeHtml = await gmGet(citeUrl);
    const bibUrl = extractBibUrlFromCiteHtml(citeHtml);
    if (!bibUrl) throw new Error('No BibTeX link in cite dialog HTML');
    const bib = await gmGet(bibUrl);
    if (!bib || bib.indexOf('@') < 0) throw new Error('Empty BibTeX body');
    return bib;
  }

  async function fetchCitationsBib(citationForView) {
    const h = encodeURIComponent(hl());
    const tryUrls = [
      location.origin +
        '/citations?view_op=export_citations&hl=' +
        h +
        '&citfmt=data&format=bibtex&citation_for_view=' +
        encodeURIComponent(citationForView),
      location.origin +
        '/citations?view_op=view_citation&hl=' +
        h +
        '&citation_for_view=' +
        encodeURIComponent(citationForView),
    ];
    // include user= if present
    const um = location.search.match(/[?&]user=([^&]+)/);
    if (um) {
      tryUrls.push(
        location.origin +
          '/citations?view_op=view_citation&hl=' +
          h +
          '&user=' +
          um[1] +
          '&citation_for_view=' +
          encodeURIComponent(citationForView)
      );
    }

    for (let i = 0; i < tryUrls.length; i++) {
      try {
        const text = await gmGet(tryUrls[i]);
        if (text.indexOf('@') >= 0 && /@\w+\{/.test(text)) return text;
        const bibUrl = extractBibUrlFromCiteHtml(text);
        if (bibUrl) {
          const bib = await gmGet(bibUrl);
          if (bib && bib.indexOf('@') >= 0) return bib;
        }
        // profile citation page sometimes has "BibTeX" export button URL
        const m = text.match(/href="([^"]*view_op=export_citations[^"]*)"/i);
        if (m) {
          const bib = await gmGet(absUrl(m[1]));
          if (bib && bib.indexOf('@') >= 0) return bib;
        }
      } catch (e) {
        console.warn('citations try failed', tryUrls[i], e);
      }
    }
    throw new Error('Author-page BibTeX export failed');
  }

  async function enrich(bib, root, title) {
    let doi = getDoiFromRoot(root);
    if (!doi && !hasDoiField(bib)) {
      try {
        const it = await lookupCrossref(parseBibField(bib, 'title') || title);
        if (it && it.DOI) doi = it.DOI;
      } catch (e) {
        console.warn(e);
      }
    }
    if (doi) bib = injectDoi(bib, doi);
    return normalizeBib(bib);
  }

  async function buildFromCrossrefOnly(title) {
    const it = await lookupCrossref(title);
    if (!it) throw new Error('Crossref found nothing for: ' + title);
    return normalizeBib(bibFromCrossrefItem(it));
  }

  async function buildBibtexSearch(root) {
    const title = getSearchTitle(root);
    const paperId = getSearchPaperId(root);
    console.log('[GS] paperId=', paperId, 'title=', title);

    if (paperId) {
      try {
        const bib = await fetchScholarBibById(paperId);
        return await enrich(bib, root, title);
      } catch (e) {
        console.warn('Scholar bib failed, fallback Crossref', e);
      }
    }
    if (!title) throw new Error('Cannot find Scholar paper id or title');
    return await buildFromCrossrefOnly(title);
  }

  async function buildBibtexCitations(row) {
    const title = getCitationsTitle(row);
    const cfv = getCitationForView(row);
    console.log('[GS] citation_for_view=', cfv, 'title=', title);

    if (cfv) {
      try {
        const bib = await fetchCitationsBib(cfv);
        return await enrich(bib, row, title);
      } catch (e) {
        console.warn('Citations export failed, fallback Crossref', e);
      }
    }
    if (!title) throw new Error('Cannot find citation_for_view or title');
    return await buildFromCrossrefOnly(title);
  }

  function setBtnState(btn, state, label) {
    btn.classList.remove('ok', 'err');
    if (state) btn.classList.add(state);
    if (label) btn.textContent = label;
  }

  function makeButton(buildFn) {
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = BTN_CLASS;
    btn.textContent = 'Copy BibTeX';
    btn.title = 'Copy BibTeX (+DOI). Falls back to Crossref if needed.';
    btn.addEventListener('click', async (e) => {
      e.preventDefault();
      e.stopPropagation();
      btn.disabled = true;
      setBtnState(btn, null, 'Copying…');
      try {
        const bib = await buildFn();
        await copyText(bib);
        const hasDoi = /doi\s*=\s*\{/i.test(bib);
        setBtnState(btn, 'ok', hasDoi ? 'Copied (+DOI)' : 'Copied (no DOI)');
        console.log('[GS BibTeX]\n' + bib);
      } catch (err) {
        console.error(err);
        setBtnState(btn, 'err', 'Failed');
        alert('Copy BibTeX failed: ' + (err && err.message ? err.message : err));
      } finally {
        btn.disabled = false;
        setTimeout(() => setBtnState(btn, null, 'Copy BibTeX'), 2500);
      }
    });
    return btn;
  }

  function addSearchButton(root) {
    if (root.querySelector('.' + BTN_CLASS)) return;
    if (!root.querySelector('h3.gs_rt')) return;
    // only real result cards
    if (!root.classList.contains('gs_or') && !root.querySelector('.gs_or_cit')) return;

    const btn = makeButton(() => buildBibtexSearch(root));
    const cite = findCiteLink(root);
    if (cite && cite.parentElement) cite.parentElement.appendChild(btn);
    else {
      const t = root.querySelector('h3.gs_rt');
      if (t) t.appendChild(btn);
    }
  }

  function addCitationsButton(row) {
    if (row.querySelector('.' + BTN_CLASS)) return;
    if (!row.querySelector('a.gsc_a_at')) return;
    const btn = makeButton(() => buildBibtexCitations(row));
    const titleLink = row.querySelector('a.gsc_a_at');
    if (titleLink && titleLink.parentElement) titleLink.parentElement.appendChild(btn);
    else row.appendChild(btn);
  }

  function scan() {
    injectStyle();
    if (isCitationsPage()) {
      document.querySelectorAll('tr.gsc_a_tr').forEach(addCitationsButton);
      return;
    }
    document.querySelectorAll('div.gs_r.gs_or, div.gs_r').forEach(addSearchButton);
  }

  scan();
  let timer = null;
  new MutationObserver(() => {
    clearTimeout(timer);
    timer = setTimeout(scan, 250);
  }).observe(document.documentElement, { childList: true, subtree: true });
})();
