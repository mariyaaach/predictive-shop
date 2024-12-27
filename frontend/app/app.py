import os
import streamlit as st
import requests
from dateutil import parser
import pytz


# --------------------------------------------------
# Параметры окружения
URL_USERS = os.getenv("URL_USERS", "http://localhost:8000")
URL_PRODUCTS = os.getenv("URL_PRODUCTS", "http://localhost:8001")
URL_ORDERS = os.getenv("URL_ORDERS", "http://localhost:8002")


def main():
    st.set_page_config(page_title="Store App", layout="wide")
    
    if 'access_token' not in st.session_state:
        st.session_state['access_token'] = None

    if st.session_state['access_token'] is None:
        page = st.sidebar.selectbox("Меню:", ["Вход", "Регистрация"])
        if page == "Вход":
            login_page()
        else:
            register_page()
    else:
        display_main_app()


def login_page():
    st.title("Вход")
    email = st.text_input("Email")
    password = st.text_input("Пароль", type="password")
    if st.button("Войти"):
        data = {"username": email, "password": password}
        resp = requests.post(f"{URL_USERS}/token", data=data)
        if resp.status_code == 200:
            token_data = resp.json()
            st.session_state['access_token'] = token_data["access_token"]
            st.success("Успешный вход!")
            st.experimental_rerun()
        else:
            st.error("Неверный email или пароль")


def register_page():
    st.title("Регистрация")
    user_name = st.text_input("Имя пользователя")
    first_name = st.text_input("Имя")
    last_name = st.text_input("Фамилия")
    email = st.text_input("Email")
    phone = st.text_input("Телефон")
    address = st.text_input("Адрес")
    password = st.text_input("Пароль", type="password")
    role = st.selectbox("Роль", ["buyer", "seller"])

    if st.button("Зарегистрироваться"):
        user_data = {
            "user_name": user_name,
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "phone": phone,
            "address": address,
            "password": password,
            "role": role,
            "verified": False
        }
        resp = requests.post(f"{URL_USERS}/users", json=user_data)
        if resp.status_code == 201:
            st.success("Регистрация успешна! Теперь вы можете войти.")
        else:
            st.error(f"Ошибка регистрации: {resp.text}")


def display_main_app():
    token = st.session_state['access_token']
    headers = {"Authorization": f"Bearer {token}"}

    resp = requests.get(f"{URL_USERS}/users/me", headers=headers)
    if resp.status_code != 200:
        st.error("Не удалось получить профиль. Повторите вход.")
        st.session_state['access_token'] = None
        st.experimental_rerun()
        return

    user = resp.json()
    st.sidebar.write(f"Привет, {user['first_name']} {user['last_name']}!")
    
    if st.sidebar.button("Выйти"):
        st.session_state['access_token'] = None
        st.experimental_rerun()
        return

    if user["role"] == "buyer":
        buyer_panel(headers, user)
    elif user["role"] == "seller":
        seller_panel(headers, user)
    else:
        st.error("Неизвестная роль пользователя")


# ------------------- Блок покупателя -------------------
def buyer_panel(headers, user):
    st.title("Рады приветствовать!")
    menu = st.sidebar.radio("Действия:", ["Все товары", "Корзина", "Мой профиль", "Мои заказы"])
    
    if menu == "Все товары":
        show_all_products(headers, user)
    elif menu == "Корзина":
        show_cart(headers, user)
    elif menu == "Мой профиль":
        show_profile_and_edit(headers, user)
    elif menu == "Мои заказы":
        show_buyer_orders(headers, user)  

