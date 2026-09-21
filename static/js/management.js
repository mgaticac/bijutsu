document.querySelectorAll('.formset').forEach(section => {
  section.querySelector('[data-add-form]')?.addEventListener('click', () => {
    const count = section.querySelector(`[name="${section.dataset.prefix}-TOTAL_FORMS"]`);
    const index = Number(count.value);
    const html = section.querySelector('[data-empty-form]').innerHTML.replaceAll('__prefix__', String(index));
    section.querySelector('[data-formset-rows]').insertAdjacentHTML('beforeend', html);
    count.value = index + 1;
    section.querySelector('[data-formset-rows]').lastElementChild.querySelector('input:not([type="hidden"])')?.focus();
  });
});
const slug = document.querySelector('[name="slug"]');
const title = document.querySelector('[name="title"], [name="name"]');
if (slug && title && !slug.value) {
  let manual = false;
  slug.addEventListener('input', () => manual = true);
  title.addEventListener('input', () => {
    if (!manual) slug.value = title.value.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
  });
}
