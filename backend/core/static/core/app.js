(() => {
  'use strict';
  const dialog = document.getElementById('confirm-dialog');
  let accept = null;
  let returnFocus = null;
  const openDialog = (title, text, label, danger, callback, origin) => {
    if (!dialog) return;
    returnFocus = origin || document.activeElement;
    document.getElementById('confirm-title').textContent = title;
    document.getElementById('confirm-description').textContent = text;
    const action = document.getElementById('confirm-action');
    action.textContent = label;
    action.classList.toggle('btn-danger', danger);
    accept = callback;
    dialog.showModal();
    document.getElementById('confirm-cancel').focus();
  };
  const confirmAction = () => {
    const callback = accept;
    dialog.close();
    if (callback) callback();
  };
  dialog?.addEventListener('close', () => {
    accept = null;
    if (returnFocus?.isConnected) returnFocus.focus();
  });
  const navToggle = document.getElementById('nav-toggle');
  const toggleNavigation = () => {
    const expanded = navToggle.getAttribute('aria-expanded') !== 'true';
    navToggle.setAttribute('aria-expanded', String(expanded));
    document.getElementById('app-navigation').classList.toggle('is-open', expanded);
  };
  const togglePassword = button => {
      const input = document.getElementById(button.dataset.passwordToggle);
      const showing = input.type === 'password';
      input.type = showing ? 'text' : 'password';
      button.setAttribute('aria-label', showing ? 'Hide password' : 'Show password');
      button.setAttribute('aria-pressed', String(showing));
  };
  const clearSearch = button => {
      const input = document.getElementById(button.dataset.clearSearch);
      input.value = '';
      input.focus();
      const form = input.form;
      const page = form.querySelector('[name=page]');
      if (page) page.remove();
      form.requestSubmit();
  };
  window.ALsJUI = {
    toggleNavigation, togglePassword, clearSearch,
    cancelConfirmation: () => dialog.close(), confirmAction,
  };
  const forms = [...document.querySelectorAll('form[method=post]')];
  const fieldError = (field, text) => {
    if (!field.id) return;
    let error = document.getElementById(field.id + '-error');
    if (!error) {
      error = document.createElement('span');
      error.id = field.id + '-error';
      error.className = 'field-error';
      field.closest('.field')?.appendChild(error);
    }
    error.textContent = text;
    error.hidden = !text;
    field.setAttribute('aria-invalid', String(Boolean(text)));
    const ids = new Set((field.getAttribute('aria-describedby') || '').split(' ').filter(Boolean));
    ids.add(error.id);
    field.setAttribute('aria-describedby', [...ids].join(' '));
  };
  forms.forEach(form => {
    const safeDirty = form.hasAttribute('data-dirty-guard');
    form.addEventListener('input', event => {
      if (safeDirty && event.target.type !== 'password') form.dataset.dirty = 'true';
      if (event.target.matches('input,select,textarea')) fieldError(event.target, '');
    });
    const decision = form.querySelector('[name=decision]');
    const reason = form.querySelector('[name=reason]');
    if (decision && reason) {
      const update = () => {
        reason.required = decision.value === 'REJECTED';
        const required = form.querySelector('[data-reason-required]');
        if (required) required.hidden = !reason.required;
      };
      decision.addEventListener('change', update);
      update();
    }
    form.addEventListener('submit', event => {
      if (form.dataset.submitting === 'true') { event.preventDefault(); return; }
      if (navigator.onLine === false) {
        event.preventDefault();
        document.getElementById('offline-banner').hidden = false;
        return;
      }
      if (form.hasAttribute('data-validate')) {
        let first = null;
        form.querySelectorAll('input:not([type=hidden]),select,textarea').forEach(field => {
          let message = '';
          if (field.required && !field.value.trim()) message = 'Enter ' + (field.dataset.label || 'this value') + '.';
          else if (field.validity.tooLong) message = 'Shorten this value.';
          else if (field.validity.typeMismatch || field.validity.badInput) message = 'Enter a valid ' + (field.dataset.label || 'value') + '.';
          fieldError(field, message);
          if (message && !first) first = field;
        });
        if (first) { event.preventDefault(); first.focus(); return; }
      }
      if (form.dataset.confirm && form.dataset.confirmed !== 'true') {
        event.preventDefault();
        let message = form.dataset.confirm;
        if (form.dataset.stageConfirm) {
          const selected = form.querySelector('select');
          message = 'Move this application to ' + selected.options[selected.selectedIndex].text + '? A new stage history entry will be recorded.';
        }
        openDialog(form.dataset.confirmTitle || 'Confirm change', message,
          form.dataset.confirmAction || 'Confirm change', form.dataset.danger === 'true',
          () => { form.dataset.confirmed = 'true'; form.requestSubmit(event.submitter || undefined); },
          event.submitter);
        return;
      }
      form.dataset.submitting = 'true';
      form.dataset.dirty = 'false';
      form.setAttribute('aria-busy','true');
      setTimeout(() => form.querySelectorAll('button[type=submit],button:not([type])').forEach(button => {
        button.dataset.originalLabel = button.textContent;
        button.disabled = true;
        if (button.dataset.busyLabel) button.textContent = button.dataset.busyLabel;
      }), 0);
    });
  });
  const dirty = () => forms.some(form => form.dataset.dirty === 'true');
  window.addEventListener('beforeunload', event => {
    if (dirty()) { event.preventDefault(); event.returnValue = ''; }
  });
  document.addEventListener('click', event => {
    const link = event.target.closest('a[href]');
    if (!link || !dirty() || link.target || event.ctrlKey || event.metaKey || link.href === location.href) return;
    if (link.hash && link.pathname === location.pathname) return;
    event.preventDefault();
    openDialog('Leave unsaved changes?', 'Your unsaved form entries will be lost.',
      'Leave page', true, () => {
        forms.forEach(form => form.dataset.dirty = 'false');
        location.assign(link.href);
      }, link);
  });
  const networkState = () => {
    const banner = document.getElementById('offline-banner');
    if (banner) banner.hidden = navigator.onLine !== false;
  };
  window.addEventListener('offline',networkState);
  window.addEventListener('online',networkState);
  networkState();
  window.addEventListener('pageshow', () => {
    forms.forEach(form => {
      form.dataset.submitting = 'false';
      form.dataset.confirmed = 'false';
      form.removeAttribute('aria-busy');
      form.querySelectorAll('button[data-original-label]').forEach(button => {
        button.disabled = false;
        button.textContent = button.dataset.originalLabel;
      });
    });
  });
  document.querySelector('[data-error-summary]')?.focus();
})();