def show_buyer_orders(headers, user):
    """
    Показывает все заказы покупателя (user_id) и даёт кнопку «Отменить заказ».
    """
    st.subheader("Мои заказы")

    # 1. Делаем запрос на order-service: GET /orders/buyer/{user_id}
    resp = requests.get(f"{URL_ORDERS}/orders/buyer/{user['user_id']}", headers=headers)
    if resp.status_code != 200:
        st.error(f"Ошибка получения заказов: {resp.text}")
        return

    orders = resp.json()
    if not orders:
        st.info("У вас нет заказов.")
        return

    for order in orders:
        creation_str = format_order_time(order["creation_time"], timezone="Europe/Moscow")
        st.write(f"**Заказ #{order['order_id']}**, статус: {order['status']}")
        st.write(f"Создан: {creation_str}, итоговая сумма: {order['total_price']}")
        st.write("Состав заказа:")
        for item in order["items"]:
            st.write(f"- {item['name']} x {item['quantity']} (цена за ед.: {item['unit_price']})")

        # Если заказ уже в статусе canceled/delivered, отменить его смысла нет
        # но это уже логика на ваше усмотрение
        if order['status'] not in ["canceled", "delivered"]:
            # Кнопка «Отменить заказ»
            if st.button(f"Отменить заказ #{order['order_id']}", key=f"cancel_order_{order['order_id']}"):
                patch_data = {"status": "canceled"}
                patch_resp = requests.patch(
                    f"{URL_ORDERS}/orders/{order['order_id']}/status",
                    json=patch_data,
                    headers=headers
                )
                if patch_resp.status_code == 200:
                    st.success("Заказ отменён.")
                    st.experimental_rerun()
                else:
                    st.error(f"Ошибка отмены заказа: {patch_resp.text}")

        st.write("---")


def show_all_products(headers, user):
    st.subheader("Список всех товаров")
    r = requests.get(f"{URL_PRODUCTS}/products", headers=headers)
    if r.status_code != 200:
        st.error(f"Ошибка получения списка товаров: {r.text}")
        return

    products = r.json()
    if not products:
        st.info("Товаров пока нет.")
        return

    for product in products:
        # Для каждого товара получаем category_name
        category_name = get_category_name(product["category_id"], headers)

        st.write(
            f"**{product['name']}**  — "
            f"цена {product['price']}, в наличии {product['stock']}, "
            f"категория: {category_name}"
        )
        st.write(f"Описание: {product['description']}")

        qty = st.number_input(
            f"Количество (товар {product['product_id']})",
            min_value=1,
            value=1,
            key=f"buyer_prod_{product['product_id']}"
        )
        if st.button(f"Добавить в корзину", key=f"btn_add_{product['product_id']}"):
            cart_item = {
                "product_id": product["product_id"],
                "product_name": product["name"],
                "price": float(product["price"]),
                "seller_id": product["seller_id"],
                "quantity": qty
            }
            resp = requests.post(f"{URL_ORDERS}/users/{user['user_id']}/cart/", json=cart_item, headers=headers)
            if resp.status_code == 201:
                st.success("Товар добавлен в корзину!")
            else:
                st.error(f"Ошибка добавления в корзину: {resp.text}")
        st.write("---")


