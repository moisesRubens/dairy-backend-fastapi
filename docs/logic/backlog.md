# Backlog de Desenvolvimento

> **Doc vivo.** Atualize conforme tasks são pegas/concluídas. Sintetiza as ADRs em ordem executável.
> **Status atual:** ADRs 0001–0005 propostas, nenhuma implementada. Backend está no estado herdado do dono (SalePoints + Order + Product em inglês).

---

## Visão geral em 6 fases

```
Fase 0 ─ Higiene do repo                          [~1 dia]
Fase 1 ─ v0.2.0: Fundação grande                  [~3-4 semanas]
        (ADR-0002 + 0003 + 0004 + 0005 juntas)
Fase 2 ─ v0.3.0: Estoque + Unidade                [~2-3 semanas]
        (ADR-0006 + 0007)
Fase 3 ─ v0.4.0: PDV                              [~3-4 semanas]
        (ADR-0009)
Fase 4 ─ v0.5.0: Fidelidade                       [~2 semanas]
        (ADR-0008)
Fase 5 ─ v1.0.0: Hardening                        [conforme demanda]
        (Fiscal, eventos, offline-first, etc.)
```

Estimativas em "semanas-dev" pra 1 dev focado. Multiplica pelo contexto real.

---

## Fase 0 — Higiene do repositório

Pequenos ajustes que não dependem de ADR. Roda em paralelo ou antes de tudo.

| ID | Task | Aceite |
|---|---|---|
| **H-001** | Adicionar `**/__pycache__/` e `*.pyc` ao `.gitignore` global | `.gitignore` cobre todas subpastas |
| **H-002** | `git rm --cached -r app/**/__pycache__/` (limpar lixo commitado) | `git status` não mostra `.pyc` |
| **H-003** | Adicionar `venv/` e `.venv/` ao `.gitignore` | Convenção consolidada |
| **H-004** | Padronizar arquivo `app/dependecies.py` → `app/dependencies.py` (typo) | Imports atualizados |
| **H-005** | Corrigir typo `ALGORTITHM` → `ALGORITHM` no `.env_example` | Documentado em `auth-and-security.md` §7 |

---

## Fase 1 — v0.2.0: Fundação grande

**Objetivo:** integrar **ADR-0002 (routing pt-BR) + 0003 (Filial/Operador/Cliente) + 0004 (idioma pt-BR) + 0005 (extension points)** numa única release. Migration única e ordenada.

**Por que junto?** As 4 tocam as mesmas tabelas e endpoints. Fazer separadamente significaria 4 breaking changes consecutivas — pior pro dono do Flutter.

### Sub-fase 1.1 — Setup de testes e CI mínimo

| ID | Task | Aceite |
|---|---|---|
| **F-101** | Configurar pytest + SQLite test DB em `tests/conftest.py` | `pytest` roda sem erro |
| **F-102** | Suite de smoke tests do estado atual (login, lista produtos, criar pedido) | Verde antes do refactor — baseline |
| **F-103** | GitHub Actions: rodar pytest em PR (job básico) | Workflow `.github/workflows/test.yml` rodando |

> Sem testes, refactor grande é roleta russa. F-101/102 são pré-requisito.

### Sub-fase 1.2 — Roteamento por domínio (ADR-0002)

| ID | Task | Aceite |
|---|---|---|
| **F-110** | Criar módulos `app/filiais/`, `app/operadores/`, `app/clientes/`, `app/pedidos/`, `app/produtos/`, `app/movimentos_estoque/`, `app/auth/` | Estrutura criada (vazia ou com router stub) |
| **F-111** | Mover `POST /auth/login`, `/auth/logout` pra `app/auth/auth_routes.py` (preservar comportamento) | Endpoint funciona idêntico |
| **F-112** | Adicionar prefix `/v1` em todos os routers | OpenAPI mostra `/v1/...` |
| **F-113** | Manter endpoints antigos como **deprecated wrappers** (redirect ou re-route pra novos) | Cliente atual não quebra durante transição |

