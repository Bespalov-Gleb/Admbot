/**
 * Инициализация Telegram WebApp API
 * Отключает закрытие приложения при скролле вниз вверху страницы
 */
(function() {
  'use strict';
  
  // Добавляем CSS для предотвращения закрытия при скролле
  const style = document.createElement('style');
  style.textContent = `
    body {
      overscroll-behavior-y: none;
      overscroll-behavior: none;
    }
    html {
      overscroll-behavior-y: none;
      overscroll-behavior: none;
    }
  `;
  document.head.appendChild(style);
  
  // Проверяем, что мы в Telegram WebApp
  if (typeof window.Telegram !== 'undefined' && window.Telegram.WebApp) {
    const tg = window.Telegram.WebApp;
    
    // Расширяем приложение на весь экран
    if (typeof tg.expand === 'function') {
      tg.expand();
    }
    
    // Отключаем вертикальные свайпы (pull-to-close)
    // Это предотвращает закрытие приложения при скролле вниз вверху страницы
    if (typeof tg.disableVerticalSwipes === 'function') {
      tg.disableVerticalSwipes();
    }
    
    // Включаем подтверждение перед закрытием (опционально)
    // Это добавит дополнительную защиту от случайного закрытия
    if (typeof tg.enableClosingConfirmation === 'function') {
      tg.enableClosingConfirmation();
    }
    
    // Устанавливаем цвет фона для лучшей интеграции
    if (typeof tg.setHeaderColor === 'function') {
      tg.setHeaderColor('#ffffff');
    }
    
    // Устанавливаем цвет фона для кнопки "Назад"
    if (typeof tg.setBackgroundColor === 'function') {
      tg.setBackgroundColor('#ffffff');
    }
    
    console.log('Telegram WebApp initialized: vertical swipes disabled');
  }
})();

