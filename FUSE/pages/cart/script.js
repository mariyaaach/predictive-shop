
document.addEventListener("DOMContentLoaded", function() {
    const logo = document.getElementById('logo'); // Получаем элемент лого

    logo.addEventListener('click', function(event) {
        event.preventDefault();  // Останавливаем стандартное поведение ссылки (если это элемент ссылки)
        window.location.href = '../main/index.html';  // Укажите путь к главной странице
    });
});

document.addEventListener("DOMContentLoaded", function() {
    // Находим элемент с изображением корзины по alt атрибуту или с использованием класса/индекса, если атрибуты уникальны
    const cartLink = document.querySelector('img[alt="Wishlist Icon"]');

    // Проверяем, найден ли элемент
    if (wishLink) {
        wishLink.addEventListener('click', function(event) {
            event.preventDefault();  // Останавливаем стандартное поведение ссылки
            window.location.href = '../wishlist/index.html';  // Переход на страницу корзины
        });
    } else {
        console.log("Элемент сердечечка не найден");
    }
});

document.addEventListener("DOMContentLoaded", function() {
    const userLink = document.querySelector('img[alt="User Icon"]');

    // Проверяем, найден ли элемент
    if (userLink) {
        userLink.addEventListener('click', function(event) {
            event.preventDefault();  // Останавливаем стандартное поведение ссылки
            window.location.href = '../user/buyer/index.html';  
        });
    } else {
        console.log("Элемент юзера не найден");
    }
});


// Массив товаров
const products = [
    { id: 1, image: '../../assets/images/product1.jpg', title: 'CLEAN+ cream wax', category: 'Подвески - мягкие игрушки', price: 570, quantity: 1 },
    { id: 2, image: '../../assets/images/product2.jpg', title: 'NATROL bone & joint health 5000 ME', category: 'Аксессуары - PS4', price: 2509, quantity: 1 },
    { id: 3, image: '../../assets/images/product3.jpg', title: 'INFLUENCE BEAUTY Ekso skin', category: 'Музыка - винил', price: 894, quantity: 1 }
];

// Корзина
let cart = [];

// Функция для отображения товаров в корзине
function displayCart() {
    const cartItemsContainer = document.querySelector('.cart-items');
    const totalPriceEl = document.querySelector('.total-price');
    cartItemsContainer.innerHTML = ''; // Очищаем контейнер

    let total = 0;
    cart.forEach(product => {
        const cartItem = document.createElement('div');
        cartItem.classList.add('cart-item');
        cartItem.innerHTML = `
            <div class="cart-item-image" style="background-image: url('${product.image}');"></div>
            <div class="cart-item-details">
                <h3>${product.title}</h3>
                <p class="category">${product.category}</p>
                <span class="price">${product.price} ₽</span>
                <div class="quantity-control">
                    <button class="decrement" onclick="changeQuantity(${product.id}, 'decrement')">-</button>
                    <span class="quantity">${product.quantity}</span>
                    <button class="increment" onclick="changeQuantity(${product.id}, 'increment')">+</button>
                </div>
            </div>
        `;
        cartItemsContainer.appendChild(cartItem);
        total += product.price * product.quantity; // Обновляем итоговую стоимость
    });

    // Обновляем итоговую сумму
    totalPriceEl.textContent = `${total} ₽`;
}

// Функция для добавления товара в корзину
function addToCart(productId) {
    const product = products.find(p => p.id === productId);
    const cartProduct = cart.find(p => p.id === productId);
    if (cartProduct) {
        cartProduct.quantity++;
    } else {
        cart.push({ ...product }); // Копируем продукт и добавляем в корзину
    }
    displayCart(); // Обновляем отображение корзины
}

// Функция для изменения количества товара
function changeQuantity(productId, action) {
    const cartProduct = cart.find(p => p.id === productId);
    if (cartProduct) {
        if (action === 'increment') {
            cartProduct.quantity++;
        } else if (action === 'decrement' && cartProduct.quantity > 1) {
            cartProduct.quantity--;
        } else if (action === 'decrement' && cartProduct.quantity === 1) {
            cart = cart.filter(p => p.id !== productId); // Удаляем товар из корзины, если количество 1
        }
        displayCart(); // Обновляем отображение корзины
    }
}

// Добавляем тестовые товары для отображения (или вызовите addToCart(productId) для добавления товара в корзину)
products.forEach(product => addToCart(product.id));
