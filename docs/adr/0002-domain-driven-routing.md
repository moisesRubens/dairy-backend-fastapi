# ADR-0002 — Reorganização do roteamento por domínio

- **Status:** Proposto
- **Data:** 2026-05-05 (atualizado 2026-05-07 após ADR-0004)
- **Relacionado:** ADR-0001, ADR-0004 (idioma pt-BR)

> **Atualização (2026-05-07):** os exemplos originais usavam paths em inglês (`/sales-points`, `/orders`, `/products`, `/outbounds`). Após **ADR-0004** que define pt-BR como idioma do domínio, os paths corretos são `/filiais`, `/pedidos`, `/produtos`, `/movimentos-estoque`. A tabela e o mapeamento abaixo refletem o estado pós-ADR-0004.

## Contexto

Hoje `app/sales_points/auth_routes.py` concentra **11 endpoints** que pertencem a três domínios distintos:

| Path atual | Domínio real | Handler em `auth_routes.py` |
|---|---|---|
| `POST /auth/login` | Auth | `:98` |
| `POST /auth/logout` | Auth | `:104` |
| `GET/POST/DELETE /auth/` + `GET/DELETE /auth/{id}` | Sales Points (CRUD) | `:15`, `:20`, `:26`, `:32`, `:38` |
| `GET/POST/DELETE /auth/{id}/order` | **Orders** | `:49`, `:60`, `:66` |
| `GET/POST/DELETE/PATCH /auth/{id}/outbounds` | **Outbounds** | `:71`, `:77`, `:88`, `:93` |

Isso traz três problemas:

1. **Quebra de coesão.** Mudar como pedidos são criados exige mexer no router de auth — qualquer pessoa do time mobile que procura "POST de pedido" vai ao lugar errado.
2. **Semântica do prefixo `/auth` está sobrecarregada.** `/auth/{id}/outbounds` lê como "operação de autenticação", mas é uma operação de estoque.
3. **Documentação OpenAPI confusa.** No `/docs` gerado pelo FastAPI, esses endpoints aparecem todos sob a mesma tag, dificultando navegação para o cliente Flutter.

Adicionalmente, há **duplicação de caminho para o mesmo recurso**: pedidos hoje têm rota tanto em `/pedidos/*` (CRUD genérico, em PT) quanto em `/auth/{id}/order` (criação vinculada). Outbounds têm `/auth/{id}/outbounds` e `/outbounds/{id}` — convivência funcional, mas inconsistente em nomenclatura (PT/EN, plural/singular).

## Decisão

Reorganizar o roteamento em **um router por domínio**, com prefixos consistentes em pt-BR e plural:

| Router | Prefix | Tag OpenAPI |
|---|---|---|
| `auth_router` | `/auth` | Auth |
| `filiais_router` | `/filiais` | Filiais |
| `operadores_router` | `/operadores` | Operadores |
| `clientes_router` | `/clientes` | Clientes |
| `pedidos_router` | `/pedidos` | Pedidos |
| `produtos_router` | `/produtos` | Produtos |
| `movimentos_estoque_router` | `/movimentos-estoque` | Movimentos de Estoque |

> Vendas, pagamentos, caixas, lotes, etc. ganham routers próprios conforme as ADRs subsequentes (estoque, PDV, fidelidade) os introduzem.

### Mapeamento de paths (atual → novo)

**Auth (mantém — termo técnico universal)**
- `POST /auth/login` → `POST /auth/login`
- `POST /auth/logout` → `POST /auth/logout`

**Filiais (move e renomeia — vide ADR-0003)**
- `GET /auth/` → `GET /filiais/`
- `POST /auth/` → `POST /filiais/` *(criação de filial é separada de criação de operador — ver ADR-0003)*
- `DELETE /auth/` → `DELETE /filiais/`
- `GET /auth/{id}` → `GET /filiais/{id}`
- `DELETE /auth/{id}` → `DELETE /filiais/{id}`

**Pedidos (move sub-recursos para `pedidos_router`; consolida)**
- `GET /auth/{id}/order` → `GET /pedidos/?filial_id={id}` (filtro)
- `POST /auth/{id}/order` → `POST /pedidos/?filial_id={id}` (ou no body)
- `DELETE /auth/{id}/order` → `DELETE /pedidos/?filial_id={id}`
- `GET /pedidos/...` → mantém (já estava em pt-BR)

