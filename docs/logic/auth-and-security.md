# Autenticação & Segurança

Referência para o time mobile (Flutter) implementar o cliente HTTP, e para o time backend manter consistência.

## Fluxo de Login (passo-a-passo Flutter)

1. Usuário informa **username** (= `name` do sales point) e **password**.
2. Cliente envia `POST /auth/login` em `application/x-www-form-urlencoded` (formato exigido pelo `OAuth2PasswordRequestForm`):
   ```
   POST /auth/login
   Content-Type: application/x-www-form-urlencoded

   username=<name>&password=<password>
   ```
3. Backend (handler em `app/sales_points/auth_routes.py:98-101`):
   - Busca sales point por `name`
   - Verifica hash da senha (pwdlib/bcrypt)
   - Gera JWT com `sub = sale_point.id`, `exp = now + EXPIRE_TIME_TOKEN`
4. Resposta:
   ```json
   {
     "access_token": "eyJhbGciOiJIUzI1NiIs...",
     "token_type": "bearer"
   }
   ```
   **Status: 201 Created** (não-padrão para login — tipicamente 200; verificar se o time backend pretende padronizar).
5. Cliente armazena o token em **Flutter Secure Storage** (não em SharedPreferences — o token é credencial).
6. Em requisições subsequentes:
   ```
   Authorization: Bearer <access_token>
   ```

### Erros possíveis
- `404` → sales point com aquele `name` não existe (`SalePointNotFound`)
- `401` → senha inválida

## Token JWT

Geração: `app/sales_points/sale_point_service.py:38-52`
- **Lib:** PyJWT 2.11.0
- **Algoritmo:** definido em `ALGORITHM` env var (HS256 esperado)
- **Claims:** `sub` (sale_point.id), `exp` (UTC com tz `America/Sao_Paulo`)
- **Secret:** `config('SECRET_KEY')` via python-decouple
- **Expiração:** `EXPIRE_TIME_TOKEN` (em minutos)

Validação: `app/sales_points/sale_point_dependencies.py:14-31` (`validate_token`)
1. Extrai token do header `Authorization` (via `OAuth2PasswordBearer`)
2. Decodifica com `SECRET_KEY` e `ALGORITHM`
3. Verifica se sales point ainda existe no BD
4. Verifica se o token **não está na blacklist** (tabela `tokens`)
5. Retorna o dict de claims; rotas protegidas recebem como `user`

### Logout
`POST /auth/logout` (`auth_routes.py:104-111`) — insere o token atual na tabela `tokens` (blacklist). Próximas chamadas com esse token são rejeitadas.

> Em produção considerar Redis (TTL = exp do token) para evitar crescimento indefinido da tabela.

## Hashing de senha

`pwdlib` 0.3.0 (`app/sales_points/sale_point_service.py:4`)
```python
pwd_context = PasswordHash.recommended()  # bcrypt
pwd_context.hash(password)                # criação
pwd_context.verify(password, hash)        # login
```

## Proteção de rotas

```python
@router.get("/...")
async def handler(user = Depends(validate_token), session = Depends(make_session)):
    # user é dict {'sub': '<id>', 'exp': <timestamp>}
    ...
```

Quase todos os endpoints exigem `validate_token`. Exceções públicas atualmente:
- `POST /auth/login` (correto)
- `POST /auth/` (criar sales point — **revisar se deveria ser admin-only**)
- `GET /products/` (lista de produtos — **revisar se intencional**)

## CORS

`app/main.py:23-30`

⚠️ **Configuração atual permite todas as origens:**
```python
allow_origins=["*"]
allow_credentials=True
allow_methods=["*"]
allow_headers=["*"]
```

A lista nominal `origins = [...]` em `main.py:14-21` (com `localhost:5173/8080/58000`) **está como dead code** — não é referenciada no `add_middleware`.

**Recomendado para produção:**
- Trocar `["*"]` pela lista nominal
- Definir explicitamente os métodos usados (`GET POST PATCH DELETE`)
- `allow_credentials=True` é incompatível com `allow_origins=["*"]` em alguns clientes — outra razão para fechar

## Variáveis de ambiente

`.env_example`:

| Variável | Propósito | Notas |
|---|---|---|
| `SECRET_KEY` | Assina o JWT (HMAC) | Mínimo 32 bytes recomendado, gerar via `secrets.token_urlsafe(32)` |
| `EXPIRE_TIME_TOKEN` | Tempo de expiração do token (minutos) | Inteiro |
| `ALGORTITHM` ⚠️ | Algoritmo JWT (ex: `HS256`) | **Typo no `.env_example`** — falta um `I`. Verificar se o código lê `ALGORITHM` (correto) ou `ALGORTITHM` (errado) — se ler o errado, é fonte de bug latente |

Carregamento via `from decouple import config; config('SECRET_KEY')`.

## Pontos de atenção

1. **Status code do login** = 201 (não-convencional; mobile precisa tratar)
2. **CORS aberto** em desenvolvimento — fechar antes de produção
3. **`ALGORTITHM` typo** no `.env_example` — auditar onde é lido no código
4. **Sem refresh token** — após `EXPIRE_TIME_TOKEN`, usuário precisa re-logar
5. **Validação no startup** — não há check que `SECRET_KEY` não está vazio; falha silenciosamente
6. **Endpoints públicos não-óbvios** — `POST /auth/`, `GET /products/`. Revisar intenção.
7. **HTTPS** — obrigatório em produção (token e senha trafegam em headers/body)
