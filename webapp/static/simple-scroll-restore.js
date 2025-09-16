/**
 * Простая система восстановления позиции скролла
 * Основана на лучших практиках из интернета
 */

(function() {
    'use strict';
    
    // Получаем имя текущей страницы
    function getPageName() {
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
    
    // Сохраняем позицию скролла
    function saveScrollPosition() {
        const scrollY = window.pageYOffset || document.documentElement.scrollTop;
        const pageName = getPageName();
        sessionStorage.setItem(`scroll_${pageName}`, scrollY.toString());
    }
    
    // Восстанавливаем позицию скролла
    function restoreScrollPosition() {
        const pageName = getPageName();
        const savedScroll = sessionStorage.getItem(`scroll_${pageName}`);
        
        if (savedScroll) {
            const scrollY = parseInt(savedScroll, 10);
            if (scrollY > 0) {
                // Устанавливаем позицию сразу, без анимации
                window.scrollTo(0, scrollY);
            }
        }
    }
    
    // Инициализация
    function init() {
        // Проверяем, есть ли система кэширования страниц
        if (window.pageCache) {
            console.log('Page cache system detected, scroll restore disabled');
            return;
        }
        
        // Восстанавливаем позицию при загрузке страницы
        restoreScrollPosition();
        
        // Сохраняем позицию при скролле (с debounce)
        let scrollTimeout;
        window.addEventListener('scroll', function() {
            clearTimeout(scrollTimeout);
            scrollTimeout = setTimeout(saveScrollPosition, 100);
        });
        
        // Сохраняем позицию при уходе со страницы
        window.addEventListener('beforeunload', saveScrollPosition);
    }
    
    // Запускаем инициализацию
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
    
})();