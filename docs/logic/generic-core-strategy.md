# Estratégia: Núcleo Genérico + Presets Verticais

> ## ⚠️ ALTERNATIVA REJEITADA — não adotada
>
> **Decidido em 2026-05-05** focar em **laticínios apenas**, com **dono único e suas filiais** (não SaaS multi-vertical). Esta estratégia foi avaliada e **descartada por YAGNI**: a complexidade de núcleo genérico + presets só se paga quando há interesse real de vender pra outros ramos. Hoje há um cliente único (laticínios) e a abstração custaria meses sem retorno.
>
> **Direção adotada:** ver [`architecture-laticinios.md`](architecture-laticinios.md).
>
> **Quando reconsiderar:** se aparecer demanda real de outros ramos (não hipotética), reabrir este doc e calcular o custo de refatoração vs construir do zero.

---

> **Status:** Working doc — vira ADR-0003 quando aprovado
> **Data:** 2026-05-05
> **Posicionamento do produto:** API+app que serve **qualquer pequeno/médio comércio**, com laticínios como o **primeiro preset** (cliente real validador).

---

## 1. O que isso significa, em uma linha

> **Construir um SaaS de gestão comercial onde o "ramo do negócio" é configuração, não código.**

O empresário de laticínios é o **primeiro cliente** e o **primeiro preset**. Mas o sistema deve aceitar amanhã uma padaria, uma farmácia, uma loja de roupa — sem fork de código, só com configuração.

Isso é **diferente** de "API de laticínios que abrimos depois pra outros ramos" — essa abordagem cria dívida técnica em ramificações verticais que se contradizem. **Genérico-primeiro com vertical-como-dado** é o caminho durável.

---

## 2. As três camadas

```
┌──────────────────────────────────────────────────┐
│  L3 — TENANT (organização cliente)               │
│  • Configurações específicas (logo, regras)      │
│  • Feature flags ligados/desligados              │
│  • metadata JSONB para campos custom             │
└──────────────────────────────────────────────────┘
                       ▲ herda de
┌──────────────────────────────────────────────────┐
│  L2 — VERTICAL PRESET (laticínios, padaria, etc.)│
│  • Unidades de medida padrão                     │
│  • Features default ligadas                      │
│  • Schema de attributes específicos do ramo      │
│  • Templates (catálogo, regras fiscais, etc.)    │
└──────────────────────────────────────────────────┘
                       ▲ é instância de
┌──────────────────────────────────────────────────┐
│  L1 — NÚCLEO GENÉRICO                            │
│  • Entidades universais (Product, Sale, ...)     │
│  • Pontos de extensão definidos                  │
│  • Nenhuma referência a "kg" ou "queijo"         │
└──────────────────────────────────────────────────┘
```

**Regra de ouro:** L1 não pode mencionar nada vertical. Se aparece a palavra "queijo" ou "litros" no núcleo, está errado.

---

## 3. Núcleo genérico (L1) — o que entra

### Entidades universais

| Entidade | Para que serve | Genérica porque... |
|---|---|---|
| `Organization` | Tenant (o cliente do SaaS) | Todo SaaS multi-tenant tem |
| `User` / `Operator` | Pessoa que opera o sistema | Universal |
| `Customer` | Cliente final (consumidor) | Todo comércio que vende a alguém |
| `Product` | Item vendável | Universal — o que difere é o que **descreve** o produto, não o conceito |
| `ProductVariant` | Variação de um produto (tamanho, cor) | Opt-in via feature flag (vestuário sim, laticínios não) |
| `StockLocation` | Onde estoque mora | Universal |
| `StockMovement` | Cada entrada/saída/ajuste (ledger) | Universal |
| `Lot` | Lote/validade | Opt-in via feature flag (laticínios/farmácia sim, vestuário não) |
| `Order` | Pedido (atacado, reposição, encomenda) | Universal — só nem todo ramo usa |
| `Sale` | Venda (varejo, balcão, delivery) | Universal |
| `Payment` | Forma de pagamento | Universal |
| `CashRegisterSession` | Turno de caixa | Universal |
| `LoyaltyAccount` | Conta de pontos | Opt-in |
| `LoyaltyTransaction` | Movimento de pontos | Opt-in |

### Pontos de extensão (escape hatches)

Estes são os mecanismos que tornam o núcleo extensível **sem mudar código**:

1. **Coluna `metadata JSONB`** em entidades-chave: `Product`, `Sale`, `Customer`, `Lot`, `StockMovement`. Onde o vertical encaixa atributos próprios.
2. **`unit_type` (string)** em `Product` e `StockMovement` — não há enum hardcoded; o preset diz quais valores são válidos.
3. **`feature_flags`** em `Organization` — liga/desliga módulos (lote, fiscal, variantes, fidelidade, multi-localização).
4. **`product_kind`** em `Product` — classificação livre que o preset define (em laticínios: "fresco", "curado"; em farmácia: "controlado", "comum"). Útil pra regras automáticas.
5. **Hooks/eventos de domínio** — `SaleCompleted`, `StockMovementCreated`. Verticais podem reagir sem alterar o núcleo (ex: laticínios escuta `LotCreated` pra registrar temperatura de entrada).

