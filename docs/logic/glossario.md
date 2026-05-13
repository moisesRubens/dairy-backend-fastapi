# Glossário Canônico

> **Fonte:** ADR-0004 (Idioma pt-BR)
> **Regra:** se código e glossário divergirem, é bug — corrige um dos dois, **não cria sinônimo**.

Documento vivo. Atualize aqui antes de adicionar entidade ou termo novo no código.

---

## Entidades principais (domínio)

| Conceito | pt-BR | Tabela | Modelo SQLAlchemy | Schema Pydantic |
|---|---|---|---|---|
| Filial / ponto físico | filial | `filiais` | `Filial` | `FilialRespostaDTO`, `FilialCriarDTO` |
| Operador (funcionário) | operador | `operadores` | `Operador` | `OperadorRespostaDTO`, `OperadorCriarDTO` |
| Cliente (consumidor final) | cliente | `clientes` | `Cliente` | `ClienteRespostaDTO`, `ClienteCriarDTO` |
| Produto | produto | `produtos` | `Produto` | `ProdutoRespostaDTO`, `ProdutoCriarDTO` |
| Pedido (atacado/encomenda) | pedido | `pedidos` | `Pedido` | `PedidoRespostaDTO`, `PedidoCriarDTO` |
| Venda (PDV/balcão) | venda | `vendas` | `Venda` | `VendaRespostaDTO`, `VendaCriarDTO` |
| Item da venda | item da venda | `itens_venda` | `ItemVenda` | `ItemVendaRespostaDTO` |
| Item do pedido | item do pedido | `itens_pedido` | `ItemPedido` | `ItemPedidoRespostaDTO` |
| Pagamento | pagamento | `pagamentos` | `Pagamento` | `PagamentoCriarDTO` |
| Caixa (registradora) | caixa | `caixas` | `Caixa` | `CaixaRespostaDTO` |
| Turno de caixa | turno de caixa | `turnos_caixa` | `TurnoCaixa` | `TurnoCaixaRespostaDTO` |
| Local de estoque | local de estoque | `locais_estoque` | `LocalEstoque` | `LocalEstoqueRespostaDTO` |
| Movimento de estoque | movimento de estoque | `movimentos_estoque` | `MovimentoEstoque` | `MovimentoEstoqueRespostaDTO` |
| Lote | lote | `lotes` | `Lote` | `LoteRespostaDTO` |
| Conta de fidelidade | conta de fidelidade | `contas_fidelidade` | `ContaFidelidade` | — |
| Movimento de fidelidade | movimento de fidelidade | `movimentos_fidelidade` | `MovimentoFidelidade` | — |

## Colunas comuns (campos repetidos)

| Em pt-BR | Tipo | Notas |
|---|---|---|
| `nome` | string | Nome livre |
| `email` | string | Mantido (palavra universalizada) |
| `telefone` | string | Sem máscara no banco |
| `endereco` | string | Sem acento — convenção identificador |
| `cpf` | string(14) | Acrônimo brasileiro |
| `cnpj` | string(18) | Acrônimo brasileiro |
| `data_nascimento` | date | |
| `senha` | (não armazenado) | |
| `senha_hash` ou `password_hash` | string | **Decisão pendente** — tendência: `senha_hash` |
| `valor_total` | float | |
| `valor_unitario` | float | |
| `quantidade` | float | |
| `unidade` | string | kg, litro, unidade, caixa |
| `data` | datetime | |
| `data_pedido` / `data_venda` | datetime | |
| `observacao` | string | Texto livre |
| `status` | string ou bool | Conforme caso |
| `ativo` | bool | Quando faz mais sentido que `is_active` no domínio |
| `metadata` | JSONB nullable | **Extensão livre** (ADR-0005). Atributos vertical-específicos sem schema rígido. Aparece em `Produto`; pode aparecer em outras entidades por demanda |
| `tipo` | string | Classificação livre (ADR-0005). Aparece em `Filial` (`loja`, `deposito`, `kiosk`, `franquia`). Não é enum fechado |

