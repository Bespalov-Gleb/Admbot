/**
 * Универсальный обработчик клавиатуры для iOS
 * Решает проблему наложения клавиатуры на контент (особенно на iPhone 13)
 */

(function() {
  'use strict';
  
  // Проверяем, что мы на мобильном устройстве
  const isMobile = /iPhone|iPad|iPod|Android/i.test(navigator.userAgent);
  const isIOS = /iPhone|iPad|iPod/i.test(navigator.userAgent);
  
  if (!isMobile) {
    return; // Не применяем на десктопе
  }
  
  // Функция для обработки изменения viewport при появлении клавиатуры
  function handleKeyboard() {
    if (window.visualViewport) {
      // Используем Visual Viewport API (современные браузеры)
      let lastViewportHeight = window.visualViewport.height;
      
      window.visualViewport.addEventListener('resize', () => {
        const currentHeight = window.visualViewport.height;
        const heightDiff = lastViewportHeight - currentHeight;
        
        // Если viewport уменьшился (появилась клавиатура)
        if (heightDiff > 150) {
          // Находим активный input
          const activeElement = document.activeElement;
          if (activeElement && (activeElement.tagName === 'INPUT' || activeElement.tagName === 'TEXTAREA')) {
            // Прокручиваем к активному элементу с задержкой
            setTimeout(() => {
              activeElement.scrollIntoView({
                behavior: 'smooth',
                block: 'center',
                inline: 'nearest'
              });
            }, 100);
          }
        }
        
        lastViewportHeight = currentHeight;
      });
    } else {
      // Fallback для старых браузеров - отслеживаем изменение высоты окна
      let lastWindowHeight = window.innerHeight;
      
      window.addEventListener('resize', () => {
        const currentHeight = window.innerHeight;
        const heightDiff = lastWindowHeight - currentHeight;
        
        // Если высота окна уменьшилась (появилась клавиатура)
        if (heightDiff > 150) {
          const activeElement = document.activeElement;
          if (activeElement && (activeElement.tagName === 'INPUT' || activeElement.tagName === 'TEXTAREA')) {
            setTimeout(() => {
              activeElement.scrollIntoView({
                behavior: 'smooth',
                block: 'center',
                inline: 'nearest'
              });
            }, 300);
          }
        }
        
        lastWindowHeight = currentHeight;
      });
    }
  }
  
  // Функция для автоматического scrollIntoView при фокусе на input
  function handleInputFocus() {
    document.addEventListener('focusin', (e) => {
      const target = e.target;
      if (target && (target.tagName === 'INPUT' || target.tagName === 'TEXTAREA')) {
        // Задержка для появления клавиатуры на iOS
        setTimeout(() => {
          target.scrollIntoView({
            behavior: 'smooth',
            block: 'center',
            inline: 'nearest'
          });
        }, isIOS ? 300 : 100);
      }
    }, true);
  }
  
  // Инициализация при загрузке DOM
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
      handleKeyboard();
      handleInputFocus();
    });
  } else {
    handleKeyboard();
    handleInputFocus();
  }
})();

