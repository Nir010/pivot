// Pivot Risk Pvt. Ltd. — shared site behaviour

document.addEventListener('DOMContentLoaded', () => {
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

  // Footer year
  const yearEl = document.querySelector('[data-year]');
  if (yearEl) yearEl.textContent = new Date().getFullYear();

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
