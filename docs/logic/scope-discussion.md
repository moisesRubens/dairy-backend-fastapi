# Discussão de Escopo — PDV, Estoque, Fidelidade

> **Status:** Documento de trabalho (working doc), não-normativo. Serve de matéria-prima para futuras ADRs e o levantamento de requisitos.
> **Data:** 2026-05-05
> **Premissa central:** API atual + app Flutter, evoluindo para um produto de gestão comercial mais completo.

---

## 1. O que temos hoje (baseline honesto)

A API atual é, na prática, um **sistema de distribuição em consignação B2B**:

- **SalePoints** se autenticam e fazem **pedidos** (Orders).
- **Retiradas** (`RetiradaProduto`) representam saída em consignação: o ponto recebe X de produto, vende Y, sobra Z. Reconcilia depois.
- **Products** têm preço único e três unidades hardcoded (`amount`, `kg`, `liters`).

**O que isso *não* é hoje:**
- Não é um PDV — não há fluxo de caixa, formas de pagamento, fechamento de turno, cupom fiscal.
- Não é um sistema de estoque "de verdade" — não há entradas, transferências, lote, validade, custo.
- Não tem cliente final (consumidor) — o "usuário" da API é o ponto de venda, não a pessoa que compra.

Isso é **importante** porque os três temas que você cuspiu (PDV, estoque, fidelidade) **assumem coisas que o modelo atual não tem**. Precisamos encarar essas lacunas explicitamente em vez de "estender pelas bordas".

---

## 2. Premissas que precisam de resposta antes de qualquer ADR

Sem isso definido, qualquer arquitetura é palpite:

1. **Quem é o usuário do app Flutter?**
   - (a) Apenas funcionário do ponto de venda (operador de caixa)?
   - (b) Apenas o consumidor final (com fidelidade, histórico de compras)?
   - (c) Os dois — mesmo app com perfis distintos?
   - (d) Dois apps separados consumindo a mesma API?

2. **O modelo de negócio é único ou misto?**
   - Distribuidor B2B vendendo pra pontos de venda (modelo atual) **e**
   - Pontos de venda usando o sistema como PDV pra vender ao consumidor final?
   - Se ambos, o sistema vira **multi-tenant** com dois papéis distintos (distribuidor / lojista) — isso muda muito.

3. **Escopo fiscal:**
   - Vai emitir nota? (NFC-e/SAT no varejo, NF-e no atacado)
   - Se sim, isso domina a complexidade. Sem fiscal, o PDV é "só" um caderno digital.

4. **Multi-empresa?**
   - O empresário inicial é um — mas o produto é pra ele só, ou para vender pra outros empresários do mesmo ramo?
   - Se for produto, precisa ser **SaaS multi-tenant** desde o início (`organization_id` em tudo).

5. **Genérico vs vertical de laticínios?**
   - Já discutimos: o modelo é ~70% genérico. Decidir agora se vamos abrir pra outros ramos ou focar em laticínios afeta as próximas ADRs (especialmente unidades de medida e validade/lote).

---

## 3. Os três pilares em detalhe

### 3.1 PDV — Point of Sale

**O que muda no modelo atual:**

O `Order` atual é um pedido de **distribuição** (sales point → distribuidor). Um PDV precisa de **venda** (consumidor → ponto de venda). São duas operações diferentes que merecem entidades diferentes:

```
Order   (existente)  → "fiz um pedido pra reposição"  [atacado/consignação]
Sale    (novo)       → "vendi pro consumidor"          [varejo/PDV]
```

**Conceitos novos exigidos:**

| Conceito | Por quê |
|---|---|
| `Sale` (venda) | Transação no caixa, com itens, pagamentos, cliente opcional |
| `Payment` | Forma de pagamento da venda (dinheiro, débito, crédito, PIX, voucher, fiado) — uma venda pode ter N (split) |
| `CashRegister` (caixa) | Identifica o caixa físico/virtual; cada venda pertence a um |
| `CashRegisterSession` | Abertura/fechamento de turno com saldo inicial, sangrias, suprimentos, saldo final esperado vs contado |
| `Operator` (operador) | Funcionário que opera o caixa (não o sales point — uma pessoa) — credencial separada |
| `Discount` / `Promotion` | Desconto manual ou regra automática aplicada na venda |
| `Receipt` / fiscal | Cupom/comprovante; se for fiscal, integração com SEFAZ |

