/**
 * Система микроанимаций
 * Обеспечивает плавные и отзывчивые анимации для всех интерактивных элементов
 */

class MicroAnimations {
  constructor() {
    this.animationQueue = [];
    this.isAnimating = false;
    this.init();
  }

  init() {
    // Инициализируем анимации при загрузке страницы
    document.addEventListener('DOMContentLoaded', () => {
      this.setupButtonAnimations();
      this.setupCardAnimations();
      this.setupInputAnimations();
      this.setupScrollAnimations();
      this.setupHoverEffects();
    });
  }

  /**
   * Настроить анимации кнопок
   */
  setupButtonAnimations() {
    // Добавляем анимации для всех кнопок
    const buttons = document.querySelectorAll('button, .btn, .button, [role="button"]');
    
    buttons.forEach(button => {
      // Анимация нажатия
      button.addEventListener('mousedown', (e) => {
        this.animateButtonPress(button);
      });

      // Анимация отпускания
      button.addEventListener('mouseup', (e) => {
        this.animateButtonRelease(button);
      });

      // Анимация hover
      button.addEventListener('mouseenter', (e) => {
        this.animateButtonHover(button);
      });

      button.addEventListener('mouseleave', (e) => {
        this.animateButtonLeave(button);
      });
    });
  }

  /**
   * Анимация нажатия кнопки
   */
  animateButtonPress(button) {
    button.style.transform = 'scale(0.95)';
    button.style.transition = 'transform 0.1s ease-out';
    
    // Добавляем эффект "ripple"
    this.createRippleEffect(button);
  }

  /**
   * Анимация отпускания кнопки
   */
  animateButtonRelease(button) {
    button.style.transform = 'scale(1)';
    button.style.transition = 'transform 0.2s ease-out';
  }

  /**
   * Анимация hover кнопки
   */
  animateButtonHover(button) {
    button.style.transform = 'translateY(-2px) scale(1.02)';
    button.style.transition = 'transform 0.2s ease-out';
    button.style.boxShadow = '0 4px 12px rgba(0, 0, 0, 0.15)';
  }

  /**
   * Анимация ухода с кнопки
   */
  animateButtonLeave(button) {
    button.style.transform = 'translateY(0) scale(1)';
    button.style.transition = 'transform 0.2s ease-out';
    button.style.boxShadow = '';
  }

  /**
   * Создать эффект ripple
   */
  createRippleEffect(button) {
    const ripple = document.createElement('span');
    ripple.className = 'ripple-effect';
    
    const rect = button.getBoundingClientRect();
    const size = Math.max(rect.width, rect.height);
    const x = rect.width / 2;
    const y = rect.height / 2;
    
    ripple.style.width = ripple.style.height = size + 'px';
    ripple.style.left = (x - size / 2) + 'px';
    ripple.style.top = (y - size / 2) + 'px';
    
    button.style.position = 'relative';
    button.style.overflow = 'hidden';
    button.appendChild(ripple);
    
    // Удаляем ripple через анимацию
    setTimeout(() => {
      ripple.remove();
    }, 600);
  }

  /**
   * Настроить анимации карточек
   */
  setupCardAnimations() {
    const cards = document.querySelectorAll('.card, .mini-card, .restaurant-card, .dish-card');
    
    cards.forEach((card, index) => {
      // Анимация появления с задержкой
      card.style.opacity = '0';
      card.style.transform = 'translateY(20px)';
      
      setTimeout(() => {
        card.style.transition = 'opacity 0.5s ease-out, transform 0.5s ease-out';
        card.style.opacity = '1';
        card.style.transform = 'translateY(0)';
      }, index * 100);

      // Анимация hover
      card.addEventListener('mouseenter', () => {
        this.animateCardHover(card);
      });

      card.addEventListener('mouseleave', () => {
        this.animateCardLeave(card);
      });
    });
  }

  /**
   * Анимация hover карточки
   */
  animateCardHover(card) {
    card.style.transform = 'translateY(-8px) scale(1.02)';
    card.style.transition = 'transform 0.3s cubic-bezier(0.4, 0, 0.2, 1)';
    card.style.boxShadow = '0 12px 24px rgba(0, 0, 0, 0.15)';
  }

  /**
   * Анимация ухода с карточки
   */
  animateCardLeave(card) {
    card.style.transform = 'translateY(0) scale(1)';
    card.style.transition = 'transform 0.3s cubic-bezier(0.4, 0, 0.2, 1)';
    card.style.boxShadow = '';
  }

  /**
   * Настроить анимации полей ввода
   */
  setupInputAnimations() {
    const inputs = document.querySelectorAll('input, textarea, select');
    
    inputs.forEach(input => {
      // Анимация фокуса
      input.addEventListener('focus', () => {
        this.animateInputFocus(input);
      });

      input.addEventListener('blur', () => {
        this.animateInputBlur(input);
      });
    });
  }

