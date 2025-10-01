/**
 * Система кэширования страниц в localStorage
 * Страницы сохраняются и открываются мгновенно из кэша
 */

// Глобальный флаг: сохранять/восстанавливать скролл (отключено)
const ENABLE_SCROLL_PERSIST = false;

class PageCache {
    constructor() {
        this.cacheKey = 'page_cache';
        this.cacheExpiry = 24 * 60 * 60 * 1000; // 24 часа
        this.maxCacheSize = 10; // Максимум 10 страниц в кэше
        this.isRestoringPosition = false; // ранее использовался для скролла, больше не нужен
    }
    
    /**
     * Получить кэш страниц
     */
    getCache() {
        try {
            const cached = localStorage.getItem(this.cacheKey);
            return cached ? JSON.parse(cached) : {};
        } catch (error) {
            console.warn('Failed to get page cache:', error);
            return {};
        }
    }
    
    /**
     * Сохранить кэш страниц
     */
    setCache(cache) {
        try {
            localStorage.setItem(this.cacheKey, JSON.stringify(cache));
        } catch (error) {
            console.warn('Failed to save page cache:', error);
        }
    }
    
    /**
     * Получить кэшированную страницу
     */
    getCachedPage(url) {
        const cache = this.getCache();
        const cached = cache[url];
        
        if (!cached) return null;
        
        // Проверяем срок действия
        if (Date.now() - cached.timestamp > this.cacheExpiry) {
            delete cache[url];
            this.setCache(cache);
            return null;
        }
        
        return cached.content;
    }
    
    /**
     * Сохранить страницу в кэш
     */
    cachePage(url, content) {
        const cache = this.getCache();
        
        // Ограничиваем размер кэша
        const urls = Object.keys(cache);
        if (urls.length >= this.maxCacheSize) {
            // Удаляем самую старую страницу
            const oldestUrl = urls.reduce((oldest, current) => 
                cache[current].timestamp < cache[oldest].timestamp ? current : oldest
            );
            delete cache[oldestUrl];
        }
        
        cache[url] = {
            content: content,
            timestamp: Date.now()
        };
        
        this.setCache(cache);
        console.log(`Cached page: ${url}`);
    }
    
    /**
     * Загрузить и кэшировать страницу
     */
    async loadAndCachePage(url) {
        try {
            const response = await fetch(url);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            const content = await response.text();
            this.cachePage(url, content);
            return content;
        } catch (error) {
            console.warn(`Failed to load page ${url}:`, error);
            throw error;
        }
    }
    
    /**
     * Навигация с кэшированием
     */
    async navigateToPage(url) {
        // Проверяем кэш
        const cachedContent = this.getCachedPage(url);
        
        if (cachedContent) {
            // Страница есть в кэше - показываем мгновенно
            console.log(`Loading from cache: ${url}`);
            this.showCachedPage(cachedContent);
            return;
        }
        
        // Страницы нет в кэше - загружаем
        console.log(`Loading from server: ${url}`);
        try {
            const content = await this.loadAndCachePage(url);
            this.showCachedPage(content);
        } catch (error) {
            // Fallback к обычной навигации
            console.warn('Cache failed, using normal navigation:', error);
            location.href = url;
        }
    }
    
    /**
     * Показать кэшированную страницу
     */
  showCachedPage(content) {
        // Создаем новый документ из кэшированного контента
        const parser = new DOMParser();
        const doc = parser.parseFromString(content, 'text/html');
        
        // Заменяем содержимое страницы
        document.documentElement.innerHTML = doc.documentElement.innerHTML;
        
        // Обновляем URL без перезагрузки
        history.pushState(null, '', location.href);
        
        // Запускаем скрипты на новой странице
    this.executeScripts();
    // Удаляем возможный overlay восстановления (наследие)
    try { const ov = document.getElementById('scroll-restore-overlay'); if (ov) ov.remove(); } catch(_){}}
    
    /**
     * Выполнить скрипты на новой странице
     */
    executeScripts() {
        const scripts = document.querySelectorAll('script');
        scripts.forEach(script => {
            if (script.src) {
                // Внешние скрипты - загружаем заново
                const newScript = document.createElement('script');
                newScript.src = script.src;
                document.head.appendChild(newScript);
            } else {
                // Встроенные скрипты - выполняем
                try {
                    eval(script.textContent);
                } catch (error) {
                    console.warn('Script execution failed:', error);
                }
            }
        });
    }
    
    // Методы восстановления скролла и ожидания контента удалены как неиспользуемые
    
    /**
     * Получить имя текущей страницы
     */
    getPageName() {
        const path = location.pathname;
        if (path.includes('index.html')) return 'home';
        if (path.includes('restaurant.html')) {
            const urlParams = new URLSearchParams(location.search);
            const restaurantId = urlParams.get('id');
            return restaurantId ? `restaurant_${restaurantId}` : 'restaurant';
        }
        if (path.includes('cart.html')) return 'cart';
        if (path.includes('profile.html')) return 'profile';
        if (path.includes('order.html')) return 'order';
        if (path.includes('checkout.html')) return 'checkout';
        if (path.includes('dish.html')) return 'dish';
        return 'unknown';
    }
    
    /**
     * Очистить кэш
     */
    clearCache() {
        localStorage.removeItem(this.cacheKey);
        console.log('Page cache cleared');
    }
}

// Создаем глобальный экземпляр
window.pageCache = new PageCache();

console.log('Page cache system initialized (scroll persistence removed)');