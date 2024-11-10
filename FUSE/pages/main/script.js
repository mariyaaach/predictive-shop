document.addEventListener("DOMContentLoaded", function() {
    // Находим элемент с изображением корзины по alt атрибуту или с использованием класса/индекса, если атрибуты уникальны
    const cartLink = document.querySelector('img[alt="Cart Icon"]');

    // Проверяем, найден ли элемент
    if (cartLink) {
        cartLink.addEventListener('click', function(event) {
            event.preventDefault();  // Останавливаем стандартное поведение ссылки
            window.location.href = '../cart/index.html';  // Переход на страницу корзины
        });
    } else {
        console.log("Элемент корзины не найден");
    }
});

document.addEventListener("DOMContentLoaded", function() {
    // Находим элемент с изображением корзины по alt атрибуту или с использованием класса/индекса, если атрибуты уникальны
    const wishLinkLink = document.querySelector('img[alt="Wishlist Icon"]');

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



// Данные для разных секций
const newProducts = [
    { image: '../../assets/images/product1.jpg', category: 'Подвески - мягкие игрушки', title: 'CLEAN+ cream wax', price: '570 ₽' },
    { image: '../../assets/images/product2.jpg', category: 'Аксессуары - PS4', title: 'NATROL bone & joint health 5000 ME', price: '2509 ₽' },
    { image: '../../assets/images/product3.jpg', category: 'Музыка - винил', title: 'INFLUENCE BEAUTY Ekso skin', price: '894 ₽' },
    
];

const categories = [
    { image: '../../assets/images/consoles.png', title: 'Консоли' },
    { image: '../../assets/images/books.png', title: 'Книги' },
    { image: '../../assets/images/gifts.png', title: 'Подарки' },
    { image: '../../assets/images/batteries.png', title: 'Батарейки' },
    { image: '../../assets/images/card.png', title: 'Карты' }
];

const recommendations = [
    { image: '../../assets/images/product4.jpg', category: 'Аксессуары - ПК', title: 'Ergonomic Keyboard', price: '3000 ₽' },
    { image: '../../assets/images/product5.jpg', category: 'Игрушки - интерактивные', title: 'Smart Robot', price: '1500 ₽' },
    { image: '../../assets/images/product6.jpg', category: 'Канцелярия - ручки', title: 'Gel Ink Pen', price: '120 ₽' }
];

// Функция для добавления товаров в секцию
function addProductsToSection(sectionId, products) {
    const section = document.getElementById(sectionId);
    products.forEach(product => {
        const productItem = document.createElement('div');
        productItem.classList.add('product-item');
        productItem.innerHTML = `
            <div class="product-image">
                <img src="${product.image}" alt="Product Image">
            </div>
            <p class="product-category">${product.category}</p>
            <h3 class="product-title">${product.title}</h3>
            <span class="price">${product.price}</span>
        `;
        section.appendChild(productItem);
    });
}

// Функция для добавления категорий
function addCategoriesToSection(sectionId, categories) {
    const section = document.getElementById(sectionId);
    categories.forEach(category => {
        const categoryItem = document.createElement('div');
        categoryItem.classList.add('category-item');
        categoryItem.innerHTML = `
            <div class="product-image">
                <img src="${category.image}" alt="${category.title}">
            </div>
            <h3 class="product-title">${category.title}</h3>
        `;
        section.appendChild(categoryItem);
    });
}

// Добавляем товары и категории
addProductsToSection('new-products-list', newProducts);
addCategoriesToSection('category-list', categories);
addProductsToSection('recommendations-list', recommendations);


