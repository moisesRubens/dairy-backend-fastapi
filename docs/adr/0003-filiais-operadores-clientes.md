# ADR-0003 — SalePoint como filial: separação de Filial, Operador e Cliente

- **Status:** Proposto
- **Data:** 2026-05-07 (atualizado após ADR-0004)
- **Relacionado:** ADR-0001, ADR-0002, ADR-0004 (idioma pt-BR)
- **Referências:** [`docs/logic/architecture-laticinios.md`](../logic/architecture-laticinios.md), [`docs/logic/flutter-client-analysis.md`](../logic/flutter-client-analysis.md), [`docs/logic/glossario.md`](../logic/glossario.md)

## Contexto

A entidade `SalePoints` no modelo atual carrega **três responsabilidades** de conceitos distintos:

1. **Filial física** — onde o estoque vive e onde acontece a venda balcão.
2. **Credencial de login** — `username` + `password` armazenados na própria tabela `sales_points`.
3. **Cliente B2B** — herança do desenho original em consignação, **incompatível com o escopo escolhido** ([`architecture-laticinios.md`](../logic/architecture-laticinios.md)): dono único com filiais próprias, sem terceiros.

O modelo atual também **não possui** entidade `Cliente` (consumidor final), o que bloqueia:
- PDV minimamente sério (identificação opcional do comprador para histórico, garantia, fidelidade)
- Programa de fidelidade futuro (titular da `ContaFidelidade`)
- Marketing/CRM (aniversários, recompra, segmentação)

A análise do repositório Flutter ([`flutter-client-analysis.md`](../logic/flutter-client-analysis.md)) confirma que **o operador da filial é o usuário do app** — não o dono nem o cliente final — reforçando que credencial de login é propriedade de **pessoa**, não de **lugar**.

## Decisão

Decompor `SalePoints` em **três entidades** com responsabilidades únicas, todas em pt-BR (conforme ADR-0004):

### Filial
Sucessora de `SalePoints`. Representa o **lugar físico**.

| Atributo | Tipo | Notas |
|---|---|---|
| `id` | int (PK) | |
| `nome` | string(100) | |
| `endereco` | string(200), nullable | adicionado na migration |
| `telefone` | string(20), nullable | adicionado na migration |
| `created_at` / `updated_at` | datetime | timestamps padrão (inglês — ADR-0004 §"em inglês") |

**Sem credencial de login.** Sem `senha`. Sem `email` (esses migram para `Operador`).

Tabela: `filiais` (renomeada de `sales_points`).

### Operador
**Pessoa física** que opera o sistema dentro de uma filial.

| Atributo | Tipo | Notas |
|---|---|---|
| `id` | int (PK) | |
| `nome` | string(100) | |
| `username` | string(50), unique | usado em `POST /auth/login` |
| `senha_hash` | string | bcrypt via pwdlib |
| `email` | string(200), nullable | |
| `filial_id` | FK → filiais | filial onde opera atualmente |
| `papel` | enum: `caixa`, `gerente`, `dono` | default `caixa` |
| `ativo` | bool, default true | desativar sem apagar (auditoria) |
| `created_at` / `updated_at` | datetime | |

**Login passa a ser por `Operador`.** Token JWT carrega `operador_id`, `filial_id`, `papel`.

Tabela: `operadores`.

### Cliente
**Pessoa física** que compra na filial. Sem login.

| Atributo | Tipo | Notas |
|---|---|---|
| `id` | int (PK) | |
| `cpf` | string(14), unique, nullable | identificador opcional |
| `nome` | string(100) | |
| `telefone` | string(20), nullable | |
| `email` | string(200), nullable | |
| `data_nascimento` | date, nullable | aniversário → fidelidade futura |
| `consentimento_dado_em` | datetime, nullable | LGPD: registro do consentimento |
| `created_at` / `updated_at` | datetime | |

Tabela: `clientes`.

> **LGPD:** `Cliente` armazena dado pessoal. Coleta exige consentimento informado (UI do PDV pede explicitamente). Direito ao esquecimento via `anonimizado_em` ou similar em ADR futura, quando aplicável.

## Mudanças derivadas

### Schema (Alembic)

Migration única e ordenada (não-reversível na prática se houver dado em produção):

1. `CREATE TABLE operadores` (vazia)
2. `CREATE TABLE clientes` (vazia)
3. `ALTER TABLE sales_points RENAME TO filiais`
4. `ALTER TABLE filiais` — renomear `name` → `nome`; adicionar `endereco`, `telefone`, `created_at`, `updated_at`
5. **Backfill de operadores:** para cada `filial` existente, criar 1 `operador` com:
   - `username` = `filial.nome` slugificado
   - `senha_hash` = `filial.password` (já está hasheado — só copia)
   - `email` = `filial.email`
   - `filial_id` = `filial.id`
   - `papel` = `gerente`
6. `ALTER TABLE filiais DROP COLUMN password, email` (já migraram pra operador)
7. Renomear FKs:
   - `retiradas_produto.sale_point_id` → `filial_id`
   - `order_sale_point.sale_point_id` → `filial_id`
8. Renomear tabelas em inglês legadas (parte de ADR-0004): `orders` → `pedidos`, `products` → `produtos`, `item_order` → `itens_pedido`, `order_sale_point` → `pedidos_filial` (ou similar — definir na implementação). Colunas internas seguem glossário.