def show_cart(headers, user):
    st.subheader("Моя корзина")
    r = requests.get(f"{URL_ORDERS}/users/{user['user_id']}/cart/", headers=headers)
    if r.status_code != 200:
        st.error(f"Ошибка загрузки корзины: {r.text}")
        return

    cart_items = r.json()
    if not cart_items:
        st.info("Корзина пуста.")
        return

    for item in cart_items:
        st.write(f"**{item['product_name']}**")
        st.write(f"Текущее количество: {item['quantity']}, цена за ед.: {item['price']}")

        col1, col2 = st.columns(2)
        with col1:
            new_qty = st.number_input(
                f"Новое количество ",
                min_value=1,
                value=item['quantity'],
                key=f"qty_update_{item['cart_item_id']}"
            )
            if st.button(f"Обновить кол-во ", key=f"btn_upd_{item['cart_item_id']}"):
                diff = new_qty - item['quantity']
                if diff > 0:
                    add_data = {
                        "product_id": item['product_id'],
                        "product_name": item['product_name'],
                        "price": item['price'],
                        "seller_id": item['seller_id'],
                        "quantity": diff
                    }
                    resp = requests.post(
                        f"{URL_ORDERS}/users/{user['user_id']}/cart/", 
                        json=add_data,
                        headers=headers
                    )
                    if resp.status_code == 201:
                        st.success("Количество увеличено")
                        st.experimental_rerun()
                    else:
                        st.error(f"Ошибка: {resp.text}")
                elif diff < 0:
                    remove_qty = abs(diff)
                    remove_url = f"{URL_ORDERS}/users/{user['user_id']}/cart/{item['product_id']}?quantity={remove_qty}"
                    resp = requests.delete(remove_url, headers=headers)
                    if resp.status_code == 200:
                        st.success("Количество уменьшено")
                        st.experimental_rerun()
                    else:
                        st.error(f"Ошибка: {resp.text}")
        with col2:
            if st.button(f"Удалить (cart_item {item['cart_item_id']})", key=f"btn_del_{item['cart_item_id']}"):
                remove_url = f"{URL_ORDERS}/users/{user['user_id']}/cart/{item['product_id']}?quantity={item['quantity']}"
                resp = requests.delete(remove_url, headers=headers)
                if resp.status_code == 200:
                    st.success("Товар удалён из корзины.")
                    st.experimental_rerun()
                else:
                    st.error(f"Ошибка: {resp.text}")

        st.write("---")
    
    total_resp = requests.get(f"{URL_ORDERS}/users/{user['user_id']}/cart/total/", headers=headers)
    if total_resp.status_code == 200:
        total_data = total_resp.json()  # { "user_id": ..., "total_price": ... }
        st.write(f"**Итоговая сумма:** {total_data['total_price']}")
    else:
        st.warning("Не удалось получить итоговую сумму из сервиса заказа.")

    # Оформление заказа
    st.write("### Оформить заказ")
    if st.button("Создать заказ из корзины"):
        cart_resp = requests.get(f"{URL_ORDERS}/users/{user['user_id']}/cart/", headers=headers)
        if cart_resp.status_code == 200:
            cart_items = cart_resp.json()
            if not cart_items:
                st.info("Корзина пуста, нечего оформлять.")
                return
            items_for_order = []
            for ci in cart_items:
                items_for_order.append({
                    "product_id": ci["product_id"],
                    "name": ci["product_name"],
                    "quantity": ci["quantity"],
                    "unit_price": ci["price"],
                    "seller_id": ci["seller_id"]
                })
            order_data = {
                "user_id": user["user_id"],
                "items": items_for_order
            }
            order_resp = requests.post(f"{URL_ORDERS}/orders/", json=order_data, headers=headers)
            if order_resp.status_code == 201:
                st.success("Заказ успешно оформлен!")
            else:
                st.error(f"Ошибка при оформлении заказа: {order_resp.text}")
        else:
            st.error(f"Ошибка при повторном получении корзины: {cart_resp.text}")


def show_profile_and_edit(headers, user):
    st.subheader("Мой профиль")
    st.write(f"Имя: {user['first_name']}, Фамилия: {user['last_name']}")
    st.write(f"Email: {user['email']}, Телефон: {user['phone']}")
    st.write(f"Адрес: {user['address']}")

    st.write("---")
    st.write("Редактировать профиль:")
    new_first_name = st.text_input("Имя", value=user['first_name'])
    new_last_name = st.text_input("Фамилия", value=user['last_name'])
    new_phone = st.text_input("Телефон", value=user['phone'])
    new_address = st.text_input("Адрес", value=user['address'])

    if st.button("Сохранить изменения"):
        data_for_update = {
            "first_name": new_first_name,
            "last_name": new_last_name,
            "phone": new_phone,
            "address": new_address
        }
        r = requests.put(f"{URL_USERS}/users/{user['user_id']}", json=data_for_update, headers=headers)
        if r.status_code == 200:
            st.success("Профиль обновлён!")
        else:
            st.error(f"Ошибка обновления: {r.text}")


# ------------------- Блок продавца -------------------
def seller_panel(headers, user):
    st.title("Личный кабинет")
    menu = st.sidebar.radio("Действия:", ["Добавить товар", "Мои товары", "Мои заказы", "Мой профиль"])

    if menu == "Добавить товар":
        create_product(headers, user)
    elif menu == "Мои товары":
        list_seller_products(headers, user)
    elif menu == "Мои заказы":
        list_seller_orders(headers, user)
    elif menu == "Мой профиль":
        show_profile_and_edit(headers, user)