---

## 4. Vertical Preset (L2) — o que é

Um preset é uma **linha numa tabela** (ou arquivo de configuração versionado), não um módulo de código. Estrutura:

```yaml
# vertical_presets/laticinios.yaml (exemplo)
slug: laticinios
name: Laticínios
default_features:
  lots_and_expiration: true        # FEFO obrigatório
  product_variants: false          # não usa
  loyalty: true
  fiscal_nfce: true
  multi_location: true
default_unit_types: [kg, litro, unidade, caixa]
product_attribute_schema:          # validado contra metadata JSONB
  type: object
  properties:
    temperature_range: {type: string, enum: [refrigerado, congelado, ambiente]}
    fat_content_pct: {type: number}
    pasteurized: {type: boolean}
default_product_kinds: [fresco, curado, processado, leite_in_natura]
seed_products: true                # popular catálogo inicial
seed_loyalty_rule: "1 ponto por R$ 1,00 gasto"
```

```yaml
# vertical_presets/vestuario.yaml
slug: vestuario
name: Vestuário
default_features:
  lots_and_expiration: false       # roupa não vence
  product_variants: true           # tamanho/cor obrigatório
  loyalty: true
  fiscal_nfce: true
  multi_location: true
default_unit_types: [unidade]
product_attribute_schema:
  type: object
  properties:
    fabric: {type: string}
    season: {type: string, enum: [verao, inverno, atemporal]}
    care_instructions: {type: string}
default_product_kinds: [vestuario, calcado, acessorio]
```

Quando uma `Organization` é criada, ela escolhe um `vertical_preset`. Os defaults daquele preset viram o estado inicial — mas o lojista pode customizar tudo depois.

---

## 5. Validação: três verticais em cima do mesmo núcleo

Pra ter certeza que a abstração segura, modelei rapidamente três ramos diferentes do laticínios em cima das mesmas entidades:

### 5.1 Laticínios (caso atual)

- `feature_flags`: `lots_and_expiration=true`, `product_variants=false`
- `Product`: `name="Queijo Minas Frescal"`, `unit_type="kg"`, `kind="fresco"`, `metadata={"temperature_range":"refrigerado","pasteurized":true}`
- `Lot`: `expires_at="2026-05-20"`, `metadata={"farm":"São João","milk_origin_date":"2026-04-25"}`
- `Sale`: B2C balcão + B2B consignação (ambos suportados)

### 5.2 Padaria

- `feature_flags`: `lots_and_expiration=true` (validade curta), `product_variants=false`
- `Product`: `name="Pão Francês"`, `unit_type="unidade"`, `kind="produzido_dia"`, `metadata={"shelf_life_hours":24}`
- `Lot`: `expires_at` muito curto (24-72h), uso intensivo de FEFO
- `Sale`: 100% B2C balcão

### 5.3 Farmácia

- `feature_flags`: `lots_and_expiration=true`, `product_variants=false`, **+ flag custom `prescription_control=true`**
- `Product`: `name="Amoxicilina 500mg"`, `unit_type="caixa"`, `kind="antibiotico"`, `metadata={"requires_prescription":true,"controlled_substance":"C1","active_ingredient":"amoxicilina"}`
- `Lot`: validade longa, mas regulada por ANVISA
- `Sale`: balcão + integração com receituário (módulo opt-in)

### 5.4 Vestuário

- `feature_flags`: `lots_and_expiration=false`, **`product_variants=true`**
- `Product`: `name="Camiseta Básica"`, `unit_type="unidade"`, `kind="vestuario"`
  - `ProductVariant`: `(size="M", color="azul")` — SKU separado por combinação
- `Lot`: não usado
- `Sale`: balcão + e-commerce

**Resultado:** o núcleo segura. Os pontos de extensão (`metadata`, `feature_flags`, `kind`, `unit_type`) absorvem 100% do que é específico de cada ramo. Onde precisa de **estrutura nova** (ex: `ProductVariant`) ela é parte do núcleo, mas opt-in.

---

## 6. Trade-offs e riscos

### 6.1 "Genérico demais" vs "vertical pobre"

**Risco:** núcleo virar tão abstrato que cada vertical reimplementa metade das regras no `metadata`.

**Mitigação:**
- Schema validation por preset (Pydantic gera validador a partir do YAML do vertical).
- Limites claros: o que é regra de negócio importante **vira coluna real** no núcleo (ex: `expires_at` em `Lot`); o que é metadata observacional fica no JSONB.
- Revisão periódica: se duas verticais convergem usando a mesma chave em `metadata`, promove pra coluna do núcleo.

### 6.2 JSONB sem disciplina vira lixo

**Risco:** `metadata` virar caixa-preta com chaves variantes, typos, dados inconsistentes.

