# Inventário de Endpoints

Referência para integração do cliente Flutter. Atualize sempre que rotas/payloads mudarem.

> **Convenções**
> - Auth: header `Authorization: Bearer <token>` (obtido em `POST /auth/login`)
> - `validate_token` = dependency obrigatória (rota protegida)
> - `make_session` = injeção de sessão SQLAlchemy
> - Datas em ISO-8601, timezone `America/Sao_Paulo`

---

## Auth & Sales Points

Arquivo: `app/sales_points/auth_routes.py`

### POST `/auth/login`
Autenticação. **Público.**
- **Body** (`application/x-www-form-urlencoded`): `username`, `password` (`OAuth2PasswordRequestForm`)
- **Response 201**: `{ "access_token": "<jwt>", "token_type": "bearer" }`
- **Erros**: 404 (usuário inexistente), 401 (senha inválida)
- Handler: `auth_routes.py:98-101`

### POST `/auth/logout`
Revoga o token atual (insere em tabela `tokens`).
- **Header**: `Authorization: Bearer <token>`
- **Response 204**: sem body
- Handler: `auth_routes.py:104-111`

### GET `/auth/`
Lista todos os sales points. Protegido.
- **Response 200**: `SalePointResponseDTO[]` → `[{ id, name, email }]`
- Handler: `auth_routes.py:15-17`

### POST `/auth/`
Cria sales point. **Atualmente público** (verificar se intencional).
- **Query**: `name`, `password`, `email?`
- **Response 201**: `SalePointResponseDTO`
- **Erros**: 409 (`ExistingSalePointException`)
- Handler: `auth_routes.py:20-23`

### DELETE `/auth/`
Apaga **todos** os sales points (cascade). Protegido.
- **Response 200**: `{ "message": "Sales points excluded" }`
- Handler: `auth_routes.py:26-29`
- ⚠️ Operação destrutiva — considerar restringir a admin.

### GET `/auth/{id}`
- **Response 200**: `SalePointResponseDTO`
- **Erros**: 404
- Handler: `auth_routes.py:32-35`

### DELETE `/auth/{id}`
Cascata em orders e retiradas associadas.
- **Response 200**: `{ "sale point deleted": SalePointResponseDTO }`
- Handler: `auth_routes.py:38-46`

---

## Orders (vinculados ao sales point)

### GET `/auth/{id}/order`
Pedidos de um sales point. Filtro opcional por data.
- **Query**: `date?` (ISO date)
- **Response 200**: `{ "sale_point_id": int, "orders": OrderResponseDTO[] }`
- Handler: `auth_routes.py:49-57`

### POST `/auth/{id}/order`
Cria pedido para um sales point.
- **Body** (`OrderRequestDTO`):
  ```json
  {
    "description": "string?",
    "status": "bool?",
    "total_value": "float?",
    "order_date": "date?",
    "items": [
      { "product_id": 1, "amount": 0, "kg": 0.0, "liters": 0.0 }
    ]
  }
  ```
- **Response 201**: `OrderResponseDTO`
- **Erros**: 409 (`InsuficientProductsAmountException`)
- Handler: `auth_routes.py:60-63`

### DELETE `/auth/{id}/order`
Remove todos os pedidos do sales point.
- Handler: `auth_routes.py:66-68`

---

## Orders (CRUD genérico)

Arquivo: `app/orders/order_routes.py`

### GET `/pedidos/`
Lista pedidos com filtros.
- **Query**: `date?`, `description?`, `status?`
- **Response 200**: `OrderResponseDTO[]`
  ```json
  [{
    "id": 1,
    "status": true,
    "total_value": 0.0,
    "description": "string?",
    "date": "datetime",
    "sale_point_id": 1,
    "item_order": [
      { "product_id": 1, "name": "string", "price": 0.0,
        "amount": 0, "kg": 0.0, "liters": 0.0 }
    ]
  }]
  ```
- Handler: `order_routes.py:9-12`