## Termos técnicos que ficam em inglês

Em pt-BR seria forçado ou ambíguo:

| Termo | Onde aparece |
|---|---|
| `id`, `created_at`, `updated_at`, `deleted_at` | Colunas técnicas em todas as tabelas |
| `is_active`, `password_hash` | Colunas técnicas (vide decisão pendente acima sobre `senha_hash`) |
| `Token`, `access_token`, `token_type`, `Bearer` | Auth |
| `JWT` | Acrônimo |
| `Depends`, `HTTPException`, `APIRouter` | FastAPI |
| `Session`, `Query`, `relationship` | SQLAlchemy |
| `make_session`, `validate_token`, `get_current_operador` | Funções de scaffolding técnico |

## Valores de enum (domínio)

Usar pt-BR snake_case. Exemplos esperados:

- **Role do operador:** `caixa`, `gerente`, `dono`
- **Status de pedido:** `pendente`, `confirmado`, `cancelado`, `concluido`
- **Status de venda:** `aberta`, `concluida`, `cancelada`
- **Tipo de pagamento:** `dinheiro`, `cartao_debito`, `cartao_credito`, `pix`, `voucher`, `fiado`
- **Tipo de movimento de estoque:** `entrada`, `saida`, `transferencia`, `ajuste_inventario`, `perda`, `devolucao`
- **Unidade:** `kg`, `litro`, `unidade`, `caixa`, `grama`, `mililitro`

## Convenções de nomenclatura

| Categoria | Convenção | Exemplo |
|---|---|---|
| Tabela | snake_case plural | `movimentos_estoque` |
| Modelo SQLAlchemy | PascalCase singular | `MovimentoEstoque` |
| Schema Pydantic | PascalCase + sufixo de papel | `MovimentoEstoqueCriarDTO`, `MovimentoEstoqueRespostaDTO` |
| Coluna | snake_case | `valor_total` |
| Campo JSON | snake_case (mesmo da coluna) | `"valor_total"` |
| Path URL (single) | kebab-case | `/movimentos-estoque` |
| Função de domínio | snake_case | `criar_movimento_estoque(...)` |
| Função técnica | snake_case (inglês permitido) | `get_current_operador(...)` |
| Variável local | snake_case pt-BR | `total_pedido = ...` |
| Constante | UPPER_SNAKE_CASE | `LIMITE_MAXIMO_DESCONTO` |

## Sufixos padronizados em DTOs

| Sufixo | Uso | Exemplo |
|---|---|---|
| `CriarDTO` | Body de POST (criação) | `ProdutoCriarDTO` |
| `AtualizarDTO` | Body de PATCH (parcial) | `ProdutoAtualizarDTO` |
| `RespostaDTO` | Response body | `ProdutoRespostaDTO` |
| `FiltroDTO` | Query params estruturados | `PedidoFiltroDTO` |
| `ResumoDTO` | Versão reduzida (listagens) | `ProdutoResumoDTO` |

## Termos a **evitar** (sinônimos não-canônicos)

| Não usar | Usar | Motivo |
|---|---|---|
| `branch`, `point_of_sale`, `loja` | `filial` | Glossário canônico |
| `customer`, `consumidor`, `comprador` | `cliente` | Já é convenção em comércio BR |
| `seller`, `vendedor`, `cashier`, `funcionario` | `operador` | Mais genérico que "vendedor" (cobre gerente também) |
| `sale_point`, `sales_point`, `salepoint` | `filial` | — |
| `stock`, `estoque_qty` | `quantidade_estoque` ou conforme contexto | — |
| `sale_item`, `line_item` | `item_venda` | — |
| `withdrawal`, `outbound`, `retirada` | `movimento_estoque` (com `tipo='saida'`) | A `retirada_produto` antiga será substituída por movimento generalizado |
| `birthday`, `birth_date` | `data_nascimento` | — |
| `subtotal_value` | `valor_subtotal` | Adjetivo depois — quando soa natural |
