# ADR-0004 — Idioma do modelo de domínio: Português Brasileiro (pt-BR)

- **Status:** Proposto
- **Data:** 2026-05-07
- **Relacionado:** ADR-0002 (paths), ADR-0003 (entidades de filial/operador/cliente)
- **Referências:** [`docs/logic/glossario.md`](../logic/glossario.md), `dairy-flutter-ref/.github/pdv-mobile.md` (decisão do dono pelo PT-BR)

## Contexto

O código atual mistura idiomas sem regra:

| Em inglês | Em pt-BR |
|---|---|
| `SalePoints`, `Order`, `Product`, `ItemsOrder` | `RetiradaProduto` |
| Colunas: `name`, `price`, `email`, `amount` | Colunas: `unidade`, `quantidade`, `observacao`, `data` |
| Paths: `/products`, `/auth`, `/outbounds` | Paths: `/pedidos` |

Essa inconsistência tem custo:
- Cliente Flutter precisa traduzir cada JSON key — ou pior, mistura português e inglês na UI
- Mensagens de erro chegam em inglês quando a UI é em pt-BR
- Devs decidem caso-a-caso → falta de convenção
- Logs/erros que escapam pra usuário final ficam em inglês

O cliente Flutter previsto ([`pdv-mobile.md`](../../../dairy-flutter-ref/.github/pdv-mobile.md)) é explícito: *"Idioma: Todo o projeto (UI e Documentação) deve ser em Português (Brasil)."* Os usuários finais (dono, operadores em filiais brasileiras) também são pt-BR.

## Decisão

Adotar **pt-BR como idioma do modelo de domínio**, mantendo inglês onde a convenção técnica do framework dita.

### O que vai em pt-BR

| Categoria | Exemplo antes | Exemplo depois |
|---|---|---|
| Tabelas | `sales_points`, `products` | `filiais`, `produtos` |
| Modelos SQLAlchemy | `SalePoints`, `Product` | `Filial`, `Produto` |
| Colunas | `name`, `price`, `email` | `nome`, `preco`, `email` |
| Schemas Pydantic | `OrderRequestDTO`, `ProductResponseDTO` | `PedidoCriarDTO`, `ProdutoRespostaDTO` |
| Campos JSON na API | `name`, `total_value` | `nome`, `valor_total` |
| Path API | `/products`, `/sales-points` | `/produtos`, `/filiais` |
| Módulos Python | `app/orders/`, `app/products/` | `app/pedidos/`, `app/produtos/` |
| Funções de domínio | `create_product()`, `validate_order()` | `criar_produto()`, `validar_pedido()` |
| Valores de enum de domínio | `active`, `cancelled` | `ativo`, `cancelado` |
| Mensagens de erro user-facing | `"Insufficient stock"` | `"Estoque insuficiente"` |

### O que continua em inglês

Conceitos técnicos universais e padrões consagrados do framework — traduzir aqui causa mais confusão que benefício:

- **Identidade técnica:** `id`, `created_at`, `updated_at`, `deleted_at`, `is_active`, `password_hash`
- **Auth/JWT:** `Token`, `JWT`, `access_token`, `token_type`, `OAuth2PasswordBearer`, `Bearer`
- **HTTP:** verbos, status codes, headers (`Authorization`, `Content-Type`)
- **Decorators e imports do framework:** `Depends`, `APIRouter`, `HTTPException`, `Field`
- **Funções de scaffolding técnico:** `make_session()`, `get_current_operador()`, `validate_token()` — nome técnico em inglês mas referenciando entidades em pt-BR
- **Exceções/logs internos** (não vistos pelo usuário final): inglês ok; pt-BR também ok — não bloqueante

### Regras de transliteração e estilo

1. **Sem acento em identificadores.** `endereco`, não `endereço`. Python aceita PEP 3131 mas convenção é evitar (problemas de IDE, ferramentas, busca).
2. **snake_case** em colunas, campos JSON, funções, variáveis (`valor_total`, `data_nascimento`, `criar_pedido`).
3. **PascalCase** em classes (`Filial`, `MovimentoEstoque`, `TurnoCaixa`).
4. **kebab-case** em paths URL multi-palavra (`/movimentos-estoque`, `/turnos-caixa`).
5. **Plural vs singular:**
   - Tabelas → plural (`filiais`, `produtos`, `pedidos`)
   - Modelos → singular (`Filial`, `Produto`, `Pedido`)
   - Paths de coleção → plural (`/filiais`, `/produtos`)
