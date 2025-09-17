/**
 * Система кэширования страниц в localStorage
 * Страницы сохраняются и открываются мгновенно из кэша
 */

class PageCache {
    constructor() {
        this.cacheKey = 'page_cache';
        this.cacheExpiry = 24 * 60 * 60 * 1000; // 24 часа
        this.maxCacheSize = 10; // Максимум 10 страниц в кэше
        this.isRestoringPosition = false; // Флаг восстановления позиции
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
        
        // Восстанавливаем позицию скролла
        this.restoreScrollPosition();
    }
    
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
    
    /**
     * Восстановить позицию скролла
     */
    restoreScrollPosition() {
        const pageName = this.getPageName();
        
        // НЕ восстанавливаем позицию для страниц блюд
        if (pageName === 'dish') {
            console.log(`Skipping scroll restoration for dish page`);
            showPageAfterReady();
            return;
        }
        
        const savedScroll = sessionStorage.getItem(`scroll_${pageName}`);
        
        console.log(`Attempting to restore scroll for ${pageName}:`, {
            savedScroll,
            scrollY: savedScroll ? parseInt(savedScroll, 10) : null,
            hasContent: !!(document.querySelector('.container') || document.querySelector('#restaurants') || document.querySelector('#selections'))
        });
        
        if (savedScroll) {
            const scrollY = parseInt(savedScroll, 10);
            if (scrollY > 0) {
                console.log(`Found saved scroll position: ${scrollY}px for ${pageName}`);
                
                // Устанавливаем флаг, что мы восстанавливаем позицию
                this.isRestoringPosition = true;
                
                // Определяем тип страницы для разной задержки
                const isRestaurantPage = pageName.startsWith('restaurant_');
                const finalDelay = isRestaurantPage ? 800 : 500; // Увеличили задержки для надежности
                
                // Ждем загрузки контента
                this.waitForContent().then(() => {
                    console.log(`Content loaded, scrolling to ${scrollY}px`);
                    
                    // Простое восстановление позиции без сложной логики
                    window.scrollTo(0, scrollY);
                    console.log(`Restored scroll position for ${pageName}: ${scrollY}`);
                    
                    // Контент загружается из index.html с задержкой
                    
                    // Снимаем флаг через короткое время
                    setTimeout(() => {
                        this.isRestoringPosition = false;
                        console.log(`Restoration protection disabled for ${pageName}`);
                    }, 1000);
                });
            } else {
                console.log(`Saved scroll position is 0 or invalid for ${pageName}`);
                // Контент загружается из index.html с задержкой
            }
        } else {
            console.log(`No saved scroll position found for ${pageName}`);
            // Контент загружается из index.html с задержкой
        }
    }
    
