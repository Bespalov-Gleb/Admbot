/**
 * Улучшенная система toast уведомлений
 * Обеспечивает красивые и информативные уведомления для пользователя
 */

class ToastSystem {
  constructor() {
    this.toasts = [];
    this.maxToasts = 3;
    this.defaultDuration = 3000;
    this.init();
  }

  init() {
    // Создаем контейнер для toast уведомлений
    this.createToastContainer();
  }

  /**
   * Создать контейнер для toast уведомлений
   */
  createToastContainer() {
    // Проверяем, что document.body существует
    if (!document.body) {
      // Если body еще не готов, ждем его загрузки
      document.addEventListener('DOMContentLoaded', () => {
        this.createToastContainer();
      });
      return;
    }
    
    const container = document.createElement('div');
    container.id = 'toast-container';
    container.className = 'toast-container';
    document.body.appendChild(container);
  }

  /**
   * Показать toast уведомление
   */
  show(message, type = 'info', duration = null, options = {}) {
    const toast = this.createToast(message, type, options);
    this.addToast(toast);
    
    // Автоматически скрываем через указанное время
    const hideDuration = duration || this.defaultDuration;
    setTimeout(() => {
      this.hideToast(toast);
    }, hideDuration);

    return toast;
  }

  /**
   * Создать toast элемент
   */
  createToast(message, type, options = {}) {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    
    // Добавляем иконку в зависимости от типа
    const icon = this.getIconForType(type);
    
    toast.innerHTML = `
      <div class="toast-content">
        <div class="toast-icon">${icon}</div>
        <div class="toast-message">${message}</div>
        <button class="toast-close" onclick="toastSystem.hideToast(this.parentElement.parentElement)">×</button>
      </div>
      <div class="toast-progress"></div>
    `;

    // Добавляем дополнительные классы
    if (options.className) {
      toast.classList.add(options.className);
    }

    // Добавляем анимацию появления
    toast.style.transform = 'translateX(100%)';
    toast.style.opacity = '0';

    return toast;
  }

  /**
   * Получить иконку для типа toast
   */
  getIconForType(type) {
    const icons = {
      success: '✅',
      error: '❌',
      warning: '⚠️',
      info: 'ℹ️',
      loading: '⏳'
    };
    return icons[type] || icons.info;
  }

  /**
   * Добавить toast в контейнер
   */
  addToast(toast) {
    const container = document.getElementById('toast-container');
    container.appendChild(toast);

    // Анимация появления
    setTimeout(() => {
      toast.style.transition = 'transform 0.3s cubic-bezier(0.4, 0, 0.2, 1), opacity 0.3s ease-out';
      toast.style.transform = 'translateX(0)';
      toast.style.opacity = '1';
    }, 100);

    // Запускаем прогресс-бар
    this.startProgressBar(toast);

    // Ограничиваем количество toast
    if (this.toasts.length >= this.maxToasts) {
      const oldestToast = this.toasts.shift();
      this.hideToast(oldestToast);
    }

    this.toasts.push(toast);
  }

  /**
   * Скрыть toast
   */
  hideToast(toast) {
    if (!toast || !toast.parentElement) return;

    // Анимация исчезновения
    toast.style.transform = 'translateX(100%)';
    toast.style.opacity = '0';

    setTimeout(() => {
      if (toast.parentElement) {
        toast.parentElement.removeChild(toast);
      }
      
      // Удаляем из массива
      const index = this.toasts.indexOf(toast);
      if (index > -1) {
        this.toasts.splice(index, 1);
      }
    }, 300);
  }

  /**
   * Запустить прогресс-бар
   */
  startProgressBar(toast) {
    const progressBar = toast.querySelector('.toast-progress');
    if (!progressBar) return;

    progressBar.style.width = '100%';
    progressBar.style.transition = 'width 3s linear';
    
    setTimeout(() => {
      progressBar.style.width = '0%';
    }, 100);
  }

  /**
   * Показать успешное уведомление
   */
  success(message, duration = null, options = {}) {
    return this.show(message, 'success', duration, options);
  }

  /**
   * Показать уведомление об ошибке
   */
  error(message, duration = null, options = {}) {
    return this.show(message, 'error', duration, options);
  }

  /**
   * Показать предупреждение
   */
  warning(message, duration = null, options = {}) {
    return this.show(message, 'warning', duration, options);
  }

  /**
   * Показать информационное уведомление
   */
  info(message, duration = null, options = {}) {
    return this.show(message, 'info', duration, options);
  }

  /**
   * Показать уведомление о загрузке
   */
  loading(message, duration = null, options = {}) {
    return this.show(message, 'loading', duration, options);
  }

  /**
   * Показать уведомление о добавлении в корзину
   */
  cartAdded(dishName, quantity = 1) {
    const message = quantity > 1 
      ? `Добавлено ${quantity} шт. "${dishName}" в корзину`
      : `"${dishName}" добавлено в корзину`;
    
    return this.success(message, 2000);
  }

  /**
   * Показать уведомление об обновлении корзины
   */
  cartUpdated(dishName, quantity) {
    const message = `Количество "${dishName}" обновлено: ${quantity} шт.`;
    return this.info(message, 2000);
  }

  /**
   * Показать уведомление об удалении из корзины
   */
  cartRemoved(dishName) {
    const message = `"${dishName}" удалено из корзины`;
    return this.warning(message, 2000);
  }

  /**
   * Показать уведомление о заказе
   */
  orderPlaced(orderNumber) {
    const message = `Заказ #${orderNumber} успешно оформлен!`;
    return this.success(message, 4000);
  }

  /**
   * Показать уведомление о статусе заказа
   */
  orderStatusChanged(status) {
    const statusMessages = {
      'confirmed': 'Заказ подтвержден',
      'preparing': 'Заказ готовится',
      'ready': 'Заказ готов к выдаче',
      'delivered': 'Заказ доставлен',
      'cancelled': 'Заказ отменен'
    };

    const message = statusMessages[status] || `Статус заказа изменен: ${status}`;
    return this.info(message, 3000);
  }

  /**
   * Показать уведомление о сети
   */
  networkError() {
    return this.error('Ошибка сети. Проверьте подключение к интернету.', 5000);
  }

  /**
   * Показать уведомление о сервере
   */
  serverError() {
    return this.error('Ошибка сервера. Попробуйте позже.', 5000);
  }

  /**
   * Показать уведомление о валидации
   */
  validationError(message) {
    return this.warning(message, 4000);
  }

  /**
   * Показать уведомление о сохранении
   */
  saved(message = 'Изменения сохранены') {
    return this.success(message, 2000);
  }

  /**
   * Показать уведомление о загрузке
   */
  loading(message = 'Загрузка...') {
    return this.show(message, 'loading', null, { className: 'toast-persistent' });
  }

  /**
   * Скрыть все toast уведомления
   */
  hideAll() {
    this.toasts.forEach(toast => {
      this.hideToast(toast);
    });
  }

  /**
   * Очистить все toast уведомления
   */
  clear() {
    const container = document.getElementById('toast-container');
    if (container) {
      container.innerHTML = '';
    }
    this.toasts = [];
  }
}

// Создаем глобальный экземпляр
window.toastSystem = new ToastSystem();