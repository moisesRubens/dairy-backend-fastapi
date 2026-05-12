# Arquitetura — Foco Laticínios, Dono Único Multi-Filial

> **Status:** Direção adotada — vira ADR-0003 (e seguintes)
> **Data:** 2026-05-05
> **Substitui:** [`generic-core-strategy.md`](generic-core-strategy.md) (rejeitado por YAGNI)

---

## 1. Decisões locked-in

| Decisão | Resposta |
|---|---|
| Vertical | **Laticínios apenas** (sem abstração multi-vertical) |
| Modelo comercial | **Dono único** com **N filiais (sales points)** sob ele |
| Tenancy | **Single-tenant** — sem `organization_id`, sem multi-empresa |
| Cliente do app Flutter | A definir (provavelmente operador da filial) |
| Fiscal (NFC-e) | A definir |

## 2. O que isso simplifica (vs proposta anterior)

- ❌ Não precisa de `organization_id` em toda entidade
- ❌ Não precisa de tabela `vertical_preset` nem schema dinâmico
- ❌ Não precisa de `metadata JSONB` com validação por vertical
- ❌ Não precisa de feature flags pra "ligar/desligar lote"
- ✅ Lote, validade, FEFO **simplesmente são**
- ✅ Unidades em laticínios são limitadas (kg, litro, unidade) — pode até ser enum
- ✅ Modelo concreto: "queijo" é queijo, sem indireção

## 3. O que muda no entendimento do modelo atual

A premissa do código atual é "**SalePoint = cliente B2B externo que compra do distribuidor**" (consignação). Com a decisão de "dono único com suas filiais", a semântica gira:

| Conceito | Antes (consignação B2B) | Agora (dono multi-filial) |
|---|---|---|
| `SalePoint` | Cliente externo que recebe produto | **Filial/branch** do próprio dono |
| Login do `SalePoint` | Credencial do cliente externo | Credencial **do operador da filial** |
| `RetiradaProduto.taken_quantity` | Saída em consignação para terceiro | **Transferência interna** (depósito → filial) |
| `RetiradaProduto.sold_quantity` | Vendas que o terceiro reportou | Vendas reais da filial (deveria virar `Sale.total`) |
| `Customer` (consumidor final) | Inexistente | **Falta criar** (B2C nas filiais + fidelidade) |

**Consequência:** o `RetiradaProduto` está fazendo o trabalho de duas coisas (transferência de estoque + venda) e **deveria ser separado** em `StockMovement` (interno) + `Sale` (PDV).

## 4. Modelo conceitual da nova arquitetura

```
Owner (1, implícito — admin do sistema)
  │
  ├── Operator (funcionários — caixa, gerente da filial)
  │
  ├── SalePoint = Filial (1..N)
  │     │
  │     ├── StockLocation     ← estoque desta filial
  │     │     └── StockMovement (ledger imutável)
  │     │
  │     ├── CashRegister (1..N caixas físicos/virtuais)
  │     │     └── CashRegisterSession (turnos abertos/fechados)
  │     │
  │     └── Sale (vendas de balcão)
  │           ├── SaleItem (produtos vendidos)
  │           ├── Payment (formas de pagamento — pode ter N por venda)
  │           └── Customer? (opcional, pra fidelidade)
  │
  ├── CentralWarehouse? (opcional — depósito central que abastece filiais)
  │     └── StockLocation
  │
  ├── Product (catálogo único do dono)
  │     └── Lot (validade, FEFO)
  │
  └── Customer (consumidor final)
        └── LoyaltyAccount
              └── LoyaltyTransaction (acúmulo/resgate/expiração)
```

**Pontos importantes:**

1. **`LocalEstoque` ≠ `Filial`** estritamente. Uma filial pode ter mais de um estoque (loja + frigorífico anexo). Um depósito central também é `LocalEstoque` mas não é `Filial`.
2. **`Cliente` é o consumidor final** — pessoa física que compra na filial. Diferente de `Filial` e de `Operador` (funcionário).
3. **Lote é first-class** — não opt-in. Em laticínios é obrigatório.
4. **`Pedido`** (atacado/consignação para fora) **fica como caso opcional**. Se o dono também vende em atacado pra terceiros, mantém. Se não, deprecia.

