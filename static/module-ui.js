/* Shared presentation and authenticated requests for administrative modules. */
window.ModulesUI = {
  escape(value) {
    return String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  },
  async request(path, options = {}) {
    const data = await api(path.replace(/^\/api/, ''), options.method || 'GET', options.body ? JSON.parse(options.body) : undefined);
    return {json: async () => data};
  },
  bind(actions) {
    for (const type of ['click', 'change', 'keyup', 'keydown']) {
      document.addEventListener(type, async event => {
        const element = event.target.closest(`[data-module-${type}]`);
        if (!element || element.disabled || element.dataset.busy) return;
        const action = actions[element.getAttribute(`data-module-${type}`)];
        if (!action) return;
        if (type === 'click') event.preventDefault();
        try {
          element.dataset.busy = 'true';
          element.setAttribute('aria-busy', 'true');
          await action(element, event);
        } catch (error) {
          toast(error.message || 'Não foi possível concluir a operação.', 'error');
        } finally {
          delete element.dataset.busy;
          element.removeAttribute('aria-busy');
        }
      });
    }
    document.addEventListener('keydown', event => {
      if (event.key === 'Escape' && window.BiUI) BiUI.exitKioskMode();
    });
    window.addEventListener('hashchange', () => {
      if (location.hash !== '#/bi' && window.BiUI) BiUI.exitKioskMode();
    });
  },
  show(title, value) {
    const escape = this.escape;
    const render = value => {
      if (value === null || value === undefined || value === '') return '<span class="muted">Não informado</span>';
      if (Array.isArray(value)) return value.length ? value.map(render).join('<hr>') : '<p class="empty">Nenhum registro encontrado.</p>';
      if (typeof value === 'object') return '<dl class="detail-grid">' + Object.entries(value).map(([key, v]) => `<div><dt>${escape(key.replaceAll('_', ' '))}</dt><dd>${render(v)}</dd></div>`).join('') + '</dl>';
      return escape(value);
    };
    openModal(escape(title), render(value));
  },
  form(title, fields, save, onSuccess) {
    const escape = this.escape;
    openModal(escape(title), `<form id="module-editor"><div class="form-grid">${fields.map(f => {
      const [name, label, type = 'text', value = '', optional = false] = f;
      const attrs = `name="${escape(name)}" ${optional ? '' : 'required'} ${type === 'number' ? 'min="0" step="any"' : ''}`;
      return `<label class="field">${escape(label)}${type === 'textarea' ? `<textarea ${attrs}>${escape(value)}</textarea>` : `<input type="${type}" ${attrs} value="${escape(value)}">`}</label>`;
    }).join('')}</div><div class="form-error" role="alert"></div><div class="form-actions"><button type="button" class="button" data-action="close-modal">Cancelar</button><button class="button primary" type="submit">Confirmar</button></div></form>`);
    const form = document.getElementById('module-editor');
    form.addEventListener('submit', async event => {
      event.preventDefault();
      if (!form.reportValidity()) return;
      const submit = form.querySelector('[type=submit]');
      if (submit.disabled) return;
      submit.disabled = true;
      form.querySelector('.form-error').textContent = '';
      try {
        const values = Object.fromEntries(new FormData(form));
        for (const [name, , type] of fields) {
          if (type === 'number') values[name] = Number(values[name]);
          if (type === 'file') values[name] = await form.elements[name].files[0]?.text() || '';
        }
        const data = await save(values);
        closeModal();
        toast('Operação concluída.');
        if (onSuccess) await onSuccess(data);
      } catch (error) {
        if (form.isConnected && document.getElementById('modal').open) form.querySelector('.form-error').textContent = error.message;
        else toast(error.message, true);
      } finally { submit.disabled = false; }
    });
  },
  download(name, content, type = 'text/plain;charset=utf-8') {
    const url = URL.createObjectURL(new Blob([content], {type}));
    const link = document.createElement('a');
    link.href = url; link.download = name; link.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
};
