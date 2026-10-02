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
      if (status) status.classList.remove('form-error', 'form-success');
      if (status) status.textContent = 'Sending your message...';

      const email = form.querySelector('#email');
      const replyTo = form.querySelector('#replyto');
      if (email && replyTo) replyTo.value = email.value;

      try {
        const secondAction = form.dataset.secondAction;
        const options = {
          method: 'POST',
          body: new FormData(form),
          headers: { Accept: 'application/json' },
        };
        const requests = [fetch(form.action, options)];
        if (secondAction) requests.push(fetch(secondAction, options));
        const responses = await Promise.all(requests);
        if (!responses.every((r) => r.ok)) throw new Error('Formspree request failed');
        form.reset();
        if (status) {
          status.classList.add('form-success');
          status.textContent = 'Thanks. Your message has been sent.';
        }
        formAlertTimer = setTimeout(() => {
          if (status) {
            status.classList.remove('form-success');
            status.textContent = '';
          }
        }, 3000);
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
});