> **Nota terminológica:** referências a entidades neste doc seguem o glossário canônico ([`glossario.md`](glossario.md)) definido pela ADR-0004. Em pt-BR: Filial, Operador, Cliente, Produto, Pedido, Venda, MovimentoEstoque, LocalEstoque, Lote, etc.

## 5. Roadmap de ADRs (atualizado e simplificado)

A lista anterior de 11 ADRs vira esta lista mais curta:

| ADR | Título | Status | Pré-requisito |
|---|---|---|---|
| **ADR-0002** | Roteamento por domínio (paths em pt-BR) | Proposto | — |
| **ADR-0003** | Filial + Operador + Cliente (separação de responsabilidades) | Proposto | — |
| **ADR-0004** | Idioma do domínio em pt-BR | Proposto | — |
| **ADR-0005** | Estoque como ledger (`MovimentoEstoque` + `LocalEstoque`) + Lote/validade | Pendente | ADR-0003, ADR-0004 |
| **ADR-0006** | `unidade_medida` + `quantidade` (substitui colunas `amount`/`kg`/`liters`) | Pendente | ADR-0005 |
| **ADR-0007** | Fidelidade: `ContaFidelidade` + `MovimentoFidelidade` | Pendente | ADR-0003 |
| **ADR-0008** | PDV: `Venda`, `Pagamento`, `Caixa`, `TurnoCaixa` | Pendente | ADR-0005 + ADR-0007 |
| **ADR-0009** | Fiscal NFC-e (opt-in) | Pendente | ADR-0008 + decisão de negócio |
| **ADR-0010** | Eventos de domínio (`VendaConcluida`, etc.) — se complexidade pedir | Pendente | ADR-0008 |

**Ordem natural de implementação:** 0002 + 0003 + 0004 (juntos — todos são fundação) → 0005 → 0006 → 0007 → 0008 → 0009.

## 6. O que fica em aberto e quando reabrir

### 6.1 Multi-tenancy (vender pra outros donos de laticínios)
- **Quando reabrir:** quando houver pedido real de um segundo dono
- **Custo estimado de adiar:** 2-3 semanas de refactor — se evitarmos certos acoplamentos agora (item 7)
- **Não é caro reabrir** desde que o código não confunda "Owner" com "filial"

### 6.2 Multi-vertical (servir padaria, farmácia, etc.)
- Marcado como **rejeitado**. Reabre apenas se houver demanda concreta.

### 6.3 Premissas ainda em aberto
- **Quem opera o app Flutter?** (operador da filial / dono / consumidor)
- **Vai emitir nota?** (NFC-e — define complexidade do PDV)
- **PDV é offline-first?** (define IDs locais, fila de sync, conflito de estoque)
- **Tem depósito central separado das filiais?** (define se precisa de `StockLocation` autônomo)

## 7. Cuidados que evitam dor futura (sem over-engineering hoje)

Coisas baratas de fazer agora que destravam multi-tenancy depois:

1. **Não usar `id` numérico em URLs/respostas externas** sem prefixo de escopo. Usa-se sequencial interno, mas a API expõe slug/uuid quando relevante.
2. **Encapsular acesso a "dono atual"** num único lugar (ex: `current_owner()` mesmo que retorne sempre `Owner(id=1)` por enquanto). Quando virar SaaS, troca-se a função e pronto.
3. **`Customer` separado de `SalePoint` desde o dia 1** — fundir agora e separar depois é caro.
4. **Estoque como ledger desde o dia 1** — colunas-snapshot são caro de migrar com histórico.

Custo zero ou quase zero, e abre opções futuras sem comprometer YAGNI.

## 8. Próximo passo concreto

Promover este doc a **ADR-0003** (com título mais específico: *"SalePoint como filial: separação de SalePoint, Operator e Customer"*).

ADR-0003 fica curto e foca em **uma decisão** (a renomeação semântica + criação do `Customer`). As outras decisões viram suas próprias ADRs.

**Pergunto antes de redigir:** essa direção está OK? Algo aqui que te incomoda ou parece errado pra como você está pensando?
