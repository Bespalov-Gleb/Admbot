/**
 * Система оптимистичных обновлений
 * Обеспечивает мгновенный feedback пользователю до получения ответа сервера
 */

class OptimisticUpdates {
  constructor() {
    this.pendingUpdates = new Map();
    this.rollbackCallbacks = new Map();
  }

  /**
   * Оптимистичное добавление в корзину
   */
  static async addToCart(dishId, quantity, options = {}) {
    const {
      onSuccess = () => {},
      onError = () => {},
      onRollback = () => {}
    } = options;

    try {
      // 1. Сразу обновляем UI
      const rollbackData = this.updateCartUI(dishId, quantity);
      
      // 2. Показываем feedback пользователю
      this.showSuccessFeedback('Добавлено в корзину');
      
      // 3. Отправляем запрос на сервер
      const response = await fetch(api + '/cart/items', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Telegram-User-Id': String(uid)
        },
        body: JSON.stringify({
          dish_id: dishId,
          qty: quantity,
          chosen_options: options.chosenOptions || []
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const result = await response.json();
      
      // 4. Обновляем UI с реальными данными
      this.updateCartWithServerData(result);
      onSuccess(result);
      
    } catch (error) {
      console.error('Add to cart error:', error);
      
      // 5. Откатываем изменения при ошибке
      this.rollbackCartUI(rollbackData);
      this.showErrorFeedback('Не удалось добавить в корзину');
      onError(error);
    }
  }

  /**
   * Оптимистичное обновление количества в корзине
   */
  static async updateCartQuantity(itemId, newQuantity) {
    try {
      // 1. Сохраняем старое значение для отката
      const oldQuantity = this.getCurrentCartQuantity(itemId);
      
      // 2. Сразу обновляем UI
      this.updateCartQuantityUI(itemId, newQuantity);
      
      // 3. Отправляем запрос
      const response = await fetch(api + `/cart/items/${itemId}?qty=${newQuantity}`, {
        method: 'PATCH',
        headers: {
          'X-Telegram-User-Id': String(uid)
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      // 4. Обновляем с серверными данными
      await this.loadCartAndSync();
      
    } catch (error) {
      console.error('Update cart quantity error:', error);
      
      // 5. Откатываем при ошибке
      this.updateCartQuantityUI(itemId, oldQuantity);
      this.showErrorFeedback('Не удалось обновить количество');
    }
  }

  /**
   * Оптимистичное удаление из корзины
   */
  static async removeFromCart(itemId) {
    try {
      // 1. Сохраняем данные для отката
      const itemData = this.getCartItemData(itemId);
      
      // 2. Сразу удаляем из UI
      this.removeCartItemUI(itemId);
      this.showSuccessFeedback('Удалено из корзины');
      
      // 3. Отправляем запрос
      const response = await fetch(api + `/cart/items/${itemId}`, {
        method: 'DELETE',
        headers: {
          'X-Telegram-User-Id': String(uid)
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      // 4. Обновляем с серверными данными
      await this.loadCartAndSync();
      
    } catch (error) {
      console.error('Remove from cart error:', error);
      
      // 5. Восстанавливаем при ошибке
      this.restoreCartItemUI(itemId, itemData);
      this.showErrorFeedback('Не удалось удалить из корзины');
    }
  }

  /**
   * Оптимистичное обновление статуса заказа
   */
  static async updateOrderStatus(orderId, newStatus) {
    try {
      // 1. Сохраняем старое состояние
      const oldStatus = this.getCurrentOrderStatus(orderId);
      
      // 2. Сразу обновляем UI
      this.updateOrderStatusUI(orderId, newStatus);
      
      // 3. Отправляем запрос
      const response = await fetch(api + `/ra/orders/${orderId}/${newStatus}`, {
        method: 'POST',
        headers: {
          'X-Telegram-User-Id': String(uid)
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      // 4. Обновляем с серверными данными
      await this.loadOrderAndSync(orderId);
      
    } catch (error) {
      console.error('Update order status error:', error);
      
      // 5. Откатываем при ошибке
      this.updateOrderStatusUI(orderId, oldStatus);
      this.showErrorFeedback('Не удалось обновить статус заказа');
    }
  }

  /**
   * Обновление UI корзины
   */
  static updateCartUI(dishId, quantity) {
    // Получаем текущее состояние корзины
    const currentCart = window.cart || { items: [] };
    
    // Ищем существующий элемент
    const existingItem = currentCart.items.find(item => 
      item.dish_id === dishId && 
      (!item.chosen_options || item.chosen_options.length === 0)
    );

    if (existingItem) {
      // Обновляем количество существующего элемента
      const oldQuantity = existingItem.qty;
      existingItem.qty += quantity;
      
      // Обновляем UI
      this.updateCartItemQuantityUI(existingItem.id, existingItem.qty);
      
      return { type: 'update', itemId: existingItem.id, oldQuantity };
    } else {
      // Добавляем новый элемент
      const newItem = {
        id: 'temp_' + Date.now(),
        dish_id: dishId,
        qty: quantity,
        chosen_options: []
      };
      
      currentCart.items.push(newItem);
      
      // Обновляем UI
      this.addCartItemUI(newItem);
      
      return { type: 'add', itemId: newItem.id, item: newItem };
    }
  }

  /**
   * Откат изменений корзины
   */
  static rollbackCartUI(rollbackData) {
    if (rollbackData.type === 'update') {
      this.updateCartItemQuantityUI(rollbackData.itemId, rollbackData.oldQuantity);
    } else if (rollbackData.type === 'add') {
      this.removeCartItemUI(rollbackData.itemId);
    }
  }

  /**
   * Обновление количества элемента корзины в UI
   */
  static updateCartItemQuantityUI(itemId, quantity) {
    const itemElement = document.querySelector(`[data-item-id="${itemId}"]`);
    if (itemElement) {
      const quantityElement = itemElement.querySelector('.item-quantity');
      if (quantityElement) {
        quantityElement.textContent = quantity;
      }
      
      // Обновляем общую сумму
      this.updateCartTotal();
    }
  }

  /**
   * Добавление элемента корзины в UI
   */
  static addCartItemUI(item) {
    // Эта функция должна быть реализована в зависимости от структуры UI
    // Здесь мы обновляем глобальное состояние
    if (window.cart) {
      window.cart.items.push(item);
    }
    
    // Обновляем счетчик корзины
    this.updateCartCounter();
  }

  /**
   * Удаление элемента корзины из UI
   */
  static removeCartItemUI(itemId) {
    const itemElement = document.querySelector(`[data-item-id="${itemId}"]`);
    if (itemElement) {
      itemElement.remove();
    }
    
    // Обновляем глобальное состояние
    if (window.cart) {
      window.cart.items = window.cart.items.filter(item => item.id !== itemId);
    }
    
    // Обновляем счетчик и общую сумму
    this.updateCartCounter();
    this.updateCartTotal();
  }

  /**
   * Обновление счетчика корзины
   */
  static updateCartCounter() {
    const cartCounter = document.querySelector('.cart-counter');
    if (cartCounter && window.cart) {
      const totalItems = window.cart.items.reduce((sum, item) => sum + item.qty, 0);
      cartCounter.textContent = totalItems;
      cartCounter.style.display = totalItems > 0 ? 'block' : 'none';
    }
  }

  /**
   * Обновление общей суммы корзины
   */
  static updateCartTotal() {
    const totalElement = document.querySelector('.cart-total');
    if (totalElement && window.cart) {
      const total = window.cart.items.reduce((sum, item) => {
        const dish = window.dishesMap?.get(item.dish_id);
        return sum + (dish?.price || 0) * item.qty;
      }, 0);
      
      totalElement.textContent = `${total} ₽`;
    }
  }

  /**
   * Показать успешный feedback
   */
  static showSuccessFeedback(message) {
    if (window.toastSystem) {
      window.toastSystem.success(message);
    } else {
      console.log('Success:', message);
    }
  }

  /**
   * Показать ошибку feedback
   */
  static showErrorFeedback(message) {
    if (window.toastSystem) {
      window.toastSystem.error(message);
    } else {
      console.error('Error:', message);
    }
  }

  /**
   * Загрузить корзину и синхронизировать с сервером
   */
  static async loadCartAndSync() {
    try {
      const response = await fetch(api + '/cart' + (uid ? ('?uid=' + uid) : ''), {
        headers: { 'X-Telegram-User-Id': String(uid) }
      });
      
      if (response.ok) {
        const cartData = await response.json();
        window.cart = cartData;
        
        // Обновляем UI с серверными данными
        if (window.renderCartItems) {
          window.renderCartItems();
        }
      }
    } catch (error) {
      console.error('Error loading cart:', error);
    }
  }

  /**
   * Получить текущее количество в корзине
   */
  static getCurrentCartQuantity(itemId) {
    const itemElement = document.querySelector(`[data-item-id="${itemId}"]`);
    if (itemElement) {
      const quantityElement = itemElement.querySelector('.item-quantity');
      return quantityElement ? parseInt(quantityElement.textContent) : 0;
    }
    return 0;
  }

  /**
   * Получить данные элемента корзины
   */
  static getCartItemData(itemId) {
    const itemElement = document.querySelector(`[data-item-id="${itemId}"]`);
    if (itemElement) {
      return {
        id: itemId,
        html: itemElement.outerHTML,
        quantity: this.getCurrentCartQuantity(itemId)
      };
    }
    return null;
  }

  /**
   * Восстановить элемент корзины в UI
   */
  static restoreCartItemUI(itemId, itemData) {
    if (itemData && itemData.html) {
      const cartContainer = document.querySelector('.cart-items');
      if (cartContainer) {
        cartContainer.insertAdjacentHTML('beforeend', itemData.html);
      }
    }
  }
}

// Экспортируем для использования
window.OptimisticUpdates = OptimisticUpdates;