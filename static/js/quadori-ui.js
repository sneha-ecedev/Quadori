document.addEventListener('DOMContentLoaded', () => {
  const loader = document.querySelector('.q-loader');

  document.querySelectorAll('form').forEach((form) => {
    form.addEventListener('submit', () => {
      const submit = form.querySelector('button[type="submit"], input[type="submit"]');
      if (submit && !form.checkValidity()) return;
      if (submit && submit.tagName === 'BUTTON') {
        submit.dataset.originalText = submit.innerHTML;
        submit.disabled = true;
        submit.classList.add('q-loading-button');
        submit.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Please wait';
      }
      loader?.classList.add('is-visible');
    });
  });
});
