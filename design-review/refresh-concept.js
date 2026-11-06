/* Visual concept only: no backend, telemetry, clinical data or external sends. */
(() => {
  'use strict';
  const billingButtons = Array.from(document.querySelectorAll('[data-billing]'));
  function setBilling(interval) {
    for (const button of billingButtons) {
      button.setAttribute('aria-pressed', String(button.dataset.billing === interval));
    }
    for (const price of document.querySelectorAll('[data-price]')) {
      const rate = interval === 'annual' ? price.dataset.annual : price.dataset.monthly;
      price.textContent = rate || 'Custom';
      const freq = price.parentElement.querySelector('[data-frequency]');
      const enterprise = !price.dataset.monthly || price.dataset.monthly === 'Custom';
      if (freq) freq.textContent = enterprise ? 'Contact for a quote' :
        interval === 'annual' ? '/ provider / year' : '/ provider / month';
    }
  }
  billingButtons.forEach(button =>
    button.addEventListener('click', () => setBilling(button.dataset.billing))
  );
  const tour = {
    'clinical': ['Clinical workflows', 'Approved interface screenshot required before publication. This panel marks the placement for encounter and documentation views.'],
    'operations': ['Operational coordination', 'Approved product capture required. Review a real billing, inventory, or reporting screen before publishing this step.'],
    'patient': ['Patient experience', 'Approved fictional-data screenshot required. Patient portal and follow-up preview will be included only after verification.'],
  };
  document.querySelectorAll('[data-tour]').forEach(button => {
    button.addEventListener('click', () => {
      document.querySelectorAll('[data-tour]').forEach(item =>
        item.setAttribute('aria-pressed', String(item === button))
      );
      const [title,detail] = tour[button.dataset.tour] || tour.clinical;
      const heading = document.getElementById('refresh-tour-title');
      const description = document.getElementById('refresh-tour-desc');
      if (heading) heading.textContent = title;
      if (description) description.textContent = detail;
    });
  });
  document.querySelectorAll('.refresh-form-fields').forEach(form => {
    form.addEventListener('submit', event => event.preventDefault());
  });
})();