**Movimentos de estoque (substitui `/outbounds` — vide ADR-0005 estoque ledger)**
- `GET /auth/{id}/outbounds` → `GET /movimentos-estoque/?filial_id={id}`
- `POST /auth/{id}/outbounds` → `POST /movimentos-estoque/?filial_id={id}`
- `DELETE /auth/{id}/outbounds` → `DELETE /movimentos-estoque/?filial_id={id}`
- `PATCH /auth/{id}/outbounds` → `POST /movimentos-estoque/devolucao?filial_id={id}` (ação explícita)
- `PATCH /outbounds/{id}` → `PATCH /movimentos-estoque/{id}`
- `PATCH /outbounds/{id}/quantity` → `PATCH /movimentos-estoque/{id}/quantidade`

### Convenções estabelecidas

1. **Idioma:** todos os paths em **pt-BR**, no **plural**, **kebab-case** (vide ADR-0004 e [`docs/logic/glossario.md`](../logic/glossario.md)). Exceção: `/auth` (termo técnico universal).
2. **Vínculo a filial:** via query param `?filial_id=<id>` em vez de path nesting (`/auth/{id}/...`). Filtro/escopo é função natural de query, não de path.
3. **Ações que não são CRUD** (ex: "devolução de movimento") usam sub-path com verbo no nome do recurso: `POST /movimentos-estoque/devolucao`. Evita misturar `PATCH` semântico com ação de domínio.
4. **Tags OpenAPI** explícitas no `APIRouter(tags=[...])` para agrupar no `/docs`.
5. **Versionamento:** considerar prefixo `/v1/...` na implementação, abrindo caminho pra `/v2/...` futuro sem partir cliente.

## Estratégia de migração (mobile-friendly)

O cliente Flutter está em desenvolvimento ativo — não dá pra simplesmente quebrar.

**Fase 1 — Aditiva (sem breaking change)**
- Criar os novos paths em paralelo aos atuais
- Novos paths chamam exatamente os mesmos `*_controller`/`*_service`
- Atualizar `docs/api/endpoints.md` listando ambos, marcando os antigos como `[deprecated]`

**Fase 2 — Migração do cliente**
- Time Flutter aponta o cliente HTTP para os novos paths
- Tag de release no app indicando "usa API v2"

**Fase 3 — Remoção**
- Após N releases (combinar com mobile), remover os paths antigos
- Criar ADR de "encerramento" referenciando este

## Alternativas consideradas

**A) Não mexer (status quo).** Custo zero hoje, mas dívida cresce a cada novo recurso vinculado a sales point. Rejeitado.

**B) Manter nesting `/auth/{id}/...` e só mover para o router certo.** Resolve coesão de código mas mantém a sobrecarga semântica de `/auth`. Rejeitado por meio termo.

**C) Refactor completo de uma vez (sem fase aditiva).** Mais limpo mas quebra cliente Flutter sem aviso. Rejeitado.

## Consequências

**Positivas**
- Cada router tem responsabilidade única e arquivo previsível para mudanças futuras.
- OpenAPI fica limpo, melhor onboarding pro time mobile.
- Caminho preparado para versionamento (`/v2/...`) se necessário.
- Remove duplicação `/pedidos` vs `/auth/{id}/order`.

**Negativas**
- Mudança de paths é breaking change — exige coordenação com mobile.
- Período de Fase 1 dobra a superfície da API temporariamente.
- Time backend precisa lembrar de manter os dois caminhos sincronizados durante a transição.

**Neutras**
- Não muda lógica de negócio, modelos ou banco.
- Não muda autenticação/autorização das rotas (cada path migrado mantém suas dependencies).

## Critério de aceite

Esta ADR é considerada **implementada** quando:
- [ ] Todos os endpoints da Fase 1 existem nos novos paths
- [ ] `docs/api/endpoints.md` reflete o estado dual
- [ ] Cliente Flutter migrou (Fase 2)
- [ ] Paths antigos foram removidos (Fase 3)
- [ ] ADR de encerramento criado referenciando este número
