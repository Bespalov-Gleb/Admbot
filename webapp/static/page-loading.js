/**
 * Универсальная функция для показа loading overlay при переходах между страницами
 */

function showPageLoadingOverlay() {
  // Проверяем, не существует ли уже overlay
  let overlay = document.getElementById('page-loading-overlay');
  
  if (!overlay) {
    // Создаем overlay
    overlay = document.createElement('div');
    overlay.id = 'page-loading-overlay';
    overlay.className = 'page-loading-overlay';
    overlay.innerHTML = `
      <div class="loading-spinner"></div>
      <div class="loading-text">Загрузка...</div>
    `;
    document.body.appendChild(overlay);
  }
  
  // Показываем overlay
  overlay.style.display = 'flex';
  overlay.style.opacity = '0';
  overlay.style.visibility = 'visible';
  
  // Плавное появление
  requestAnimationFrame(() => {
    overlay.style.transition = 'opacity 0.2s ease-in';
    overlay.style.opacity = '1';
  });
}

// Показываем overlay немедленно при загрузке скрипта
// (скрипт загружается синхронно, так что это будет одним из первых действий)
showPageLoadingOverlay();

function hidePageLoadingOverlay() {
  const overlay = document.getElementById('page-loading-overlay');
  if (overlay) {
    overlay.style.opacity = '0';
    setTimeout(() => {
      overlay.style.display = 'none';
      overlay.style.visibility = 'hidden';
    }, 200);
  }
}

// Автоматически скрываем overlay при загрузке страницы,
// если страница не запретила это явным флагом
document.addEventListener('DOMContentLoaded', () => {
  if (!window.pageLoadingAutoHideDisabled) {
    hidePageLoadingOverlay();
  }
});

// Также скрываем при полной загрузке страницы (fallback)
window.addEventListener('load', () => {
  if (!window.pageLoadingAutoHideDisabled) {
    hidePageLoadingOverlay();
  }
});

// Экспортируем для использования
window.showPageLoadingOverlay = showPageLoadingOverlay;
window.hidePageLoadingOverlay = hidePageLoadingOverlay;

