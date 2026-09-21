(() => {
  const formatter = new Intl.NumberFormat('es-CL', {style: 'currency', currency: 'CLP', maximumFractionDigits: 0});
  document.querySelectorAll('[data-estimate-url]').forEach(form => {
    let controller;
    const message = form.querySelector('[data-estimate-message]');
    const update = async () => {
      if (controller) controller.abort();
      controller = new AbortController();
      const data = new FormData();
      form.querySelectorAll('[name^="option_"], [name="quantity"]').forEach(input => data.append(input.name, input.value));
      message.textContent = 'Calculando…';
      form.querySelector('[data-unit]').textContent = '—';
      form.querySelector('[data-total]').textContent = '—';
      try {
        const response = await fetch(form.dataset.estimateUrl, {method: 'POST', body: data, signal: controller.signal,
          headers: {'X-CSRFToken': form.dataset.csrf || form.querySelector('[name="csrfmiddlewaretoken"]').value}, credentials: 'same-origin'});
        const result = await response.json();
        if (!response.ok) {
          message.textContent = Object.values(result.errors).flat().map(error => error.message).join(' ');
          return;
        }
        form.querySelector('[data-unit]').textContent = formatter.format(Number(result.unit));
        form.querySelector('[data-total]').textContent = formatter.format(Number(result.total));
        message.textContent = `${result.quantity} unidad${result.quantity > 1 ? 'es' : ''} · Estimación sujeta a revisión`;
      } catch (error) {
        if (error.name !== 'AbortError') message.textContent = 'No pudimos actualizar la estimación. Puedes continuar y el taller revisará tu solicitud.';
      }
    };
    form.querySelectorAll('[name^="option_"], [name="quantity"]').forEach(input => input.addEventListener('change', update));
    update();
  });
})();