**Decisões a tomar (futuras ADRs):**

- **PDV é offline-first?** Caixa não pode parar se a internet cair. Isso muda **tudo** — fila de sincronização, IDs gerados localmente (UUID), conflito de estoque. Decisão crítica e cara de adiar.
- **Numeração de cupom é por caixa ou global?** Fiscal exige sequencial por equipamento.
- **Cancelamento de venda:** soft delete + entrada de estorno, ou marca como cancelada in-place? (Auditoria fiscal exige histórico.)

**MVP de PDV (sem fiscal):**
- Abertura/fechamento de caixa
- Venda com múltiplos itens, múltiplos pagamentos
- Cancelamento simples (mesmo turno)
- Comprovante não-fiscal em PDF/impressão térmica

**Riscos:**
- Subestimar fiscal — adicionar NFC-e depois de pronto custa 3x mais que projetar com ele em mente.
- Misturar `Order` (atacado) com `Sale` (varejo) na mesma tabela — vai virar carnaval em 6 meses.

---

### 3.2 Estoque

**Limitações do modelo atual:**

O `Product` tem `amount`/`kg`/`liters` como **colunas que viram o "estoque atual"**. Isso é o que se chama de "snapshot" — só guarda o número de agora, sem histórico. Não dá pra responder:

- Quanto tinha de produto X dia 15?
- Quem fez a entrada de 200kg de queijo no estoque?
- Qual lote venceu primeiro?

**O que estoque "de verdade" exige:**

| Conceito | Função |
|---|---|
| `StockMovement` (movimento) | Cada entrada/saída/transferência/ajuste é um registro. Estoque atual = soma dos movimentos. **Imutável.** |
| `StockLocation` | Onde o produto está (depósito central, ponto X, prateleira A) — permite múltiplos locais |
| `Lot` / `Batch` | Lote de fabricação (com data de validade) — **crítico em laticínios** |
| `ExpirationDate` | Data de validade por lote — alerta antes de vencer, FEFO (First-Expire-First-Out) |
| `Cost` (custo médio / FIFO) | Diferente do preço. Custo entra com a compra do fornecedor |
| `Supplier` (fornecedor) | De onde veio o lote |
| `StockTake` (inventário) | Contagem física periódica + ajuste de divergência |
| `MinStock` / alerta | Nível mínimo por produto/local pra disparar reposição |

**Específico do ramo laticínios** (esse aqui é provavelmente seu valor agregado vs concorrência genérica):

- **Validade curta** — leite cru/pasteurizado tem dias, não meses. FEFO obrigatório.
- **Cadeia do frio** — dá pra registrar temperatura na entrada do lote como metadado.
- **Variação por safra/estação** — leite de inverno tem outra composição. Vale guardar atributos do lote.
- **Devolução por validade** — venda em consignação que retorna porque venceu vira perda. Tem regra contábil específica.

**Como isso conversa com o `RetiradaProduto` atual:**

`RetiradaProduto` hoje é um **híbrido**: tem `taken_quantity` (parece movimento de saída), `sold_quantity` (parece venda) e `remaining_quantity` (parece saldo). Está fazendo trabalho de três entidades. No modelo evoluído:

- `taken_quantity` → vira `StockMovement` (saída do depósito central → entrada no ponto)
- `sold_quantity` → vira soma de `Sale.items` no ponto
- `remaining_quantity` → calculado, não armazenado

Esse refactor é grande mas inevitável se for sério com estoque.

**MVP de estoque:**
- `StockMovement` substituindo as colunas amount/kg/liters como fonte de verdade
- Múltiplos `StockLocation` (depósito + N pontos)
- Lote com validade (sem cadeia do frio ainda)
- Relatório de saldo por local/produto
- Alerta de validade próxima

