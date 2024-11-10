document.addEventListener("DOMContentLoaded", function() {
    const logo = document.getElementById('logo');
    logo.addEventListener('click', function(event) {
        event.preventDefault();
        window.location.href = '../../main/index.html';
    });

    const wishlistLink = document.querySelector('img[alt="Wishlist Icon"]');
    if (wishlistLink) {
        wishlistLink.addEventListener('click', function(event) {
            event.preventDefault();
            window.location.href = '../../wishlist/index.html';
        });
    } else {
        console.log("Элемент избранного не найден");
    }

    const cartLink = document.querySelector('img[alt="Cart Icon"]');
    if (cartLink) {
        cartLink.addEventListener('click', function(event) {
            event.preventDefault();
            window.location.href = '../../cart/index.html';
        });
    } else {
        console.log("Элемент корзины не найден");
    }

    const editButton = document.getElementById('editButton');
    const saveButton = document.getElementById('saveButton');
    const userName = document.getElementById('userName');
    const userEmail = document.getElementById('userEmail');

    editButton.addEventListener('click', enableEdit);
    saveButton.addEventListener('click', saveChanges);

    function enableEdit() {
        userName.contentEditable = "true";
        userEmail.contentEditable = "true";
        userName.style.border = "1px solid #ccc";
        userEmail.style.border = "1px solid #ccc";

        editButton.style.display = "none";
        saveButton.style.display = "inline-block";
    }

    function saveChanges() {
        userName.contentEditable = "false";
        userEmail.contentEditable = "false";
        userName.style.border = "none";
        userEmail.style.border = "none";

        saveButton.style.display = "none";
        editButton.style.display = "inline-block";

        // TODO: добавить отправку данных на сервер
    }

    // Обработка кликов на товарные карточки
    const productItems = document.querySelectorAll('.product-item');
    productItems.forEach(item => {
        item.addEventListener('click', function() {
            const productName = this.querySelector('h4').innerText;
            const productPrice = this.querySelector('p:nth-of-type(1)').innerText;
            const productViews = this.querySelector('p:nth-of-type(2)').innerText;
            const productPurchases = this.querySelector('p:nth-of-type(3)').innerText;

            alert(`Информация о товаре:\n${productName}\n${productPrice}\n${productViews}\n${productPurchases}`);
        });
    });
});
