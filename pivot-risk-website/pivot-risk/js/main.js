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
    const normalize = (p) => p.replace(/\.html$/, '').replace(/^index$/, '');
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
});