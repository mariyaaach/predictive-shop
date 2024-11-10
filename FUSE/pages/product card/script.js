document.querySelector('.add-to-cart-button').addEventListener('click', () => {
    alert('Товар добавлен в корзину!');
    //TODO: логика для обновления корзины на backend
});

function toggleReviewForm() {
    const reviewForm = document.getElementById('reviewForm');
    reviewForm.style.display = reviewForm.style.display === 'none' ? 'block' : 'none';
}

function addReview() {
    const name = document.getElementById('reviewerName').value.trim();
    const text = document.getElementById('reviewText').value.trim();
    const rating = document.getElementById('reviewRating').value;

    if (!name || !text) {
        alert("Пожалуйста, заполните все поля.");
        return;
    }

    // Создаем новый элемент для отзыва
    const reviewList = document.getElementById('reviewList');
    const newReview = document.createElement('div');
    newReview.classList.add('review');
    newReview.innerHTML = `
        <p><strong>${name}:</strong> ${text}</p>
        <p><strong>Оценка:</strong> ${'★'.repeat(rating)}${'☆'.repeat(5 - rating)}</p>
    `;

    // Добавляем новый отзыв в список и очищаем форму
    reviewList.appendChild(newReview);
    document.getElementById('reviewerName').value = '';
    document.getElementById('reviewText').value = '';
    document.getElementById('reviewRating').value = '5';
    toggleReviewForm(); // Скрываем форму после добавления
}
