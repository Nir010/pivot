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

  // Contact form: no backend wired up yet, so guide the user clearly
  const form = document.querySelector('#contact-form');
  const status = document.querySelector('#form-status');
  if (form) {
    form.addEventListener('submit', (e) => {
      e.preventDefault();
      if (status) {
        status.textContent =
          "This form isn't connected to an inbox yet — email us directly at hello@pivotrisk.com.np, or connect a form service (see README) to receive submissions here.";
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
});