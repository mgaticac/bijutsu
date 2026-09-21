document.querySelectorAll('input[type="file"]').forEach(input => input.addEventListener('change', () => {
  input.setCustomValidity(input.files.length > 5 ? 'Selecciona como máximo 5 archivos.' : '');
  input.reportValidity();
}));