6. **Acrônimos brasileiros** (CPF, CNPJ, NFCe, SEFAZ, ANVISA): maiúsculas, mantidos como estão.
7. **Termos com aceitação universal sem boa tradução** (token, hash, log, deploy, cache, stream): mantidos em inglês mesmo no domínio.

### Glossário canônico

Glossário completo extraído desta ADR e mantido vivo em [`docs/logic/glossario.md`](../logic/glossario.md). Qualquer divergência entre código e glossário é bug (corrige um ou outro, **não cria sinônimo**).

## Implicações para ADRs anteriores

- **ADR-0002** (roteamento): paths usados como exemplo (`/sales-points`, `/orders`, `/products`) passam a ser `/filiais`, `/pedidos`, `/produtos`. Atualizar a ADR junto com a implementação.
- **ADR-0003** (separação de entidades): `Branch + Operator + Customer` → **Filial + Operador + Cliente**. ADR-0003 reescrita pra refletir.

Como ambas estão em status `Proposto` e ainda **não foram implementadas**, editar in-place é seguro (sem migration histórica afetada).

## Alternativas consideradas

**A) Manter mistura atual (status quo).** Nenhum benefício, custos crescentes. Rejeitado.

**B) Tudo em inglês (incluindo o que já está em pt-BR).** Comum em projetos open-source globais e facilita ferramentas de IA. Mas:
- Cliente Flutter explicitou pt-BR
- Usuários finais (operadores em filiais brasileiras) leem em pt-BR
- Doc do dono é em pt-BR
Ir contra esses três cria fricção desnecessária. Rejeitado.

**C) Pt-BR só nos campos de saída (JSON), modelos em inglês.** Adiciona uma camada de tradução em todo lugar (Pydantic alias). Duplica nomes mentalmente. Rejeitado.

**D) Pt-BR no domínio, inglês no técnico (esta).** Aceito.

## Consequências

**Positivas**
- API e cliente Flutter falam mesma língua → dispensa camada de tradução em models/repositories.
- Logs e erros user-facing já vêm em pt-BR → menos código de localização.
- Domínio fica natural: fala-se "filial", não "branch", em comércio brasileiro. Diminui distância entre código e conversa de negócio.
- Onboarding de devs brasileiros mais natural.

**Negativas**
- Devs internacionais (se algum dia) precisam aprender o glossário.
- Buscar por termos técnicos universais ("Customer") em editor não acha — busca-se "Cliente".
- Bibliotecas em inglês (FastAPI, SQLAlchemy) ficam contrastando com domínio em pt-BR — fronteira aceita.
- Ferramentas de IA / code-gen têm leve preferência por inglês (impacto residual).

**Neutras**
- Não muda nenhuma decisão técnica de arquitetura.
- Não impede internacionalizar UI futuramente (i18n é problema do cliente, não do domínio).

## Critério de aceite

- [ ] [`docs/logic/glossario.md`](../logic/glossario.md) publicado e mantido como referência viva
- [ ] ADR-0003 reescrita com nomes em pt-BR (Filial, Operador, Cliente)
- [ ] ADR-0002 com paths atualizados para pt-BR
- [ ] Convenção aplicada em **toda** nova migração e feature daqui em diante (revisão de PR enforça)
- [ ] Migração dos modelos atuais (`SalePoints`, `Order`, `Product`, etc.) para pt-BR é parte da migration de ADR-0003

## Pontos não bloqueantes

- **Mensagens de log internas:** pode ficar em pt-BR ou inglês caso a caso. Inclinação: user-facing → pt-BR; logs internos de debug → o que for mais claro.
- **Comentários e docstrings:** pt-BR é a convenção, mas comentário em inglês onde explicar uma sutileza técnica do framework é aceitável.
- **Identificadores em testes (pytest):** seguir mesma regra do código de produção.
- **Strings em arquivos de migration:** os nomes das tabelas/colunas mudam, mas IDs de revisão Alembic são técnicos.
