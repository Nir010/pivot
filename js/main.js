// Pivot Risk Pvt. Ltd. — shared site behaviour

document.addEventListener('DOMContentLoaded', () => {
  // Load shared header/footer (html/header.html, html/footer.html)
  const loadIncludes = Promise.all(
    Array.from(document.querySelectorAll('[data-include]')).map((el) =>
      fetch(new URL(`../html/${el.dataset.include.replace(/\.html$/, '')}.html`, document.baseURI))
        .then((res) => (res.ok ? res.text() : Promise.reject(new Error(`Failed to load ${el.dataset.include}`))))
        .then((html) => {
          el.innerHTML = html;
        })
        .catch((err) => console.error(err))
    )
  );

  loadIncludes.then(() => {
    // Mobile nav toggle
    const toggle = document.querySelector('.nav-toggle');
    const links = document.querySelector('.nav-links');
    if (toggle && links) {
      toggle.addEventListener('click', () => {
        const isOpen = links.classList.toggle('open');
        toggle.setAttribute('aria-expanded', String(isOpen));
      });
      links.querySelectorAll('a').forEach((a) => {
        a.addEventListener('click', () => {
          links.classList.remove('open');
          toggle.setAttribute('aria-expanded', 'false');
        });
      });
    }

    // Highlight the current page in the nav
    const current = location.pathname.split('/').filter(Boolean).pop() || 'index.html';
    const normalize = (href) => {
      const file = (href.split('/').pop() || 'index.html').replace(/\.html$/i, '');
      return file === 'index' ? 'home' : file;
    };
    document.querySelectorAll('.nav-links a').forEach((a) => {
      if (normalize(a.getAttribute('href')) === normalize(current)) a.classList.add('active');
    });

    // Footer year
    const yearEl = document.querySelector('[data-year]');
    if (yearEl) yearEl.textContent = new Date().getFullYear();
  });

  // Services page: reveal the additional services on demand
  const servicesToggle = document.querySelector('#toggle-services');
  const moreServices = document.querySelector('#more-services');
  if (servicesToggle && moreServices) {
    servicesToggle.addEventListener('click', () => {
      const isOpen = !moreServices.classList.contains('is-hidden');
      moreServices.classList.toggle('is-hidden', isOpen);
      servicesToggle.setAttribute('aria-expanded', String(!isOpen));
      servicesToggle.textContent = isOpen ? 'View full services' : 'Show less';
      if (!isOpen) moreServices.scrollIntoView({ behavior: 'smooth', block: 'start' });
    });
  }

  // Contact form: submit through Formspree without leaving the page
  const form = document.querySelector('#contact-form');
  const status = document.querySelector('#form-status');
  if (form) {
    let formAlertTimer;
    form.addEventListener('submit', async (e) => {
      e.preventDefault();
      clearTimeout(formAlertTimer);
      if (status) status.classList.remove('form-error');
      if (status) status.textContent = 'Sending your message...';

      const email = form.querySelector('#email');
      const replyTo = form.querySelector('#replyto');
      if (email && replyTo) replyTo.value = email.value;

      try {
        const response = await fetch(form.action, {
          method: 'POST',
          body: new FormData(form),
          headers: { Accept: 'application/json' },
        });
        if (!response.ok) throw new Error('Formspree request failed');
        form.reset();
        if (status) status.textContent = 'Thanks. Your message has been sent.';
      } catch (err) {
        if (status) status.classList.add('form-error');
        if (status) status.textContent = 'Sorry, your message could not be sent. Please email us directly.';
        formAlertTimer = setTimeout(() => {
          if (status) {
            status.classList.remove('form-error');
            status.textContent = '';
          }
        }, 3000);
      }
    });
  }

  // Blog page: render published PDF blogs
  const blogList = document.querySelector('#blog-list');
  if (blogList) {
    const esc = (s) =>
      String(s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

    const TEMPLATE_BLOGS = [
      {
        title: 'Actuarial Thinking for Everyday Decisions',
        category: 'Actuarial',
        desc: 'A practical look at how actuarial discipline — valuation, reserving and pricing — sharpens everyday business decisions.',
        date: '2026-09-21',
        pdf: '/blogs/actuarial-thinking-2026.pdf',
        img: '/images/blog/actuarial-thinking.jpg',
      },
      {
        title: 'Building Resilience in a Changing Nepal',
        category: 'Resilience',
        desc: 'How scenario planning, financial preparation and local operating knowledge hold together as one connected discipline.',
        date: '2026-09-21',
        pdf: '/blogs/resilience-nepal-2026.pdf',
        img: '',
      },      
    ];

    const readDate = (iso) => {
      if (!iso) return '';
      const d = new Date(iso + 'T00:00:00');
      if (Number.isNaN(d.getTime())) return iso;
      return d.toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' });
    };

    const cardFor = (b, index) => {
      const cover = b.img
        ? `<div class="blog-cover"><img src="${esc(b.img)}" alt="${esc(b.title)}" loading="lazy"></div>`
        : '';
      return `
        <article class="blog-card${b.img ? ' has-cover' : ''}">
          ${cover}
          <span class="index">${String(index).padStart(2, '0')}</span>
          <span class="category">${esc(b.category || 'Journal')}</span>
          <h3><a href="${esc(b.pdf)}" data-blog-pdf>${esc(b.title)}</a></h3>
          <p>${esc(b.desc)}</p>
          <span class="meta">Published ${esc(readDate(b.date))}</span>
          <a class="read-link" href="${esc(b.pdf)}" data-blog-pdf>Open blog</a>
        </article>`;
    };

    blogList.innerHTML = TEMPLATE_BLOGS.map((b, i) => cardFor(b, i + 1)).join('');

    // Open the PDF in an embedded popup viewer on the same page.
    const pdfModal = document.querySelector('#pdf-modal');
    const pdfFrame = document.querySelector('#pdf-frame');
    const pdfTitle = document.querySelector('#pdf-modal-title');
    if (pdfModal && pdfFrame) {
      const openPdf = (url) => {
        pdfFrame.src = url;
        pdfModal.classList.add('open');
        pdfModal.setAttribute('aria-hidden', 'false');
        document.body.style.overflow = 'hidden';
      };
      const closePdf = () => {
        pdfModal.classList.remove('open');
        pdfModal.setAttribute('aria-hidden', 'true');
        pdfFrame.removeAttribute('src');
        document.body.style.overflow = '';
      };

      blogList.addEventListener('click', (e) => {
        const link = e.target.closest('[data-blog-pdf]');
        if (!link) return;
        e.preventDefault();
        const card = link.closest('.blog-card');
        if (pdfTitle && card) pdfTitle.textContent = card.querySelector('h3').textContent;
        openPdf(link.getAttribute('href'));
      });

      pdfModal.addEventListener('click', (e) => {
        if (e.target.closest('[data-pdf-close]')) closePdf();
      });
      document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && pdfModal.classList.contains('open')) closePdf();
      });
      pdfFrame.addEventListener('load', () => {});
    }
  }

  // Team page: name + designation rows that open a profile popup
  const teamData = document.querySelector('#team-data');
  if (teamData) {
    const esc = (s) =>
      String(s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

    let members = [];
    try {
      members = JSON.parse(teamData.textContent);
    } catch (err) {
      members = [];
    }

    const leadershipList = document.querySelector('#leadership-list');
    const membersList = document.querySelector('#members-list');

    const rowFor = (m) => `
      <div class="${m.group === 'leadership' ? 'leader' : 'person'}">
        <div class="photo"><img src="${esc(m.photo)}" alt="${esc(m.name)}" loading="lazy"></div>
        <div class="person-head">
          <div class="team-intro">
            <h3>${esc(m.name)}</h3>
            <span class="team-designation">${esc(m.designation)}</span>
          </div>
          <button type="button" class="team-info" data-team-open aria-label="View ${esc(m.name)}'s profile" title="View profile">
            <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
              <circle cx="12" cy="12" r="10"></circle>
              <line x1="12" y1="16" x2="12" y2="12"></line>
              <line x1="12" y1="8" x2="12.01" y2="8"></line>
            </svg>
            <span class="team-info-label">More info</span>
          </button>
        </div>
      </div>`;

    if (leadershipList) leadershipList.innerHTML = members.filter((m) => m.group === 'leadership').map(rowFor).join('');
    if (membersList) membersList.innerHTML = members.filter((m) => m.group === 'members').map(rowFor).join('');

    const teamModal = document.querySelector('#team-modal');
    const teamPhoto = document.querySelector('#team-photo');
    const teamName = document.querySelector('#team-name');
    const teamDesignation = document.querySelector('#team-designation');
    const teamDetails = document.querySelector('#team-details');

    const listFor = (items) =>
      items && items.length
        ? `<ul class="team-detail-list">${items.map((i) => `<li>${esc(i)}</li>`).join('')}</ul>`
        : '<p class="team-detail-empty">Details will be added soon.</p>';

    const detailsFor = (m) => `
      <div class="team-detail">
        <h4>Qualifications</h4>
        ${listFor(m.qualifications)}
      </div>
      <div class="team-detail">
        <h4>Experience</h4>
        ${listFor(m.experience)}
      </div>
      <div class="team-detail">
        <h4>Major works</h4>
        ${listFor(m.works)}
      </div>`;

    const openProfile = (m) => {
      if (!teamModal) return;
      if (teamName) teamName.textContent = m.name;
      if (teamDesignation) teamDesignation.textContent = m.designation;
      if (teamPhoto) {
        teamPhoto.innerHTML = m.photo
          ? `<img src="${esc(m.photo)}" alt="${esc(m.name)}">`
          : `<span class="team-photo-fallback">${esc(m.name.charAt(0))}</span>`;
      }
      if (teamDetails) teamDetails.innerHTML = detailsFor(m);
      teamModal.classList.add('open');
      teamModal.setAttribute('aria-hidden', 'false');
      document.body.style.overflow = 'hidden';
    };
    const closeProfile = () => {
      if (!teamModal) return;
      teamModal.classList.remove('open');
      teamModal.setAttribute('aria-hidden', 'true');
      document.body.style.overflow = '';
    };

    [leadershipList, membersList].forEach((list) => {
      if (!list) return;
      list.addEventListener('click', (e) => {
        const btn = e.target.closest('[data-team-open]');
        if (!btn) return;
        const row = btn.closest('.person, .leader');
        const name = row && row.querySelector('h3') ? row.querySelector('h3').textContent : '';
        const member = members.find((m) => m.name === name);
        if (member) openProfile(member);
      });
    });

    if (teamModal) {
      teamModal.addEventListener('click', (e) => {
        if (e.target.closest('[data-team-close]')) closeProfile();
      });
      document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && teamModal.classList.contains('open')) closeProfile();
      });
    }
  }
});