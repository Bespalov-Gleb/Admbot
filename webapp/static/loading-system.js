/**
 * Универсальная система загрузки и skeleton screens
 * Обеспечивает плавную загрузку контента без пустых экранов
 */

class LoadingSystem {
  constructor() {
    this.activeLoaders = new Map();
  }

  /**
   * Показать skeleton screen
   * @param {string} containerId - ID контейнера
   * @param {string} type - Тип skeleton (cards, list, grid, text)
   * @param {number} count - Количество элементов
   */
  static showSkeleton(containerId, type = 'cards', count = 6) {
    const container = document.getElementById(containerId);
    if (!container) {
      console.warn(`Container ${containerId} not found`);
      return;
    }

    const skeleton = this.createSkeleton(type, count);
    container.innerHTML = '';
    container.appendChild(skeleton);
    
    // Добавляем анимацию появления
    skeleton.classList.add('skeleton-appear');
  }

  /**
   * Создать skeleton элемент
   */
  static createSkeleton(type, count) {
    const skeleton = document.createElement('div');
    skeleton.className = 'skeleton-container';
    
    switch(type) {
      case 'cards':
        skeleton.innerHTML = Array(count).fill(0).map((_, i) => `
          <div class="skeleton-card" style="animation-delay: ${i * 0.1}s">
            <div class="skeleton-image"></div>
            <div class="skeleton-content">
              <div class="skeleton-text"></div>
              <div class="skeleton-text short"></div>
              <div class="skeleton-price"></div>
            </div>
          </div>
        `).join('');
        break;
        
      case 'list':
        skeleton.innerHTML = Array(count).fill(0).map((_, i) => `
          <div class="skeleton-list-item" style="animation-delay: ${i * 0.1}s">
            <div class="skeleton-avatar"></div>
            <div class="skeleton-content">
              <div class="skeleton-text"></div>
              <div class="skeleton-text short"></div>
            </div>
          </div>
        `).join('');
        break;
        
      case 'grid':
        skeleton.innerHTML = Array(count).fill(0).map((_, i) => `
          <div class="skeleton-grid-item" style="animation-delay: ${i * 0.1}s">
            <div class="skeleton-image"></div>
            <div class="skeleton-text"></div>
          </div>
        `).join('');
        break;
        
      case 'text':
        skeleton.innerHTML = Array(count).fill(0).map((_, i) => `
          <div class="skeleton-text-line" style="animation-delay: ${i * 0.1}s"></div>
        `).join('');
        break;
        
      case 'restaurant':
        skeleton.innerHTML = Array(count).fill(0).map((_, i) => `
          <div class="skeleton-restaurant" style="animation-delay: ${i * 0.1}s">
            <div class="skeleton-hero"></div>
            <div class="skeleton-info">
              <div class="skeleton-text"></div>
              <div class="skeleton-text short"></div>
              <div class="skeleton-meta">
                <div class="skeleton-badge"></div>
                <div class="skeleton-badge"></div>
              </div>
            </div>
          </div>
        `).join('');
        break;
    }
    
    return skeleton;
  }

  /**
   * Скрыть skeleton и показать контент
   */
  static hideSkeleton(containerId, content) {
    const container = document.getElementById(containerId);
    if (!container) return;

    // Плавно скрываем skeleton
    const skeleton = container.querySelector('.skeleton-container');
    if (skeleton) {
      skeleton.classList.add('skeleton-fade-out');
      setTimeout(() => {
        container.innerHTML = content;
        container.classList.add('content-appear');
      }, 200);
    } else {
      container.innerHTML = content;
      container.classList.add('content-appear');
    }
  }

  /**
   * Показать loading spinner
   */
  static showSpinner(containerId, text = 'Загрузка...') {
    const container = document.getElementById(containerId);
    if (!container) return;

    container.innerHTML = `
      <div class="loading-spinner-container">
        <div class="loading-spinner"></div>
        <div class="loading-text">${text}</div>
      </div>
    `;
  }

  /**
   * Показать error state с retry кнопкой
   */
  static showError(containerId, message, onRetry) {
    const container = document.getElementById(containerId);
    if (!container) return;

    container.innerHTML = `
      <div class="error-state">
        <div class="error-icon">⚠️</div>
        <div class="error-message">${message}</div>
        ${onRetry ? `<button class="retry-btn" onclick="(${onRetry.toString()})()">Повторить</button>` : ''}
      </div>
    `;
  }

  /**
   * Показать empty state
   */
  static showEmpty(containerId, message, icon = '📭') {
    const container = document.getElementById(containerId);
    if (!container) return;

    container.innerHTML = `
      <div class="empty-state">
        <div class="empty-icon">${icon}</div>
        <div class="empty-message">${message}</div>
      </div>
    `;
  }

  /**
   * Обертка для async функций с автоматическим loading state
   */
  static async withLoading(containerId, asyncFunction, options = {}) {
    const {
      skeletonType = 'cards',
      skeletonCount = 6,
      loadingText = 'Загрузка...',
      errorMessage = 'Произошла ошибка'
    } = options;

    try {
      // Показываем skeleton
      this.showSkeleton(containerId, skeletonType, skeletonCount);
      
      // Выполняем функцию
      const result = await asyncFunction();
      
      // Скрываем skeleton
      this.hideSkeleton(containerId, result);
      
      return result;
    } catch (error) {
      console.error('Loading error:', error);
      this.showError(containerId, errorMessage, asyncFunction);
      throw error;
    }
  }
}

// Экспортируем для использования
window.LoadingSystem = LoadingSystem;