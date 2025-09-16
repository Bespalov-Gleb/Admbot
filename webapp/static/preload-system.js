/**
 * Система предзагрузки контента
 * Обеспечивает мгновенную загрузку популярных страниц и данных
 */

class PreloadSystem {
  constructor() {
    this.cache = new Map();
    this.preloadQueue = [];
    this.isPreloading = false;
    this.init();
  }

  init() {
    // Предзагружаем контент после загрузки страницы
    document.addEventListener('DOMContentLoaded', () => {
      this.startPreloading();
    });

    // Предзагружаем при hover на ссылки
    this.setupHoverPreloading();
  }

  /**
   * Начать предзагрузку
   */
  startPreloading() {
    // Предзагружаем через 1 секунду после загрузки страницы
    setTimeout(() => {
      this.preloadPopularPages();
      this.preloadCriticalData();
    }, 1000);
  }

  /**
   * Предзагрузить популярные страницы
   */
  preloadPopularPages() {
    const popularPages = [
      '/static/cart.html',
      '/static/profile.html',
      '/static/checkout.html',
      '/static/dish.html'
    ];

    popularPages.forEach(page => {
      this.preloadPage(page);
    });
  }

  /**
   * Предзагрузить критически важные данные
   */
  preloadCriticalData() {
    // Предзагружаем данные корзины
    this.preloadCartData();
    
    // Предзагружаем данные пользователя
    this.preloadUserData();
    
    // Предзагружаем популярные рестораны
    this.preloadRestaurantsData();
  }

  /**
   * Предзагрузить страницу
   */
  async preloadPage(url) {
    if (this.cache.has(url)) {
      return Promise.resolve();
    }

    try {
      const response = await fetch(url, { 
        method: 'GET',
        cache: 'force-cache'
      });
      
      if (response.ok) {
        const content = await response.text();
        this.cache.set(url, content);
        console.log(`Preloaded page: ${url}`);
        return Promise.resolve();
      }
    } catch (error) {
      console.debug('Preload failed for:', url, error.message);
    }
    
    // Не возвращаем reject - просто игнорируем ошибки
    return Promise.resolve();
  }

  /**
   * Предзагрузить данные корзины
   */
  async preloadCartData() {
    try {
      // Проверяем, что api определена
      if (typeof api === 'undefined') {
        console.debug('API not defined, skipping cart preload');
        return;
      }
      
      const response = await fetch(api + '/cart' + (uid ? ('?uid=' + uid) : ''), {
        headers: { 'X-Telegram-User-Id': String(uid) }
      });
      
      if (response.ok) {
        const cartData = await response.json();
        this.cache.set('cart_data', cartData);
        console.log('Preloaded cart data');
      }
    } catch (error) {
      console.warn('Failed to preload cart data:', error);
    }
  }

  /**
   * Предзагрузить данные пользователя
   */
  async preloadUserData() {
    try {
      // Проверяем, что api определена
      if (typeof api === 'undefined') {
        console.debug('API not defined, skipping user preload');
        return;
      }
      
      const response = await fetch(api + '/users/me', {
        headers: { 'X-Telegram-User-Id': String(uid) }
      });
      
      if (response.ok) {
        const userData = await response.json();
        this.cache.set('user_data', userData);
        console.log('Preloaded user data');
      }
    } catch (error) {
      console.warn('Failed to preload user data:', error);
    }
  }

  /**
   * Предзагрузить данные ресторанов
   */
  async preloadRestaurantsData() {
    try {
      // Проверяем, что api определена
      if (typeof api === 'undefined') {
        console.debug('API not defined, skipping restaurants preload');
        return;
      }
      
      const response = await fetch(api + '/restaurants');
      
      if (response.ok) {
        const restaurantsData = await response.json();
        this.cache.set('restaurants_data', restaurantsData);
        console.log('Preloaded restaurants data');
      }
    } catch (error) {
      console.warn('Failed to preload restaurants data:', error);
    }
  }

  /**
   * Настроить предзагрузку при hover
   */
  setupHoverPreloading() {
    document.addEventListener('mouseover', (e) => {
      const link = e.target.closest('a');
      if (!link) return;

      const href = link.getAttribute('href');
      if (!href || href.startsWith('#') || href.startsWith('http') || href.startsWith('tel:') || href.startsWith('mailto:')) {
        return;
      }

      // Предзагружаем при hover с задержкой
      clearTimeout(link.preloadTimeout);
      link.preloadTimeout = setTimeout(() => {
        this.preloadPage(href);
      }, 300);
    });

    document.addEventListener('mouseout', (e) => {
      const link = e.target.closest('a');
      if (!link) return;

      clearTimeout(link.preloadTimeout);
    });
  }

  /**
   * Получить предзагруженные данные
   */
  getCachedData(key) {
    return this.cache.get(key);
  }

  /**
   * Проверить, есть ли данные в кэше
   */
  hasCachedData(key) {
    return this.cache.has(key);
  }

  /**
   * Очистить кэш
   */
  clearCache() {
    this.cache.clear();
  }

  /**
   * Получить статистику кэша
   */
  getCacheStats() {
    return {
      size: this.cache.size,
      keys: Array.from(this.cache.keys())
    };
  }
}

// Создаем глобальный экземпляр
window.preloadSystem = new PreloadSystem();