    /**
     * Ждать загрузки контента
     */
    waitForContent() {
        return new Promise((resolve) => {
            let attempts = 0;
            const maxAttempts = 20; // Максимум 1 секунда
            
            const checkContent = () => {
                attempts++;
                
                // Проверяем наличие основного контента
                const hasContent = document.querySelector('.container') || 
                                 document.querySelector('#restaurants') || 
                                 document.querySelector('#selections') ||
                                 document.querySelector('.menu-container') ||
                                 document.querySelector('.dish-container') ||
                                 document.querySelector('.restaurant-container') ||
                                 document.querySelector('main') ||
                                 document.querySelector('body > div');
                
                // Для страниц блюд проверяем наличие изображений или текста
                const hasDishContent = document.querySelector('img') || 
                                     document.querySelector('h1') || 
                                     document.querySelector('h2') ||
                                     document.querySelector('.dish-info') ||
                                     document.querySelector('.restaurant-info');
                
                if (hasContent || hasDishContent) {
                    // Увеличили задержку для завершения рендеринга
                    setTimeout(resolve, 150);
                } else if (attempts >= maxAttempts) {
                    // Таймаут - восстанавливаем позицию в любом случае
                    console.warn('Content loading timeout, proceeding anyway');
                    resolve();
                } else {
                    setTimeout(checkContent, 50);
                }
            };
            
            checkContent();
        });
    }
    
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

// Перехватываем клики по ссылкам
document.addEventListener('click', function(e) {
    const link = e.target.closest('a');
    if (!link || !link.href) return;
    
    // Проверяем, что это внутренняя ссылка
    if (link.href.startsWith(location.origin + '/static/')) {
        e.preventDefault();
        
        // Сохраняем текущую позицию скролла
        const pageName = window.pageCache.getPageName();
        
        // НЕ сохраняем позицию для страниц блюд
        if (pageName !== 'dish') {
            const scrollY = window.pageYOffset || document.documentElement.scrollTop;
            sessionStorage.setItem(`scroll_${pageName}`, scrollY.toString());
            console.log(`Saved scroll position for ${pageName}: ${scrollY}px`);
            console.log(`All saved positions:`, Object.keys(sessionStorage).filter(key => key.startsWith('scroll_')).map(key => `${key}: ${sessionStorage.getItem(key)}`));
        } else {
            console.log(`Skipping scroll position save for dish page`);
        }
        
        // Навигируем с кэшированием
        window.pageCache.navigateToPage(link.href);
    }
});

// Сохраняем позицию при скролле
let pageCacheScrollTimeout;
window.addEventListener('scroll', function() {
    clearTimeout(pageCacheScrollTimeout);
    pageCacheScrollTimeout = setTimeout(() => {
        // Не сохраняем позицию, если мы восстанавливаем позицию
        if (window.pageCache.isRestoringPosition) {
            console.log('Skipping auto-save during position restoration');
            return;
        }
        
        const pageName = window.pageCache.getPageName();
        
        // НЕ сохраняем позицию для страниц блюд
        if (pageName === 'dish') {
            return;
        }
        
        const scrollY = window.pageYOffset || document.documentElement.scrollTop;
        sessionStorage.setItem(`scroll_${pageName}`, scrollY.toString());
        console.log(`Auto-saved scroll position for ${pageName}: ${scrollY}px`);
    }, 100);
});

// Обработка кнопки "Назад"
window.addEventListener('popstate', function(e) {
    // При нажатии "Назад" восстанавливаем позицию
    setTimeout(() => {
        window.pageCache.restoreScrollPosition();
    }, 100);
});

console.log('Page cache system initialized');

// Отладочная информация
console.log('Current page:', window.pageCache.getPageName());
console.log('Saved scroll positions:', Object.keys(sessionStorage).filter(key => key.startsWith('scroll_')));

// Отладочные перехватчики убраны - проблема найдена и исправлена

// Создаем overlay для скрытия страницы до полной загрузки
function hidePageUntilReady() {
    // Создаем overlay для скрытия страницы
    const overlay = document.createElement('div');
    overlay.id = 'scroll-restore-overlay';
    overlay.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: white;
        z-index: 9999;
        display: flex;
        align-items: center;
        justify-content: center;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    `;
    overlay.innerHTML = `
        <div style="text-align: center; color: #666;">
            <div style="width: 20px; height: 20px; border: 2px solid #f3f3f3; border-top: 2px solid #3498db; border-radius: 50%; animation: spin 1s linear infinite; margin: 0 auto 10px;"></div>
            <div>Загрузка...</div>
        </div>
        <style>
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
        </style>
    `;
    document.body.appendChild(overlay);
    console.log('Overlay created - page hidden until ready');
}

function showPageAfterReady() {
    const overlay = document.getElementById('scroll-restore-overlay');
    if (overlay) {
        overlay.remove();
        console.log('Overlay removed - page is now visible');
    }
}

// Восстановление позиции теперь управляется из index.html
// Автоматическое восстановление отключено
console.log('Page cache system initialized - scroll restoration controlled by index.html');