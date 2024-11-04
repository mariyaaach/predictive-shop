document.addEventListener("DOMContentLoaded", function() {
    const registerBtn = document.getElementById("register-btn");
    const popup = document.getElementById("popup");
    const userEmailSpan = document.getElementById("user-email");
    const emailInput = document.getElementById("email");
    const confirmBtn = document.getElementById("confirm-btn");
    const confirmationCodeInput = document.getElementById("confirmation-code");
    
    let confirmationCode = "12345";  // Это код подтверждения для примера

    // При нажатии на кнопку "Зарегистрироваться"
    registerBtn.addEventListener("click", function() {
        const email = emailInput.value;
        
        if (email) {
            userEmailSpan.textContent = email;
            popup.classList.remove("hidden");
        } else {
            alert("Пожалуйста, введите e-mail");
        }
    });

    // При нажатии на кнопку "Подтвердить"
    confirmBtn.addEventListener("click", function() {
        const enteredCode = confirmationCodeInput.value;
        
        if (enteredCode === confirmationCode) {
            alert("Аккаунт подтвержден");
            window.location.href = "../main/index.html";  
        } else {
            alert("Неверный код подтверждения");
        }
    });
});

document.addEventListener("DOMContentLoaded", function() {
    const registerLink = document.querySelector('a');

    registerLink.addEventListener('click', function(event) {
        event.preventDefault();  // Останавливаем стандартное поведение ссылки
        window.location.href = '../login/index.html';  // Перенаправляем на страницу регистрации
    });
});