### Sub-fase 1.3 — Migration grande (ADRs 0003 + 0004 + 0005)

| ID | Task | Aceite |
|---|---|---|
| **F-120** | Escrever Alembic migration `add_filial_operador_cliente_ptbr_extension_points` | Migration revisada, dry-run em DB de cópia OK |
| **F-121** | Renomear `sales_points` → `filiais`; adicionar `endereco`, `telefone`, `tipo` (ADR-0005), `created_at`, `updated_at`; renomear `name` → `nome` | Tabela `filiais` no schema final |
| **F-122** | Criar tabela `operadores` com `papel` enum, `branch_id` FK; backfill: 1 operador por filial existente | `operadores` populada e queryável |
| **F-123** | Criar tabela `clientes` (vazia) com CPF unique, dados pessoais opcionais, `consentimento_dado_em` | `clientes` queryável |
| **F-124** | `ALTER TABLE filiais DROP COLUMN password, email` (migraram pra operador) | Schema sem credencial em filial |
| **F-125** | Renomear `orders` → `pedidos`, `products` → `produtos`, `item_order` → `itens_pedido`, etc. (per glossário) | Schemas em pt-BR |
| **F-126** | Renomear colunas pt-BR onde aplicável (`name` → `nome`, `price` → `preco`, etc.) | Tabelas com colunas pt-BR |
| **F-127** | Adicionar `produtos.metadata` JSONB nullable (ADR-0005) | Schema final tem `metadata` |
| **F-128** | Renomear `sale_point_id` → `filial_id` em todas FKs | FKs atualizadas |

### Sub-fase 1.4 — Modelos SQLAlchemy + Pydantic

| ID | Task | Aceite |
|---|---|---|
| **F-130** | `app/model.py` (ou modularizar) — classes `Filial`, `Operador`, `Cliente`, `Produto`, `Pedido`, `ItemPedido` em pt-BR | Classes mapeiam às tabelas novas |
| **F-131** | Schemas Pydantic por módulo: `FilialCriarDTO`, `OperadorCriarDTO`, etc. — seguir sufixos do glossário | DTOs validam corretamente |
| **F-132** | `Operador.papel` como enum pt-BR (`caixa`, `gerente`, `dono`) | Enum tipado |
| **F-133** | `Produto.metadata` como `dict[str, Any]` nullable no schema Pydantic | Aceita JSON arbitrário |

### Sub-fase 1.5 — Auth refatorada

| ID | Task | Aceite |
|---|---|---|
| **F-140** | `POST /v1/auth/login` valida `Operador` (não Filial) e retorna `{access_token, token_type, filial_id, papel}` | Login funciona com operador |
| **F-141** | `validate_token` retorna `{operador_id, filial_id, papel}` | Dependency atualizada |
| **F-142** | Dependency `requer_papel('gerente', 'dono')` pra rotas administrativas | Bloqueia caixa em rotas restritas |
| **F-143** | `POST /v1/auth/logout` insere token na blacklist (mantém comportamento atual, só renomeia) | Logout funcional |

### Sub-fase 1.6 — Endpoints migrados

| ID | Task | Aceite |
|---|---|---|
| **F-150** | CRUD `Filial` em `/v1/filiais/` | GET/POST/PATCH/DELETE testados |
| **F-151** | CRUD `Operador` em `/v1/operadores/` (criar/listar/desativar; sem delete físico) | Testados |
| **F-152** | CRUD `Cliente` em `/v1/clientes/` (criar/buscar por CPF/listar/atualizar) | Testados |
| **F-153** | CRUD `Produto` em `/v1/produtos/` | Testados |
| **F-154** | CRUD `Pedido` em `/v1/pedidos/?filial_id=` | Testados |
| **F-155** | Remover endpoints velhos `/auth/{id}/order`, `/auth/{id}/outbounds` | 410 Gone ou redirect pros novos |