**Mitigação:**
- Cada preset declara **schema JSONSchema** validado na escrita.
- Migrations explícitas quando schema do preset muda (não silencioso).
- Queries críticas nunca dependem de `metadata` — só de colunas estruturadas.

### 6.3 Custo cognitivo do "configurar tudo"

**Risco:** lojista novo abre o sistema e vê 50 toggles. Vai embora.

**Mitigação:**
- Preset escolhe defaults sensatos. Lojista mexe se quiser; não precisa.
- Onboarding guiado por vertical (wizard com perguntas-chave do ramo).
- Catálogo seed: cada vertical traz 30-50 produtos típicos pré-cadastrados.

### 6.4 Empresário inicial pode "puxar" pro vertical dele

**Risco:** o cliente real (laticínios) fica pedindo features que viram código no núcleo em vez de no preset.

**Mitigação (esta é cultural, não técnica):**
- Antes de aceitar feature, perguntar: **"isso vale pra padaria? farmácia? roupa?"**
- Se sim → núcleo. Se não → preset. Se não couber em preset → flag custom + módulo opt-in.
- Documentar a decisão num ADR.

### 6.5 Multi-tenancy sem multi-tenancy é mentira

**Risco:** sistema "preparado pra qualquer negócio" mas com 1 cliente, sem `organization_id`. Quando o segundo cliente entrar, refactor é dor.

**Mitigação:**
- ADR-0003 já trata multi-tenant **antes** de qualquer feature nova.
- Toda entidade de negócio carrega `organization_id` desde o dia 1.
- Indexes compostos `(organization_id, ...)` desde a primeira migration nova.

---

## 7. O que isso muda no roadmap

A ordem das ADRs precisa mudar pra refletir que **o núcleo genérico vem antes das features**:

| Antes | Agora | Diferença |
|---|---|---|
| ADR-0003 multi-tenant | ADR-0003 multi-tenant | igual |
| ADR-0004 Customer separado | **ADR-0004 Núcleo genérico + presets verticais** | esta nova ADR consolida a decisão estratégica |
| ADR-0005 unit_type genérico | ADR-0005 Customer separado | empurrado |
| ADR-0006 estoque ledger | ADR-0006 unit_type + product attributes (JSONB) | mais amplo |
| ADR-0007 offline PDV | ADR-0007 estoque ledger (genérico, lote opt-in) | inclui Lot |
| ADR-0008 fiscal | ADR-0008 PDV (Sale, Payment, CashRegister) | mantém ordem |
| ADR-0009 fidelidade | ADR-0009 fiscal opt-in | mantém |
| ADR-0010 eventos domínio | ADR-0010 fidelidade opt-in | mantém |
|  | ADR-0011 eventos de domínio | mantém |

ADR-0004 é a **espinha dorsal** — todas as seguintes herdam dela.

---

## 8. Como o app Flutter encosta nisso

O app Flutter atual é "de laticínios" no conteúdo, mas o **app pode ser genérico** com a mesma estratégia:

- Tela de produto exibe campos do `metadata` conforme **schema do preset** (renderização dirigida por dados).
- Lista de unidades vem do preset, não hardcoded.
- Features ligadas/desligadas no app refletem `feature_flags` da organização (sem botão de fidelidade pra cliente que não usa).
- Skin/cores são per-organization.

Isso vira ADR de cliente (não de API), mas vale registrar que a estratégia da API **só faz sentido** se o cliente também respeitar.

---

## 9. Decisões que precisam ser tomadas

Para promover este doc a ADR-0004, responder:

1. **Confirma o posicionamento "SaaS multi-vertical desde o dia 1"?** (Alternativa honesta: focar em laticínios, refatorar depois — mais barato no curto prazo, mais caro no longo.)
2. **Verticais MVP planejados em ordem:** laticínios → ? → ?  
   (Mesmo que só implementemos laticínios primeiro, saber os próximos 2 calibra as abstrações.)
3. **Modelo comercial:** o cliente paga por organização, por usuário, por venda? (Define onde cabem limites no `feature_flags`.)
4. **Preset é fixo (1 por organização) ou pode misturar?**  
   Ex: padaria que vende roupa de uniforme — quer dois presets ou um custom?  
   Recomendo: **1 preset por organização**, customizações via `feature_flags` e `metadata`. Misturar preset adiciona complexidade exponencial.

---

## 10. Próximo passo concreto

Se aprovar a direção:

1. Promover este doc a **ADR-0004 — Núcleo genérico com presets verticais**
2. Reordenar as ADRs seguintes
3. Começar implementação pela **fundação**: `Organization` + multi-tenant + feature_flags (ADR-0003 + esqueleto de ADR-0004 simultaneamente)
4. Migrar entidades atuais (`Product`, `Order`, `RetiradaProduto`) pro novo formato com `organization_id` + `metadata`

Se o objetivo é só **descobrir mais antes de decidir**, o próximo passo é levantar requisitos com o empresário (questionário no `scope-discussion.md`) **considerando que a resposta dele vai virar o preset "laticínios"**, não o núcleo.
