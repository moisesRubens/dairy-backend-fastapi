# Análise do Cliente Flutter (repo do dono)

> **Repo:** https://github.com/moisesRubens/dairy.git
> **Clone local de referência:** `../dairy-flutter-ref/` (sibling deste repo)
> **Data da análise:** 2026-05-07

---

## TL;DR

O repo Flutter **não tem implementação** — só boilerplate quebrado. **Mas** tem dois documentos em `.github/` (`interface-style.md` e `pdv-mobile.md`) que **definem a intenção** do dono do projeto: app é **PDV mobile** com **Clean Architecture + Provider + Dio**, estética Paramount+ light, idioma PT-BR.

Para ADR-0003, isso é informação rica — várias premissas ficam respondidas.

---

## 1. Estado real do repositório

| Item | Estado |
|---|---|
| Arquivos Dart em `lib/` | **1** (`main.dart`, contador boilerplate) |
| Dependências em `pubspec.yaml` | nenhuma além de `cupertino_icons` (sem HTTP, sem state mgmt) |
| Branches | `main` e `moises` — idênticas |
| Histórico | 6 commits, dois deles adicionando os `.md` em `.github/` |
| Compilação | `lib/main.dart` tem **erros de sintaxe** (faltam prefixos `ColorScheme.`, `MainAxisAlignment.`) — não compila como está |

**Conclusão:** o cliente é **greenfield**. Não há contratos de API a preservar do lado mobile.

## 2. O que os `.github/*.md` revelam (intenção do dono)

### 2.1 `pdv-mobile.md` — direção funcional

**Stack escolhida:**
- Flutter + Dart
- **Provider** para state management
- **Dio** (ou http) para chamadas REST
- **Clean Architecture** com Repositories isolando a API
- **PT-BR** em UI e código

**Posicionamento explícito:**
> *"A lógica de negócio reside na API Python/FastAPI. O Flutter deve apenas refletir o estado fornecido pelos endpoints."*

→ Confirma **backend rico, cliente fino**. Endpoints precisam carregar a regra; cliente não recalcula. Reforça importância da nossa estratégia de modelagem na API.

**Telas planejadas:**

| Tela | Funcionalidade | Implicação para a API |
|---|---|---|
| **Login** | Username + senha (sem cadastro/recuperação no MVP) | OK — `POST /auth/login` (existente) atende |
| **Dashboard / Home** | Faturamento em R$ + **tabela de vendas** com input de quantidade + botão "Add" | Precisa de endpoint de **vendas do dia** + lógica de "carrinho" no cliente, com finalização batendo numa API de venda |
| **Grade de Produtos (Estoque)** | Cards com quantidade, "Editar", "Excluir" | `GET /products/`, `PATCH /products/{id}`, `DELETE /products/{id}` (existem) — mas **falta endpoint de "estoque atual por produto"** |
| **Histórico de Pedidos** | Lista com "Detalhes", "Editar", "Excluir" | Mapeia ao `GET /pedidos/`, `GET /pedidos/{id}`, `PATCH/DELETE /pedidos/{id}` |

### 2.2 `interface-style.md` — direção visual

- Estética **Paramount+ light** — alto contraste, minimalista, **sem azul**
- Paleta P&B + verde sucesso (`#2ECC71`) para "Em Stock" + vermelho (`#E74C3C`) para crítico
- Tipografia sans-serif (Inter / Roboto / Montserrat), uppercase em títulos
- Componentes: borders 1px, raio 4px, botões P&B com largura total no login

Não impacta a API diretamente, mas mostra que o dono **pensou na experiência do operador** — reforça que o usuário do app é **funcionário da filial**, não consumidor final.

## 3. Premissas que ficam respondidas

Da lista do `scope-discussion.md`:

| Premissa | Resposta vinda dos docs |
|---|---|
| 1. Quem usa o app Flutter? | **Operador da filial** (vendedor) — confirmado por *"design limpo e intuitivo para o vendedor"* |
| 2. B2B/B2C? | **B2C principal** — fluxo descrito é venda balcão (PDV) |
| 4. Multi-tenant? | Já respondido fora — dono único |
| 5. Genérico/vertical? | Já respondido — laticínios |

**Continua em aberto:** fiscal (NFC-e), offline-first.

