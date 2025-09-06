/**
 * Система плавных переходов между страницами
 * Обеспечивает единообразные анимации для всех переходов в приложении
 */

class PageTransitions {
  constructor() {
    this.isTransitioning = false;
    this.transitionDuration = 300; // мс
    this.init();
  }

  init() {
    // Добавляем класс анимации при загрузке страницы
    document.addEventListener('DOMContentLoaded', () => {
      this.addPageTransitionClass();
    });

    // Перехватываем все клики по ссылкам
    document.addEventListener('click', (e) => {
      this.handleLinkClick(e);
    });

    // Перехватываем программные переходы
    this.interceptLocationChanges();
  }

  addPageTransitionClass() {
    const container = document.querySelector('.container') || document.body;
    container.classList.add('page-transition');
  }

  handleLinkClick(e) {
    const link = e.target.closest('a');
    if (!link || this.isTransitioning) return;

    const href = link.getAttribute('href');
    
    // Игнорируем якорные ссылки и внешние ссылки
    if (!href || href.startsWith('#') || href.startsWith('http') || href.startsWith('tel:') || href.startsWith('mailto:')) {
      return;
    }

    // Игнорируем ссылки с preventDefault
    if (link.onclick && link.onclick.toString().includes('preventDefault')) {
      return;
    }

    e.preventDefault();
    this.navigateToPage(href);
  }

  interceptLocationChanges() {
    // Сохраняем оригинальный метод
    const originalLocationHref = Object.getOwnPropertyDescriptor(Location.prototype, 'href') || 
                                Object.getOwnPropertyDescriptor(HTMLAnchorElement.prototype, 'href');

    // Перехватываем изменения location.href
    let currentHref = location.href;
    
    setInterval(() => {
      if (location.href !== currentHref && !this.isTransitioning) {
        currentHref = location.href;
        this.addPageTransitionClass();
      }
    }, 100);
  }

  navigateToPage(url) {
    if (this.isTransitioning) return;
    
    this.isTransitioning = true;
    
    // Добавляем класс выхода
    const container = document.querySelector('.container') || document.body;
    container.classList.add('page-transition-out');
    
    // Ждем завершения анимации выхода
    setTimeout(() => {
      // Переходим на новую страницу
      location.href = url;
    }, 200);
  }

  // Метод для программного перехода с анимацией
  static navigate(url) {
    const transitions = new PageTransitions();
    transitions.navigateToPage(url);
  }

  // Метод для добавления анимации к кнопкам
  static addButtonAnimation(button) {
    if (!button) return;
    
    button.addEventListener('click', (e) => {
      button.classList.add('button-press');
      setTimeout(() => {
        button.classList.remove('button-press');
      }, 150);
    });

    button.addEventListener('mouseenter', () => {
      button.classList.add('button-hover');
    });

    button.addEventListener('mouseleave', () => {
      button.classList.remove('button-hover');
    });
  }

  // Метод для добавления анимации к карточкам
  static addCardAnimation(card) {
    if (!card) return;
    
    // Добавляем анимацию появления
    card.classList.add('card-appear');
    
    // Добавляем hover эффекты
    card.addEventListener('mouseenter', () => {
      card.style.transform = 'translateY(-2px)';
      card.style.boxShadow = '0 4px 12px rgba(0,0,0,0.1)';
    });

    card.addEventListener('mouseleave', () => {
      card.style.transform = 'translateY(0)';
      card.style.boxShadow = '';
    });
  }

  // Метод для анимации модальных окон
  static showModal(modal) {
    if (!modal) return;
    
    modal.style.display = 'block';
    modal.classList.add('modal-slide-in');
    
    // Убираем класс анимации после завершения
    setTimeout(() => {
      modal.classList.remove('modal-slide-in');
    }, 300);
  }

  static hideModal(modal) {
    if (!modal) return;
    
    modal.classList.add('page-fade-out');
    
    setTimeout(() => {
      modal.style.display = 'none';
      modal.classList.remove('page-fade-out');
    }, 200);
  }

  // Метод для анимации уведомлений
  static showNotification(element) {
    if (!element) return;
    
    element.classList.add('notification-slide-in');
    
    setTimeout(() => {
      element.classList.remove('notification-slide-in');
    }, 400);
  }

  // Метод для анимации загрузки
  static showLoading(element) {
    if (!element) return;
    
    element.classList.add('loading-pulse');
  }

  static hideLoading(element) {
    if (!element) return;
    
    element.classList.remove('loading-pulse');
  }
}

// Инициализируем систему переходов
document.addEventListener('DOMContentLoaded', () => {
  new PageTransitions();
  
  // Добавляем анимации ко всем кнопкам
  document.querySelectorAll('button').forEach(button => {
    PageTransitions.addButtonAnimation(button);
  });
  
  // Добавляем анимации ко всем карточкам
  document.querySelectorAll('.card, .mini-card, .restaurant-card').forEach(card => {
    PageTransitions.addCardAnimation(card);
  });
  
  // Добавляем анимации к навигационным элементам
  document.querySelectorAll('.nav-item').forEach(navItem => {
    navItem.addEventListener('click', (e) => {
      navItem.classList.add('button-press');
      setTimeout(() => {
        navItem.classList.remove('button-press');
      }, 150);
    });
  });
});

// Экспортируем для использования в других скриптах
window.PageTransitions = PageTransitions;