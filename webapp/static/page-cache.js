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
                const finalDelay = isRestaurantPage ? 800 : 400; // Для ресторанов больше времени
                
                // Ждем загрузки контента
                this.waitForContent().then(() => {
                    console.log(`Content loaded, scrolling to ${scrollY}px`);
                    
                    // Восстанавливаем позицию ОДИН раз
                    window.scrollTo(0, scrollY);
                    console.log(`Restored scroll position for ${pageName}: ${scrollY}`);
                    
                    // Дополнительно восстанавливаем позицию после загрузки контента
                    setTimeout(() => {
                        const currentScroll = window.pageYOffset || document.documentElement.scrollTop;
                        if (Math.abs(currentScroll - scrollY) > 50) {
                            console.log(`Position changed after content load from ${scrollY} to ${currentScroll}, restoring again`);
                            window.scrollTo(0, scrollY);
                        }
                    }, isRestaurantPage ? 400 : 200); // Для ресторанов больше времени
                    
                    // Еще одна проверка (для страниц блюд и ресторанов)
                    setTimeout(() => {
                        const currentScroll = window.pageYOffset || document.documentElement.scrollTop;
                        if (Math.abs(currentScroll - scrollY) > 50) {
                            console.log(`Final position check: ${scrollY} vs ${currentScroll}, final restore`);
                            window.scrollTo(0, scrollY);
                        }
                        
                        // Дополнительная проверка для ресторанов
                        if (isRestaurantPage) {
                            setTimeout(() => {
                                const finalScroll = window.pageYOffset || document.documentElement.scrollTop;
                                if (Math.abs(finalScroll - scrollY) > 50) {
                                    console.log(`Extra restaurant check: ${scrollY} vs ${finalScroll}, final restore`);
                                    window.scrollTo(0, scrollY);
                                }
                            }, 200);
                            
                            // Еще одна проверка через 600мс (после загрузки меню)
                            setTimeout(() => {
                                const finalScroll = window.pageYOffset || document.documentElement.scrollTop;
                                if (Math.abs(finalScroll - scrollY) > 50) {
                                    console.log(`Post-menu restaurant check: ${scrollY} vs ${finalScroll}, final restore`);
                                    window.scrollTo(0, scrollY);
                                }
                            }, 600);
                        }
                        
                        // ПОКАЗЫВАЕМ СТРАНИЦУ после финальной проверки
                        showPageAfterReady();
                        console.log(`Page shown after final scroll restoration for ${pageName} (delay: ${finalDelay}ms)`);
                    }, finalDelay);
                    
                    // Снимаем флаг через разное время для разных страниц
                    const protectionTime = isRestaurantPage ? 4000 : 2000; // Для ресторанов больше времени
                    setTimeout(() => {
                        this.isRestoringPosition = false;
                        console.log(`Restoration protection disabled for ${pageName} (after ${protectionTime}ms)`);
                    }, protectionTime);
                });
            } else {
                console.log(`Saved scroll position is 0 or invalid for ${pageName}`);
                // Показываем страницу, если позиция 0 или невалидна
                showPageAfterReady();
            }
        } else {
            console.log(`No saved scroll position found for ${pageName}`);
            // Показываем страницу, если нет сохраненной позиции
            showPageAfterReady();
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
                    // Минимальная задержка для завершения рендеринга
                    setTimeout(resolve, 50);
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

// Скрываем страницу до полного восстановления позиции
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
}

function showPageAfterReady() {
    const overlay = document.getElementById('scroll-restore-overlay');
    if (overlay) {
        overlay.remove();
    }
}

// Восстанавливаем позицию при загрузке страницы
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        console.log('DOM loaded, hiding page until scroll restored...');
        hidePageUntilReady();
        // Ждем загрузки контента перед восстановлением
        const currentPage = window.pageCache.getPageName();
        const isRestaurantPage = currentPage.startsWith('restaurant_');
        const initialDelay = isRestaurantPage ? 200 : 100; // Для ресторанов больше времени
        
        setTimeout(() => {
            window.pageCache.restoreScrollPosition();
        }, initialDelay);
        
        // Таймаут на случай, если что-то пошло не так
        const fallbackTimeout = isRestaurantPage ? 3000 : 1500; // Для ресторанов больше времени
        
        setTimeout(() => {
            showPageAfterReady();
            console.log(`Fallback: Page shown after timeout (${fallbackTimeout}ms)`);
        }, fallbackTimeout);
    });
} else {
    console.log('DOM already loaded, hiding page until scroll restored...');
    hidePageUntilReady();
    // Ждем загрузки контента перед восстановлением
    const currentPage = window.pageCache.getPageName();
    const isRestaurantPage = currentPage.startsWith('restaurant_');
    const initialDelay = isRestaurantPage ? 200 : 100; // Для ресторанов больше времени
    
    setTimeout(() => {
        window.pageCache.restoreScrollPosition();
    }, initialDelay);
    
    // Таймаут на случай, если что-то пошло не так
    const fallbackTimeout = isRestaurantPage ? 3000 : 1500; // Для ресторанов больше времени
    
    setTimeout(() => {
        showPageAfterReady();
        console.log(`Fallback: Page shown after timeout (${fallbackTimeout}ms)`);
    }, fallbackTimeout);
}