  /**
   * Анимация фокуса поля ввода
   */
  animateInputFocus(input) {
    input.style.transform = 'scale(1.02)';
    input.style.transition = 'transform 0.2s ease-out';
    input.style.boxShadow = '0 0 0 3px rgba(25, 118, 210, 0.1)';
  }

  /**
   * Анимация потери фокуса поля ввода
   */
  animateInputBlur(input) {
    input.style.transform = 'scale(1)';
    input.style.transition = 'transform 0.2s ease-out';
    input.style.boxShadow = '';
  }

  /**
   * Настроить анимации скролла
   */
  setupScrollAnimations() {
    // Анимация появления элементов при скролле
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          this.animateElementAppear(entry.target);
        }
      });
    }, {
      threshold: 0.1,
      rootMargin: '0px 0px -50px 0px'
    });

    // Наблюдаем за элементами, которые должны появляться при скролле
    const animatedElements = document.querySelectorAll('.animate-on-scroll');
    animatedElements.forEach(el => observer.observe(el));
  }

  /**
   * Анимация появления элемента
   */
  animateElementAppear(element) {
    element.style.opacity = '0';
    element.style.transform = 'translateY(30px)';
    element.style.transition = 'opacity 0.6s ease-out, transform 0.6s ease-out';
    
    setTimeout(() => {
      element.style.opacity = '1';
      element.style.transform = 'translateY(0)';
    }, 100);
  }

  /**
   * Настроить hover эффекты
   */
  setupHoverEffects() {
    // Анимация для ссылок
    const links = document.querySelectorAll('a');
    links.forEach(link => {
      link.addEventListener('mouseenter', () => {
        this.animateLinkHover(link);
      });

      link.addEventListener('mouseleave', () => {
        this.animateLinkLeave(link);
      });
    });

    // Анимация для иконок
    const icons = document.querySelectorAll('.icon, [class*="icon-"]');
    icons.forEach(icon => {
      icon.addEventListener('mouseenter', () => {
        this.animateIconHover(icon);
      });

      icon.addEventListener('mouseleave', () => {
        this.animateIconLeave(icon);
      });
    });
  }

  /**
   * Анимация hover ссылки
   */
  animateLinkHover(link) {
    link.style.transform = 'translateY(-1px)';
    link.style.transition = 'transform 0.2s ease-out';
  }

  /**
   * Анимация ухода с ссылки
   */
  animateLinkLeave(link) {
    link.style.transform = 'translateY(0)';
    link.style.transition = 'transform 0.2s ease-out';
  }

  /**
   * Анимация hover иконки
   */
  animateIconHover(icon) {
    icon.style.transform = 'scale(1.1) rotate(5deg)';
    icon.style.transition = 'transform 0.2s ease-out';
  }

  /**
   * Анимация ухода с иконки
   */
  animateIconLeave(icon) {
    icon.style.transform = 'scale(1) rotate(0deg)';
    icon.style.transition = 'transform 0.2s ease-out';
  }

  /**
   * Анимация успешного действия
   */
  animateSuccess(element) {
    element.classList.add('success-animation');
    setTimeout(() => {
      element.classList.remove('success-animation');
    }, 600);
  }

  /**
   * Анимация ошибки
   */
  animateError(element) {
    element.classList.add('error-shake');
    setTimeout(() => {
      element.classList.remove('error-shake');
    }, 500);
  }

  /**
   * Анимация загрузки
   */
  animateLoading(element) {
    element.classList.add('loading-animation');
  }

  /**
   * Остановить анимацию загрузки
   */
  stopLoading(element) {
    element.classList.remove('loading-animation');
  }

  /**
   * Анимация счетчика
   */
  animateCounter(element) {
    element.classList.add('counter-pulse');
    setTimeout(() => {
      element.classList.remove('counter-pulse');
    }, 300);
  }

  /**
   * Анимация появления модального окна
   */
  animateModalAppear(modal) {
    modal.style.opacity = '0';
    modal.style.transform = 'scale(0.8)';
    modal.style.transition = 'opacity 0.3s ease-out, transform 0.3s ease-out';
    
    setTimeout(() => {
      modal.style.opacity = '1';
      modal.style.transform = 'scale(1)';
    }, 100);
  }

  /**
   * Анимация исчезновения модального окна
   */
  animateModalDisappear(modal) {
    modal.style.opacity = '0';
    modal.style.transform = 'scale(0.8)';
    modal.style.transition = 'opacity 0.3s ease-out, transform 0.3s ease-out';
    
    setTimeout(() => {
      modal.style.display = 'none';
    }, 300);
  }
}

// Создаем глобальный экземпляр
window.microAnimations = new MicroAnimations();