---

### 3.3 Fidelidade

**O gap mais óbvio:** **não existe entidade `Customer` no sistema.** Hoje o "usuário" é o `SalePoint` (B2B). Pra fazer fidelidade, precisa identificar o **consumidor final**.

**Conceitos novos:**

| Conceito | Função |
|---|---|
| `Customer` (cliente final) | Pessoa física: nome, CPF, telefone, e-mail, data de nascimento (aniversário = cupom) |
| `LoyaltyAccount` | Conta de pontos do cliente (saldo + histórico) |
| `LoyaltyTransaction` | Cada acúmulo/resgate/expiração — imutável, igual estoque |
| `EarningRule` | "1 ponto a cada R$1 gasto" / "ponto duplo no produto X" / "regra A vale só na semana Y" |
| `RedemptionRule` | "100 pontos = R$5 de desconto" / "500 pontos = produto Y grátis" |
| `Tier` (segmento) | Bronze/Prata/Ouro com benefícios diferentes — opcional pra MVP |
| `Campaign` (campanha) | Período + regras especiais (Black Friday, Dia do Cliente) |

**Como cliente é identificado no PDV:**
- CPF (mais comum no Brasil)
- Telefone
- QR code do app Flutter (gerado dinamicamente)
- Cartão físico de fidelidade (raro hoje, mas alguns segmentos pedem)

**Pontos críticos de design:**

1. **Pontos têm validade.** Quase sempre 12 meses. Precisa de job que expira pontos antigos (lógica FIFO: gastam-se primeiro os pontos mais próximos de expirar).
2. **Idempotência da concessão.** Se a venda for sincronizada duas vezes (offline-first do PDV), os pontos não podem ser concedidos em duplicidade. Cada `LoyaltyTransaction` deve referenciar a `Sale` com unique constraint.
3. **Estorno de venda → estorno de pontos.** Cancelou venda? Devolve pontos. Já gastou os pontos? Saldo negativo permitido ou bloqueia o cancelamento? **Decisão de negócio.**
4. **Privacidade (LGPD).** Customer é dado pessoal. Consentimento + direito ao esquecimento + base legal pra tratamento.

**Onde fidelidade encosta no Flutter:**
- Cliente abre o app → vê saldo de pontos, histórico, recompensas disponíveis
- No PDV, operador digita CPF → API retorna saldo e descontos disponíveis pra aplicar
- Push notification de "seus pontos expiram em 30 dias" — engajamento clássico

**MVP de fidelidade:**
- `Customer` + `LoyaltyAccount` + `LoyaltyTransaction`
- Uma única regra de acúmulo (R$ → pontos) configurável por organização
- Resgate como desconto direto na venda (não em produto)
- Sem tiers, sem campanhas, sem expiração na primeira versão (mas com schema preparado pra adicionar)

---

## 4. Arquitetura: como os três conversam

```
┌──────────────────────────────────────────────────────┐
│                  App Flutter                         │
│  (perfil operador + perfil cliente, ou apps      )   │
└────────────────────┬─────────────────────────────────┘
                     │
                     ▼
┌──────────────────────────────────────────────────────┐
│                   API FastAPI                        │
│ ┌──────────┐  ┌──────────┐  ┌──────────────────┐     │
│ │  Auth    │  │  PDV     │  │   Fidelidade     │     │
│ │ (multi   │  │ (Sale,   │  │ (Customer,       │     │
│ │ tenant)  │  │ Payment, │  │  LoyaltyAccount, │     │
│ │          │  │ Cash)    │  │  Transaction)    │     │
│ └──────────┘  └────┬─────┘  └────────┬─────────┘     │
│                    │                 │               │
│                    ▼                 │               │
│              ┌──────────┐            │               │
│              │ Estoque  │◄───────────┘               │
│              │ (Movement│  (resgate de produto       │
│              │  Lot,    │   debita estoque)          │
│              │  Location│                            │
│              └──────────┘                            │
│                                                      │
│  Distribuição (legado: Order, RetiradaProduto)       │
│  → vira fonte de StockMovement no novo modelo        │
└──────────────────────────────────────────────────────┘
```