def create_product(headers, user):
    st.subheader("Добавить новый товар")

    # 1) Подгружаем весь список категорий (GET /categories)
    categories = fetch_categories(headers)
    if not categories:
        st.error("Не удалось получить категории. Проверьте, работает ли product-service.")
        return

    # 2) Поля товара
    name = st.text_input("Название товара")
    description = st.text_area("Описание товара")
    price = st.number_input("Цена", min_value=0.0, value=0.0)
    stock = st.number_input("Количество на складе", min_value=0, value=0)

    # В selectbox показываем ИМЕНА категорий
    category_names = [cat["name"] for cat in categories]
    selected_category_name = st.selectbox("Выберите категорию", category_names)

    if st.button("Создать товар"):
        # 3) Найдём category_id по выбранному названию
        selected_category = next((c for c in categories if c["name"] == selected_category_name), None)
        if not selected_category:
            st.error("Ошибка: не найдена категория.")
            return

        category_id = selected_category["category_id"]

        # 4) Отправляем POST /products
        payload = {
            "seller_id": user["user_id"],
            "category_id": category_id,
            "name": name,
            "description": description,
            "price": float(price),
            "stock": int(stock),
        }
        resp = requests.post(f"{URL_PRODUCTS}/products", json=payload, headers=headers)
        if resp.status_code == 201:
            st.success("Товар успешно создан!")
        else:
            st.error(f"Ошибка создания товара: {resp.text}")


def list_seller_products(headers, user):
    st.subheader("Мои товары")

    # Контролируем edit_mode
    if "edit_mode" not in st.session_state:
        st.session_state["edit_mode"] = False
    if "edit_product_id" not in st.session_state:
        st.session_state["edit_product_id"] = None

    if st.session_state["edit_mode"]:
        product_id = st.session_state["edit_product_id"]
        show_edit_form(headers, user, product_id)
    else:
        resp = requests.get(f"{URL_PRODUCTS}/products/seller/{user['user_id']}", headers=headers)
        if resp.status_code != 200:
            st.error(f"Ошибка товаров продавца: {resp.text}")
            return

        products = resp.json()
        if not products:
            st.info("У вас пока нет созданных товаров.")
            return

        for p in products:
            # Получаем название категории по p["category_id"]
            category_name = get_category_name(p["category_id"], headers)

            st.write(
                f"**{p['name']}** \n"
                f"Цена: {p['price']}, Остаток: {p['stock']}, "
                f"Категория: {category_name}"
            )
            st.write(f"Описание: {p['description']}")

            if st.button(f"Редактировать товар", key=f"edit_{p['product_id']}"):
                st.session_state["edit_mode"] = True
                st.session_state["edit_product_id"] = p["product_id"]
                st.experimental_rerun()
            st.write("---")


def show_edit_form(headers, user, product_id):
    """
    Показываем форму редактирования для товара (product_id).
    Если пользователь нажимает "Сохранить" или "Отмена" — выполняем соответствующие действия.
    """
    st.subheader(f"Редактирование товара")

    # 1) Сначала получаем сам товар
    product_resp = requests.get(f"{URL_PRODUCTS}/products/{product_id}", headers=headers)
    if product_resp.status_code != 200:
        st.error(f"Ошибка при получении товара: {product_resp.text}")
        st.session_state["edit_mode"] = False
        return

    product = product_resp.json()

    # 2) Загрузим список категорий (список словарей [{category_id, name}, ...])
    categories = fetch_categories(headers)
    if not categories:
        st.error("Не удалось получить категории. Проверьте, работает ли product-service.")
        st.session_state["edit_mode"] = False
        return

    # 3) Определяем текущее название категории через get_category_name
    current_category_name = get_category_name(product["category_id"], headers)

    # 4) Формируем список всех названий категорий
    category_names = [cat["name"] for cat in categories]

    # 5) Пытаемся найти индекс текущей категории в этом списке
    if current_category_name in category_names:
        default_index = category_names.index(current_category_name)
    else:
        default_index = 0  # Если почему-то не нашли, ставим 0

    # 6) Отображаем поля для редактирования
    new_name = st.text_input("Название", value=product["name"])
    new_desc = st.text_area("Описание", value=product["description"])
    new_price = st.number_input("Цена", min_value=0.0, value=float(product["price"]))
    new_stock = st.number_input("Количество", min_value=0, value=int(product["stock"]))

    # 7) Выбор категории по названию
    selected_category_name = st.selectbox(
        "Категория",
        category_names,
        index=default_index
    )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("Сохранить изменения"):
            # 8) Получаем полный объект выбранной категории (чтобы узнать её ID)
            selected_category = next((c for c in categories if c["name"] == selected_category_name), None)
            if not selected_category:
                st.error("Ошибка: выбранная категория не найдена в списке.")
                return

            new_cat_id = selected_category["category_id"]

            # Формируем данные для PATCH
            data = {
                "name": new_name,
                "description": new_desc,
                "price": new_price,
                "stock": new_stock,
                "category_id": new_cat_id
            }
            # Отправляем запрос на обновление
            r = requests.patch(f"{URL_PRODUCTS}/products/{product_id}", json=data, headers=headers)
            if r.status_code == 200:
                st.success("Товар успешно обновлён.")
            else:
                st.error(f"Ошибка обновления: {r.text}")

            # Выходим из режима редактирования
            st.session_state["edit_mode"] = False
            st.experimental_rerun()

    with col2:
        if st.button("Отмена"):
            # Закрываем режим без сохранения
            st.session_state["edit_mode"] = False
            st.experimental_rerun()