### GET `/pedidos/{id}` — Handler: `order_routes.py:14-17`
### PATCH `/pedidos/{id}`
- **Body**: `OrderRequestDTO`
- Handler: `order_routes.py:20-22`
### DELETE `/pedidos/{id}` — Handler: `order_routes.py:25-28`
### DELETE `/pedidos/` — Response 204. Handler: `order_routes.py:30-33`

---

## Products

Arquivo: `app/products/product_routes.py`

### GET `/products/`
**Público** (sem `validate_token`). Verificar se é intencional.
- **Response 200**: `ProductResponseDTO[]` → `[{ id, name, price, amount, kg, liters }]`
- Handler: `product_routes.py:11-14`

### POST `/products/`
- **Query**: `name`, `price`, `amount?`, `kg?`, `liters?`
- **Response 201**: `ProductResponseDTO`
- **Erros**: 409 (`ExistingProductException`)
- Handler: `product_routes.py:17-20`

### GET `/products/{id}` — Handler: `product_routes.py:29-32`
### PATCH `/products/{id}`
- **Body**: `ProductRequestDTO` (todos campos opcionais)
- Handler: `product_routes.py:35-38`
### DELETE `/products/{id}` — Handler: `product_routes.py:23-26`
### DELETE `/products/` — Response 204. Handler: `product_routes.py:41-44`

---

## Outbounds (Retiradas — núcleo do domínio)

### GET `/auth/{id}/outbounds`
Retiradas de um sales point. Filtro por data.
- **Query**: `date?`
- **Response 200**: `ItemsRetiradaResponseDTO[]`
  ```json
  [{
    "id": 1,
    "sale_point_id": 1,
    "product_id": 1,
    "name": "string?",
    "status": true,
    "date": "datetime",
    "unit_type": "kg|litros|unidade",
    "taken_quantity": 0.0,
    "sold_quantity": 0.0,
    "remaining_quantity": 0.0,
    "total_value_item": 0.0,
    "observation": "string?"
  }]
  ```
- Handler: `auth_routes.py:71-74`

### POST `/auth/{id}/outbounds`
Cria retirada (saída de estoque em consignação).
- **Body** (`RetirarProdutosRequestDTO`):
  ```json
  {
    "produtos": [
      { "product_id": 1, "quantidade": 0.0, "unidade": "kg" }
    ],
    "observacao": "string?"
  }
  ```
- **Response 201**: detalhes da retirada
- **Erros**: 404 (sale point inexistente), 500 (erro interno)
- Handler: `auth_routes.py:77-85`

### DELETE `/auth/{id}/outbounds` — Handler: `auth_routes.py:88-90`

### PATCH `/auth/{id}/outbounds`
Reconcilia/retorna outbounds do sales point.
- Handler: `auth_routes.py:93-95`

### PATCH `/outbounds/{id}`
Edita campos individuais. Body: `OutboundRequestDTO`.
- Arquivo: `app/outbounds/outbound_routes.py:9-12`

### PATCH `/outbounds/{id}/quantity`
Atualiza quantidade vendida; recalcula `remaining_quantity`.
- **Query**: `quantity` (int)
- Arquivo: `app/outbounds/outbound_routes.py:14-16`

---

## Status codes em uso

| Code | Uso |
|---|---|
| 200 | GET / PATCH bem-sucedidos |
| 201 | POST (criação) — incluindo `/auth/login` |
| 204 | DELETE bem-sucedido sem body |
| 400 | Erro genérico de validação/processamento |
| 401 | Senha inválida |
| 404 | Recurso não encontrado |
| 409 | Conflito (recurso duplicado, estoque insuficiente) |
| 500 | Erro interno (outbound) |

> **Observação para o time mobile:** `POST /auth/login` retorna **201** (não 200). Trate ambos no cliente HTTP do Flutter, ou padronize 200 do lado do backend (vide histórico recente: `5f802b1 fix: login endpoint`, `94b4d0b refactor: endpoints' response status code`).