**Princípios:**

1. **Estoque é a fonte de verdade.** PDV consome estoque ao vender, não modifica produto.
2. **Fidelidade é assíncrona em relação ao PDV.** Conceder pontos não pode bloquear o caixa. Se o serviço de fidelidade cair, a venda continua e os pontos entram numa fila.
3. **Cada venda gera N efeitos independentes:** 1 `StockMovement` por item (saída), 0..N `LoyaltyTransaction` (acúmulo), 0..1 emissão fiscal. Vale modelar com **eventos de domínio** (`SaleCompleted`) que outros módulos escutam.

---

## 5. Roadmap sugerido (faseado)

A ordem importa porque cada fase destrava a próxima.

**Fase 0 — Fundação (próximos PRs)**
- ADR-0002 (já proposto) — refactor de roteamento
- ADR-0003 — multi-tenant (`organization_id` em tudo)
- ADR-0004 — `Customer` como entidade separada de `SalePoint`
- Renomeação PT→EN dos campos legados

**Fase 1 — Estoque robusto**
- `StockMovement` + `StockLocation` + `Lot`
- Migrar `RetiradaProduto` para movimentos
- Manter compat de leitura (views/endpoints antigos retornando saldo calculado)

**Fase 2 — PDV MVP**
- `Sale`, `Payment`, `CashRegisterSession`
- Sem fiscal nem offline-first
- Integração com Estoque (venda gera movimento)

**Fase 3 — Fidelidade MVP**
- `LoyaltyAccount` + `LoyaltyTransaction`
- Regra única de acúmulo
- Resgate como desconto

**Fase 4 — Hardening**
- Offline-first no PDV (se confirmado como requisito)
- Fiscal (se aplicável)
- Tiers, campanhas, expiração de pontos

---

## 6. Próximas ADRs sugeridas

| Número | Título | Pré-requisito |
|---|---|---|
| ADR-0003 | Multi-tenancy (organization_id em todas as entidades) | Resposta às premissas 4 |
| ADR-0004 | Customer ≠ SalePoint: separação de identidades | Resposta à premissa 1 |
| ADR-0005 | Modelo de unidade de medida genérico (`unit_type` + `quantity`) | Resposta à premissa 5 |
| ADR-0006 | Estoque como ledger de movimentos (substitui colunas em Product) | ADR-0005 |
| ADR-0007 | PDV: offline-first ou online-only? | Confirmação do uso real |
| ADR-0008 | Modelo fiscal: NFC-e desde o início ou opt-in posterior? | Premissa 3 |
| ADR-0009 | Fidelidade: regras configuráveis vs hardcoded | Premissa 1 + 4 |
| ADR-0010 | Eventos de domínio para desacoplamento (SaleCompleted, etc.) | ADR-0006 |

---

## 7. Próximos passos: levantamento de requisitos

Pra fechar essa discussão e entrar em ADRs concretas, sugiro uma sessão estruturada com o empresário (cliente real) cobrindo:

**Negócio**
- Quantos pontos de venda hoje? Em quanto tempo escala pra quantos?
- Qual % das vendas é consignação (atacado) vs varejo no balcão?
- Tem caixa/PDV físico ou tudo é via celular?
- Emite nota? Qual tipo?
- Tem programa de fidelidade hoje (mesmo que manual em caderno)?

**Operação**
- Quantos funcionários por ponto?
- Internet é estável nos pontos? (define offline-first)
- Tem leitor de código de barras? Impressora térmica?
- Como recebe pagamento? (cartão, PIX, fiado)

**Produto**
- Validade média dos produtos vendidos?
- Tem perda por vencimento hoje? Qual %?
- Quantos SKUs no catálogo?

**Cliente final**
- Tem cadastro de cliente hoje? Onde?
- Cliente é fiel ou rotativo?
- Aniversário, indicação, recompra — alguma dessas vale ponto?

Com isso respondido, as ADRs viram triviais.
