document.addEventListener("DOMContentLoaded", function() {
    const registerLink = document.querySelector('a');

    registerLink.addEventListener('click', function(event) {
        event.preventDefault();  // Останавливаем стандартное поведение ссылки
        window.location.href = '../login/index.html';  // Перенаправляем на страницу регистрации
    });
});
