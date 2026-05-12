# Overview — Arquitetura

Backend FastAPI de gestão de distribuição de laticínios (pontos de venda → pedidos → retiradas/outbound). Cliente principal é um app Flutter.

## Stack

| Componente | Versão / Lib |
|---|---|
| Framework | FastAPI 0.128.1 |
| ORM | SQLAlchemy 2.0.46 |
| Migrations | Alembic 1.18.3 |
| Validação | Pydantic v2 (`ConfigDict(from_attributes=True)`) |
| Auth | PyJWT 2.11.0 + pwdlib 0.3.0 (bcrypt) |
| Config | python-decouple 3.8 |
| BD (dev) | SQLite (`database/dairy_database.db`) |
| Timezone | America/Sao_Paulo |

## Estrutura de diretórios

```
app/
├── main.py                      # entrypoint: cria app, registra routers, CORS
├── model.py                     # 7 models SQLAlchemy + Base
├── dependecies.py               # make_session (typo: dependecies → dependencies)
├── exceptions.py                # ExpiredTokenException
├── sales_points/                # domínio: pontos de venda + auth
│   ├── auth_routes.py           # 11 endpoints (login + CRUD + sub-recursos)
│   ├── sale_point_controller.py
│   ├── sale_point_service.py
│   ├── sale_point_dependencies.py   # validate_token, oauth2_scheme
│   ├── sale_point_schema.py
│   └── sale_point_exceptions.py
├── orders/                      # domínio: pedidos
├── products/                    # domínio: catálogo
└── outbounds/                   # domínio: retiradas (saída de estoque)
alembic/
├── env.py                       # importa Base de app.model
└── versions/                    # 6 migrations
```

## Convenções

**Camadas por módulo:** `routes → controller → service → model`
- `*_routes.py` — endpoints FastAPI, injeção de dependências
- `*_controller.py` — adapta exceções de domínio para `HTTPException`
- `*_service.py` — regra de negócio + queries SQLAlchemy
- `*_schema.py` — DTOs Pydantic (sufixo `RequestDTO` / `ResponseDTO`)
- `*_exceptions.py` — exceções de domínio

**Auth:** `oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")` em `app/sales_points/sale_point_dependencies.py`. Logout via blacklist na tabela `tokens`.

**DTOs Pydantic v2:** `ConfigDict(from_attributes=True, populate_by_name=True)` para mapear ORM → JSON com aliases.

## Pontos de atenção / inconsistências

Itens identificados pela análise inicial — candidatos a ADR ou refactor.

1. **Roteamento concentrado em `auth_routes.py`** — 11 endpoints misturando auth, criação de orders (`POST /auth/{id}/order`) e outbounds (`POST /auth/{id}/outbounds`). Quebra coesão por domínio.
2. **Imports relativos sem prefixo `app.`** em `app/main.py:2-5` (`from sales_points.auth_routes import ...`). Funciona porque o servidor é iniciado de dentro de `app/`, mas atrapalha testes e portabilidade.
3. **CORS aberto demais.** `app/main.py:25` define `allow_origins=["*"]`, sobrescrevendo a lista `origins` (linhas 14–21) que está como dead code. Em produção, usar a lista nominal.
4. **Typo em arquivo:** `app/dependecies.py` (correto: `dependencies.py`).
5. **Typo em env var:** `.env_example` declara `ALGORTITHM` (deveria ser `ALGORITHM`). Verificar se `config('ALGORITHM')` realmente bate com o que o `.env` tem.
6. **Naming inconsistente de exceções:** `ProductExceptions.py` (PascalCase) vs `order_exceptions.py` / `outbound_exceptions.py` (snake_case).
7. **Session management inconsistente:** alguns services chamam `.close()` no fim (ex: `product_service.py:244`); outros confiam no dependency. Risco de conexões abertas se exceção sobe.
8. **Validações declaradas e não chamadas / referenciadas e não definidas:**
   - `validate_product()` existe em `product_service.py` mas não é invocada em `create_product_service`
   - `validate_item_order_request()` referenciada em `order_service.py:24` — verificar se está definida
9. **Modelo `RetiradaProduto.set_remaining_quantity`** (`app/model.py:133`) — método setter sem decorator `@property.setter`.

## Próximos passos sugeridos

- ADR-0001: registro do uso de ADRs (este repo)
- ADR-0002: padronização do roteamento por domínio (mover sub-recursos de `auth_routes` para módulos próprios)
- ADR-0003: política de CORS para produção