def list_seller_orders(headers, user):
    st.subheader("Заказы с моими товарами")
    r = requests.get(f"{URL_ORDERS}/orders/seller/{user['user_id']}", headers=headers)
    if r.status_code != 200:
        st.error(f"Ошибка получения заказов: {r.text}")
        return

    orders = r.json()
    if not orders:
        st.info("Пока нет заказов с вашими товарами.")
        return

    possible_statuses = ["pending", "shipped", "delivered", "canceled"]

    for order in orders:
        creation_str = format_order_time(order["creation_time"], timezone="Europe/Moscow")
        st.write(f"**Заказ #{order['order_id']}** | Статус: {order['status']} ")
        st.write(f"Создан: {creation_str}, сумма: {order['total_price']}")
        st.write("Состав заказа:")
        for item in order["items"]:
            st.write(f"- {item['name']} x {item['quantity']} (цена за ед.: {item['unit_price']})")

        current_status = order["status"]
        default_idx = 0
        if current_status in possible_statuses:
            default_idx = possible_statuses.index(current_status)

        new_status = st.selectbox(
            f"Изменить статус заказа",
            possible_statuses,
            index=default_idx,
            key=f"select_status_{order['order_id']}"
        )

        if st.button(f"Сохранить статус заказа ", key=f"save_status_{order['order_id']}"):
            payload = {"status": new_status}
            patch_resp = requests.patch(
                f"{URL_ORDERS}/orders/{order['order_id']}/status",
                json=payload,
                headers=headers
            )
            if patch_resp.status_code == 200:
                st.success("Статус заказа обновлён!")
                st.experimental_rerun()
            else:
                st.error(f"Ошибка изменения статуса: {patch_resp.text}")

        st.write("---")


# ------------------- Функции для категорий -------------------

def fetch_categories(headers):
    """
    Делаем GET /categories, возвращаем список словарей [{category_id, name}, ...].
    Если не 200 -> [] (или None).
    """
    resp = requests.get(f"{URL_PRODUCTS}/categories", headers=headers)
    if resp.status_code == 200:
        return resp.json()
    else:
        return []


def get_category_name(category_id: int, headers) -> str:
    """
    Делаем GET /categories/{category_id}, возвращаем name (строку).
    Если нет, возвращаем "Неизвестно".
    """
    url = f"{URL_PRODUCTS}/categories/{category_id}"
    resp = requests.get(url, headers=headers)
    if resp.status_code == 200:
        data = resp.json()  # { "category_id":..., "name":... }
        return data.get("name", "???")
    else:
        return "Неизвестно"


def format_order_time(iso_dt: str, timezone: str = "Europe/Moscow") -> str:
    """
    Парсит ISO-дату (например, 2024-12-27T00:41:24.035201Z) и возвращает 
    её в локальном часовом поясе в формате 27.12.2024 03:41:24.
    """
    # Парсим строку ISO 8601
    dt = parser.isoparse(iso_dt)  # dt — в UTC
    # Переводим в локальный часовой пояс (при желании)
    local_tz = pytz.timezone(timezone)
    dt_local = dt.astimezone(local_tz)
    # Преобразуем в строку
    return dt_local.strftime("%d.%m.%Y %H:%M:%S")


# -------------------------------------------------------------
# Запуск приложения
if __name__ == "__main__":
    main()
