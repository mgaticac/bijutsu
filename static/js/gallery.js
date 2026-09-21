(() => {
  const modal = document.getElementById('lightbox');
  if (!modal || !window.bootstrap) return;
  const image = document.getElementById('lightbox-image');
  const title = document.getElementById('lightbox-title');
  let group = [], index = 0;
  function show() {
    const button = group[index];
    image.src = button.dataset.image;
    image.alt = button.dataset.caption || 'Fotografía';
    title.textContent = image.alt;
    document.getElementById('gallery-prev').disabled = group.length < 2;
    document.getElementById('gallery-next').disabled = group.length < 2;
  }
  document.querySelectorAll('[data-gallery]').forEach(button => button.addEventListener('click', () => {
    group = [...document.querySelectorAll('[data-gallery]')].filter(item => item.dataset.gallery === button.dataset.gallery);
    index = group.indexOf(button);
    show();
    bootstrap.Modal.getOrCreateInstance(modal).show();
  }));
  const move = step => { if (group.length) { index = (index + step + group.length) % group.length; show(); } };
  document.getElementById('gallery-prev').addEventListener('click', () => move(-1));
  document.getElementById('gallery-next').addEventListener('click', () => move(1));
  modal.addEventListener('keydown', event => {
    if (event.key === 'ArrowLeft') move(-1);
    if (event.key === 'ArrowRight') move(1);
  });
})();