### Sub-fase 1.7 — Documentação e release

| ID | Task | Aceite |
|---|---|---|
| **F-160** | Atualizar `docs/api/endpoints.md` refletindo contrato novo | Doc bate com OpenAPI |
| **F-161** | Atualizar `docs/logic/domain-model.md` com novas entidades + ER novo | Diagrama atualizado |
| **F-162** | Atualizar `docs/overview.md` com nova estrutura de pastas | Doc bate com `app/` |
| **F-163** | `CHANGELOG.md` na raiz listando todas mudanças `v0.2.0` | Sumário pro dono |
| **F-164** | Tag `v0.2.0` no commit final | Tag visível |
| **F-165** | Abrir issue/PR no repo Flutter avisando do break + apontando docs | Comunicação registrada |

**Bloqueia:** todas as fases seguintes.

---

## Fase 2 — v0.3.0: Estoque ledger + Unidade de medida

**ADRs:** 0006 (estoque como ledger) + 0007 (unit_type + quantidade).

| ID | Task | Aceite |
|---|---|---|
| **E-201** | Tabela `locais_estoque` (FK → filiais; depósito pode ser local sem filial) | Schema |
| **E-202** | Tabela `movimentos_estoque` (ledger imutável: tipo, quantidade, local, lote, operador, timestamp) | Schema |
| **E-203** | Tabela `lotes` (produto_id, codigo, validade, observacao) | Schema |
| **E-204** | Migration: substituir `Produto.amount/kg/liters` por `Produto.unidade_padrao` + `Produto.quantidade_estoque_inicial`; gerar movimentos de entrada históricos a partir do snapshot | Saldo atual preservado |
| **E-205** | Endpoint `POST /v1/movimentos-estoque/` (entrada, saída, transferência, ajuste) | Testado |
| **E-206** | Endpoint `GET /v1/produtos/{id}/saldo?local_id=` retorna saldo calculado | Testado |
| **E-207** | Endpoint `GET /v1/produtos/{id}/lotes` lista lotes ativos ordenados por FEFO | Testado |
| **E-208** | Validar: venda não pode tirar mais que saldo; transferência precisa de local origem com saldo | Testes de regra |
| **E-209** | Deprecar `RetiradaProduto` (manter tabela read-only pra histórico; novos movimentos vão pra `movimentos_estoque`) | Endpoint antigo retorna 410 ou redirect |
| **E-210** | Doc: `docs/logic/domain-model.md` atualizado com novo ER | Doc batendo |
| **E-211** | Tag `v0.3.0` + comunicar Flutter | Release |

**Bloqueia:** Fase 3 (PDV depende de estoque), Fase 4 (Fidelidade vincula-se a venda que vincula-se a estoque).

---

## Fase 3 — v0.4.0: PDV (Venda + Pagamento + Caixa + Turno)

**ADR:** 0009.

| ID | Task | Aceite |
|---|---|---|
| **P-301** | Tabela `caixas` (filial_id, nome, status) | Schema |
| **P-302** | Tabela `turnos_caixa` (caixa_id, operador_id, abertura, fechamento, saldo_inicial, saldo_final_esperado, saldo_final_contado, diferenca) | Schema |
| **P-303** | Tabela `vendas` (turno_id, operador_id, filial_id, cliente_id nullable, status, valor_total, descontos, observacao, criada_em) | Schema |
| **P-304** | Tabela `itens_venda` (venda_id, produto_id, lote_id, quantidade, unidade, valor_unitario, valor_subtotal) | Schema |
| **P-305** | Tabela `pagamentos` (venda_id, tipo enum, valor, troco, autorizacao) | Schema |
| **P-306** | Endpoint `POST /v1/turnos-caixa/abertura` (operador abre turno num caixa) | Testado |
| **P-307** | Endpoint `POST /v1/turnos-caixa/{id}/fechamento` (saldo contado, calcula diferença) | Testado |
| **P-308** | Endpoint `POST /v1/vendas/` (cria venda com itens e pagamentos, debita estoque atômico) | Testado com cenário split-payment |
| **P-309** | Endpoint `POST /v1/vendas/{id}/cancelamento` (cancela venda + reverte movimentos de estoque) | Testado |
| **P-310** | Endpoint `GET /v1/vendas/dashboard?filial_id=&data=` retorna faturamento agregado | Testado |
| **P-311** | Doc atualizada + Tag `v0.4.0` | Release |