## 4. Tensões e ambiguidades nos docs

Pontos onde a intenção do dono **conflita** com decisões que tomamos ou com boas práticas — vale conversar com ele:

### 4.1 "Pedido" vs "Venda"
O `pdv-mobile.md` chama de **"Histórico de Pedidos"** o que descreve como vendas no balcão. Na nossa virada semântica (`architecture-laticinios.md`):
- `Order` = pedido de reposição/atacado (raro neste fluxo)
- `Sale` = venda no PDV (foco do app)

→ **Conversar com o dono:** ele quer dizer "histórico de vendas" e está usando "pedido" como sinônimo? Ou tem fluxo de pedido (encomenda) também? **Decisão impacta nomenclatura da API e UI.**

### 4.2 "Editar/Excluir pedido"
O doc lista "Editar" e "Excluir" pedidos como funcionalidade. Em PDV minimamente sério:
- **Editar venda finalizada não existe** — só cancelar (com estorno).
- **Excluir** apaga o histórico — incompatível com auditoria fiscal e contábil.

→ **Conversar com o dono:** essas operações são pra correção em tempo real (antes de fechar o caixa) ou pra "mexer" no histórico depois? Se é pós-fechamento, modelar como **cancelamento** (não delete).

### 4.3 Stack: Provider + Dio
São escolhas razoáveis mas datadas. Em 2026:
- **Riverpod** (sucessor do Provider) é o consenso da comunidade
- **Dio** funciona, mas `http` + interceptors funciona igual e tem menos magia

→ **Não brigar com o dono nesse ponto** — ele decidiu, está ok. Só vale flagar que se ele quiser modernizar depois, riverpod é o caminho. (Não é decisão da API.)

### 4.4 "Apenas username e password"
Sem recuperação de senha, sem 2FA, sem refresh token. Para MVP de um operador único da filial, ok. Mas:
- Se um operador esquecer a senha → não tem como recuperar (precisa de admin manual)
- Sem refresh token → após `EXPIRE_TIME_TOKEN`, operador é deslogado e perde estado

→ **Para v2:** considerar fluxo de reset de senha + refresh token. Não bloqueia MVP.

## 5. Gaps na API atual vs necessidades do app

Do que o app vai precisar e **a API ainda não oferece**:

| Necessidade | Endpoint atual | Gap |
|---|---|---|
| Faturamento do dia (Dashboard) | inexistente | Criar agregação por data |
| "Estoque atual" por produto | inexistente como número agregado | Hoje é coluna em `Product`; após ADR-0004, será derivada de `StockMovement` |
| "Vender produtos" (carrinho → venda) | inexistente como `Sale` | Hoje só tem `Order` (pedido) — vide ADR-0007 |
| Listagem com paginação | `GET /pedidos/` retorna tudo | App vai sofrer com volume — adicionar paginação |
| Sincronização offline | inexistente | Premissa em aberto — definir em ADR-0007 |

## 6. Implicações concretas para ADR-0003

ADR-0003 ("SalePoint como filial: separação de SalePoint, Operator e Customer") **fica reforçada** por essa análise:

- **`Operator`** é claramente uma entidade necessária — o app é usado pelo operador, não pelo dono nem pelo consumidor.
- **`Customer`** é separado de `SalePoint` (filial) — o consumidor compra na filial via PDV.
- **`SalePoint`** representa a filial física onde o operador trabalha — confirmado pelo design "tela de operador".

Adição que o app sugere para o ADR-0003:
- **Cada `Operator` pertence a uma `SalePoint`** (1 operador trabalha em 1 filial por vez; trocar de filial = trocar de operador ou login com escopo).
- **Login do operador retorna o `SalePoint` no qual ele opera**, pra o cliente saber qual estoque/caixa está usando.

## 7. Próximos passos práticos

1. **Conversar com o dono** sobre as ambiguidades em §4.1 e §4.2 (pedido vs venda; editar/excluir).
2. **Promover `architecture-laticinios.md` a ADR-0003** com as adições da §6.
3. **Não tentar "bater" com a Flutter atual** — ela é greenfield. Definimos a API; o cliente Flutter implementa contra ela.
4. **Manter `dairy-flutter-ref/` como referência viva** — re-clonar/atualizar quando o dono começar a implementar.
