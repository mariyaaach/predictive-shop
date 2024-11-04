document.addEventListener("DOMContentLoaded", function() {
    const registerLink = document.querySelector('a');

    registerLink.addEventListener('click', function(event) {
        event.preventDefault();  // Останавливаем стандартное поведение ссылки
        window.location.href = '../register/index.html';  // Перенаправляем на страницу регистрации
    });
});

document.addEventListener("DOMContentLoaded", function() {
    const registerLink = document.querySelector('button');

    registerLink.addEventListener('click', function(event) {
        event.preventDefault();  // Останавливаем стандартное поведение ссылки
        window.location.href = '../main/index.html';  // Перенаправляем на страницу регистрации
    });
});
