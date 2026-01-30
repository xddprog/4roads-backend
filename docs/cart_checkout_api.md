# Cart & Checkout API (v1)

Base URL: `/api/v1`

## Notes
- Cart is stored in cookie-based session (`SessionMiddleware`).
- Frontend must send cookies: `fetch(..., { credentials: "include" })`.
- If frontend and backend are on different domains, cookies may not be sent because `SameSite=Lax` by default. In that case, we must adjust SessionMiddleware to `same_site="none"` and `https_only=True`.

## Cart

### Get cart
`GET /cart`

Response 200:
```json
{
  "items": [
    {
      "product_id": "UUID",
      "name": "Товар",
      "unit_price": 1000,
      "quantity": 2,
      "total_price": 2000
    }
  ],
  "total_amount": 2000
}
```

### Add item
`POST /cart/items`

Body:
```json
{ "product_id": "UUID", "quantity": 1 }
```

Responses:
- 200: CartModel (same as GET)
- 404: `{"detail":"Товар не найден"}`

### Set item quantity
`PATCH /cart/items/{product_id}`

Body:
```json
{ "quantity": 3 }
```

Notes:
- `quantity=0` removes item.

Responses:
- 200: CartModel
- 404: `{"detail":"Товара нет в корзине"}`

### Remove item
`DELETE /cart/items/{product_id}`

Responses:
- 200: CartModel
- 404: `{"detail":"Товара нет в корзине"}`

### Clear cart
`DELETE /cart`

Response 200:
```json
{ "items": [], "total_amount": 0 }
```

## Checkout

### Create order from cart
`POST /cart/checkout`

Body:
```json
{
  "name": "Иван",
  "phone": "+79001234567",
  "email": "ivan@example.com",
  "comment": "Позвонить заранее"
}
```

Responses:
- 201: OrderModel
- 400: `{"detail":"Корзина пуста"}`

OrderModel example:
```json
{
  "id": "UUID",
  "name": "Иван",
  "phone": "+79001234567",
  "email": "ivan@example.com",
  "comment": "Позвонить заранее",
  "status": "Новая",
  "total_amount": 2000,
  "created_at": "2026-01-30T12:00:00+00:00",
  "items": [
    {
      "id": "UUID",
      "product_id": "UUID",
      "product_name": "Товар",
      "unit_price": 1000,
      "quantity": 2,
      "total_price": 2000
    }
  ]
}
```

## Direct order (optional)

### Create order without using cart
`POST /order`

Body:
```json
{
  "name": "Иван",
  "phone": "+79001234567",
  "email": "ivan@example.com",
  "comment": "Позвонить заранее",
  "items": [
    { "product_id": "UUID", "quantity": 2 }
  ]
}
```

Responses:
- 201: OrderModel
- 404: `{"detail":"Товары не найдены: ..."}`
