document.addEventListener("DOMContentLoaded", function() {
    const logo = document.getElementById('logo'); // Получаем элемент лого

    logo.addEventListener('click', function(event) {
        event.preventDefault();  // Останавливаем стандартное поведение ссылки (если это элемент ссылки)
        window.location.href = '../../main/index.html';  // Укажите путь к главной странице
    });
});

document.addEventListener("DOMContentLoaded", function() {
    // Находим элемент с изображением корзины по alt атрибуту или с использованием класса/индекса, если атрибуты уникальны
    const cartLink = document.querySelector('img[alt="Wishlist Icon"]');

    // Проверяем, найден ли элемент
    if (wishLink) {
        wishLink.addEventListener('click', function(event) {
            event.preventDefault();  // Останавливаем стандартное поведение ссылки
            window.location.href = '../../wishlist/index.html';  // Переход на страницу корзины
        });
    } else {
        console.log("Элемент сердечечка не найден");
    }
});

document.addEventListener("DOMContentLoaded", function() {
    // Находим элемент с изображением корзины по alt атрибуту или с использованием класса/индекса, если атрибуты уникальны
    const cartLink = document.querySelector('img[alt="Cart Icon"]');

    // Проверяем, найден ли элемент
    if (cartLink) {
        cartLink.addEventListener('click', function(event) {
            event.preventDefault();  // Останавливаем стандартное поведение ссылки
            window.location.href = '../../cart/index.html';  // Переход на страницу корзины
        });
    } else {
        console.log("Элемент сердечечка не найден");
    }
});

function enableEdit() {
    const userName = document.getElementById('userName');
    const userEmail = document.getElementById('userEmail');
    const userPhone = document.getElementById('userPhone');
    const editButton = document.getElementById('editButton');
    const saveButton = document.getElementById('saveButton');

    // Переключаем в режим редактирования
    userName.contentEditable = "true";
    userEmail.contentEditable = "true";
    userPhone.contentEditable = "true";
    userName.style.border = "1px solid #ccc";
    userEmail.style.border = "1px solid #ccc";
    userPhone.style.border = "1px solid #ccc";

    // Показать кнопку "Сохранить" и скрыть "Внести изменения"
    editButton.style.display = "none";
    saveButton.style.display = "inline-block";
}

function saveChanges() {
    const userName = document.getElementById('userName');
    const userEmail = document.getElementById('userEmail');
    const userPhone = document.getElementById('userPhone');
    const editButton = document.getElementById('editButton');
    const saveButton = document.getElementById('saveButton');

    // Сохраняем изменения и отключаем редактирование
    userName.contentEditable = "false";
    userEmail.contentEditable = "false";
    userPhone.contentEditable = "false";
    userName.style.border = "none";
    userEmail.style.border = "none";
    userPhone.style.border = "none";

    // Показать кнопку "Внести изменения" и скрыть "Сохранить"
    editButton.style.display = "inline-block";
    saveButton.style.display = "none";

    // Здесь можно добавить код для отправки измененных данных на сервер
}