> A migration desta ADR e da renomeação geral de ADR-0004 vão **juntas** porque coexistem na mesma janela de break — não vale dois `v0.x` consecutivos quebrando o cliente.

### Endpoints afetados

| Endpoint atual | Mudança |
|---|---|
| `POST /auth/login` | valida credenciais em `operadores` (não mais em `filiais`) |
| `POST /auth/login` resposta | passa a incluir `filial_id`, `papel` no payload, além de `access_token` |
| `validate_token` | retorna `{operador_id, filial_id, papel}` |
| Todas rotas com `sale_point_id` | parâmetro renomeado para `filial_id` |
| (após ADR-0002) `POST /sales-points/` | desaparece — vira `POST /filiais/` (filial) e `POST /operadores/` (operador), separados |
| (novo) `POST /clientes/` | criação de cliente — payload e regras detalhados em ADR de fidelidade futura |

### Permissões (esboço — detalhar em ADR futura)

- `caixa`: vê e opera só a própria filial
- `gerente`: gerencia operadores e estoque da filial; relatórios da filial
- `dono`: tudo (consolidado entre filiais, criar/desativar filiais e operadores)

`validate_token` extrai `papel` e expõe via dependency `requer_papel(...)` nas rotas.

## Alternativas consideradas

**A) Manter `SalePoints` como está e adicionar `Cliente`.** Resolve ausência do consumidor final mas mantém credencial de login no nível da filial — impede dois operadores na mesma filial sem confusão, e impede auditoria por pessoa. **Rejeitado.**

**B) Só `Filial + Cliente`, sem `Operador`.** Login continua "da filial" (1 conta por filial). Funciona pra MVP com 1 funcionário por filial. **Rejeitado** porque o doc do dono em `pdv-mobile.md` trata operador como entidade implícita ("design para o vendedor"), e PDV real exige troca de turno e auditoria por pessoa.

**C) `Filial + Operador + Cliente` (esta).** Cada conceito carrega 1 responsabilidade. Custo de migração razoável (uma migration ordenada). **Aceito.**

**D) Adiar tudo e implementar fidelidade depois sem refactor agora.** Levaria a reescrever metade dos endpoints quando vier ADR de fidelidade. **Rejeitado** — o custo da decomposição agora é o mesmo, e destrava ADRs subsequentes.

## Consequências

**Positivas**
- Modelo mental alinhado com a realidade: filial é lugar, operador é pessoa, cliente é cliente.
- Destrava ADRs seguintes (estoque por filial, fidelidade, PDV).
- Auditoria por operador (cada `Venda` referencia `operador_id`).
- Operadores podem trocar de filial (`UPDATE operadores SET filial_id = ...`) sem perder histórico passado.
- Papéis (`caixa`, `gerente`, `dono`) abrem caminho para permissões granulares.

**Negativas**
- Migration toca múltiplas tabelas — risco médio. Mitigar com backup antes de rodar em produção.
- Breaking change na API: endpoints renomeados, payload de login muda. Coordena com cliente Flutter (greenfield, custo baixo).
- Documentação atual (`overview.md`, `endpoints.md`, `domain-model.md`) precisa ser atualizada após implementação.
- Combinada com ADR-0004 (renomeação geral pt-BR), a migration é grande — fazer com cuidado e testes.

**Neutras**
- Não introduz `organization_id` (single-tenant mantido).
- Não muda `Pedido` (ex-`Order`), `Produto` (ex-`Product`), `RetiradaProduto` no comportamento — esses ficam pra ADRs subsequentes (estoque ledger, unidade de medida).

## Critério de aceite

Esta ADR é considerada **implementada** quando:

- [ ] Migration Alembic criada, revisada, testada em DB de cópia
- [ ] Modelos SQLAlchemy `Filial`, `Operador`, `Cliente` em `app/model.py` (ou módulos próprios após ADR-0002)
- [ ] Schemas Pydantic correspondentes seguindo nomenclatura do glossário
- [ ] `POST /auth/login` valida `Operador` e retorna `{access_token, token_type, filial_id, papel}`
- [ ] `validate_token` retorna dict com `operador_id`, `filial_id`, `papel`
- [ ] Endpoints com filtro por `sale_point_id` migrados para `filial_id`
- [ ] [`docs/api/endpoints.md`](../api/endpoints.md) atualizado refletindo o novo contrato
- [ ] [`docs/logic/domain-model.md`](../logic/domain-model.md) atualizado (entidades + ER)
- [ ] Tag de release marcando o break (`v0.2.0`) e changelog destacando os endpoints alterados
- [ ] Issue/PR aberta no repo do Flutter avisando da mudança de contrato (ver [`docs/logic/two-repos-workflow.md`](../logic/two-repos-workflow.md))

## Pontos em aberto (não bloqueiam esta ADR)

- **`dono` é `Operador.papel = 'dono'` ou entidade separada?** Inclinação: `Operador.papel = 'dono'` por simplicidade. Decidir na implementação ou em ADR-0003.1 se ficar contencioso.
- **Identificação do cliente no PDV** (CPF / telefone / QR / cartão): definir na ADR de fidelidade.
- **Matriz completa de permissões por papel:** crescer conforme novos endpoints aparecem.
- **`senha_hash` vs `password_hash`** no schema (decisão pendente listada no [`glossario.md`](../logic/glossario.md)). Inclinação: `senha_hash` pela coerência. Decidir até a implementação.