**Bloqueia:** Fase 4 (fidelidade concede pontos por venda).

---

## Fase 4 — v0.5.0: Fidelidade

**ADR:** 0008.

| ID | Task | Aceite |
|---|---|---|
| **L-401** | Tabela `contas_fidelidade` (cliente_id, saldo_pontos, criada_em) | Schema |
| **L-402** | Tabela `movimentos_fidelidade` (conta_id, tipo: acumulo/resgate/expiracao/estorno, pontos, venda_id nullable, criado_em) | Schema |
| **L-403** | Regra: ao concluir `Venda` com `cliente_id`, criar `MovimentoFidelidade` (tipo: acumulo) via evento ou trigger explícito | Testado |
| **L-404** | Endpoint `GET /v1/clientes/{id}/fidelidade` retorna saldo + extrato | Testado |
| **L-405** | Endpoint `POST /v1/vendas/{id}/resgate-fidelidade` aplica pontos como desconto | Testado |
| **L-406** | Job/endpoint pra expirar pontos antigos (configurável; default 12 meses) | Testado |
| **L-407** | Estorno de venda → estorno de pontos correspondente | Testado |
| **L-408** | Doc atualizada + Tag `v0.5.0` | Release |

---

## Fase 5 — v1.0.0: Hardening (lista aberta, conforme demanda)

Sem ordem fixa. Trazer só quando dor real aparecer.

| ID | Task | Quando trazer |
|---|---|---|
| **H-501** | Fiscal NFC-e (ADR-0010) — emissão, contingência, cancelamento | Quando dono pedir fiscal |
| **H-502** | Offline-first do PDV — IDs locais (UUID), fila de sync, conflict resolution | Quando internet for instável em campo |
| **H-503** | Eventos de domínio (ADR-0011) — `VendaConcluida`, `LoteVencido`, `EstoqueBaixo` | Quando complexidade entre módulos crescer |
| **H-504** | Refresh token + reset de senha | Quando UX de auth pedir |
| **H-505** | RBAC granular (permissions por endpoint, não só por papel) | Quando matriz de papéis crescer |
| **H-506** | Paginação cursor-based em listas grandes | Quando lista de produtos/vendas escalar |
| **H-507** | Indexação GIN em `Produto.metadata` (ADR-0005) | Quando busca textual em metadata virar caso real |
| **H-508** | Multi-tenancy (`Organization`, isolation) | Quando 2º dono contratar — vide [`generic-core-strategy.md`](generic-core-strategy.md) (rejeitada) |

---

## Tracking sugerido

- **Por fase:** uma `tag` no repo (`v0.2.0`, `v0.3.0`...)
- **Por task:** issue no GitHub com ID prefixado (`F-101`, `E-201`, etc.) — facilita referenciar em PR
- **Por release:** entrada em `CHANGELOG.md`
- **Comunicação com o dono do Flutter:** issue **lá** anunciando cada tag, com link pra `endpoints.md` atualizado

---

## Onde começar agora

**Sugestão prática:** começar por **Fase 0** completa (1-2 dias) + **F-101, F-102** (setup de testes, baseline). Sem isso, qualquer task de Fase 1.3 em diante é arriscada.

Depois, mergulhar em **F-110 a F-128** sequencialmente — todas as mudanças de schema/modelo numa migration única.
