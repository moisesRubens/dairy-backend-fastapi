Execute na pasta `dairy-backend-fastapi`, com as dependencias do backend instaladas:

```powershell
.\venv\Scripts\python.exe -m unittest discover -s tests -v
```

Os testes usam `unittest`, `IsolatedAsyncioTestCase` e mocks da biblioteca
padrao. Verificam o retorno de `GET /sale-points/{id}/outbounds`, incluindo a
serializacao dos DTOs, lista vazia e filtro de data. A sessao SQLAlchemy e
simulada: nenhum banco real e consultado ou modificado. As funcoes sao
chamadas diretamente; autenticacao e validacao HTTP nao fazem parte destes
testes unitarios de retiradas. `test_auth_rest.py` usa TestClient para validar
o contrato HTTP, o formulario OAuth2, o logout sem corpo, os DTOs JSON e a
exigencia de autenticacao, com dependencias e controllers simulados.

Contrato REST atualizado (as rotas antigas foram removidas):

| Operacao | Endpoint | Entrada / retorno |
| --- | --- | --- |
| Login | `POST /auth/sessions` | Formulario `username`, `password`; 201 com token bearer |
| Logout | `DELETE /auth/sessions/current` | Bearer token; 204 sem corpo |
| Cadastro | `POST /sale-points` | JSON `name`, `password`, `email` opcional; 201 com `Location` |
| Listagem | `GET /sale-points` | Bearer token |
| Perfil | `GET /sale-points/{id}` | Bearer token |
| Edicao | `PATCH /sale-points/{id}` | Bearer token e JSON com campos opcionais |
| Exclusao | `DELETE /sale-points/{id}` | Bearer token; 204 sem corpo, 404 se inexistente |
| Exclusao da colecao | `DELETE /sale-points` | Bearer token; 204 sem corpo |
| Pedidos | `/sale-points/{id}/orders` | GET, POST, DELETE |
| Retiradas | `/sale-points/{id}/outbounds` | GET, POST, PATCH, DELETE |

O app Flutter foi atualizado junto com a API. Outros clientes devem migrar
as URLs e enviar cadastro/edicao como JSON. O login preserva o formulario
OAuth2 para manter a autenticacao pelo Swagger.

O CRUD usa respostas `SalePointResponseDTO`, sem senha. PATCH preserva campos
omitidos; `email: null` limpa o email. Nomes em branco, campos desconhecidos,
IDs nao positivos e valores invalidos retornam 422. Nomes duplicados (sem
diferenciar maiusculas) retornam 409 no cadastro e na edicao. GET e PATCH
de pontos inexistentes retornam 404.

`test_sale_points.py` inclui testes unitarios de validacao, PATCH e mapeamento
de excecoes e testes de integracao com controllers e services reais e SQLite
em memoria. O teste de sessoes usa hashing, JWT e revogacao reais com segredo
exclusivo dos testes; nenhum dado do banco da aplicacao e alterado.

No mobile, execute `flutter test --no-pub`. `auth_service_test.dart` cobre
perfil com MockClient; `sale_point_http_integration_test.dart` integra
AuthService, DTOs e preferencias com HTTP real em servidor local simulado.

## Pedidos, produtos e retiradas

| Recurso | Operacoes | Contrato |
| --- | --- | --- |
| `/orders` | GET, DELETE | Filtros GET: `date` (ISO), `description`, `status` (booleano); DELETE 204 |
| `/orders/{id}` | GET, PATCH, DELETE | PATCH de `description`, `status`, `order_date`; DELETE 204 |
| `/sale-points/{id}/orders` | POST, GET | POST 201; itens com `product_id` e `quantity` positiva ou uma unidade explicita |
| `/products` | GET, POST, DELETE | POST recebe lote JSON e retorna lista simples com 201; lote atomico; DELETE 204 |
| `/products/{id}` | GET, PATCH, DELETE | PATCH parcial; DELETE 204 |
| `/outbounds` | GET | Lista agrupada por ponto de venda; filtro `date` ISO |
| `/outbounds/{id}` | GET, PATCH | PATCH JSON com `remaining_quantity`, `observation` e/ou `status` |
| `/sale-points/{id}/outbounds` | POST | Lote `produtos` com `product_id`, `quantidade`, `unidade`; 201 com lista de retiradas |

Rotas antigas `/pedidos` e `/outbounds/{id}/quantity` foram removidas. A URL
canonica das colecoes nao tem barra final. Erros usam 404 para recurso
inexistente, 409 para duplicidade/saldo insuficiente/retirada encerrada e 422
para entrada invalida. Todas estas rotas exigem autenticacao.

Produtos recebem `name`, `price` e exatamente uma unidade de estoque entre
`amount`, `kg`, `liters`. Zero e valido; -1 do Flutter e convertido em null.
Ao trocar a unidade por PATCH, envie null nas unidades que devem ser limpas.
Campos omitidos permanecem intactos.

Pedidos calculam valor total e atualizam saldo das retiradas na criacao.
PATCH altera apenas metadados: itens e totais derivados nao podem ser
sobrescritos diretamente. Respostas de pedidos usam `date`, `item_order`
e `price` nos itens. Quantidades fracionarias sao aceitas para kg e litros.

PATCH de retirada ajusta o estoque pela diferenca de `remaining_quantity`.
`status: false` devolve o saldo e encerra a retirada sem apagar o historico;
repetir o encerramento nao devolve o saldo duas vezes. Uma retirada encerrada
nao pode ser reaberta. `observation: null` limpa a observacao. Quantidades
vendidas, unidade e totais sao derivados e nao recebem PATCH direto.

`test_resource_rest.py` cobre controllers, validacao e integracao HTTP com
SQLite em memoria, incluindo rollback e estoque em amount/kg/liters.
No Flutter, `resource_service_test.dart` usa MockClient e
`resource_http_integration_test.dart` usa servidor HTTP local com API e
persistencia local simuladas. Os testes anteriores de produtos continuam
cobrindo leitura, edicao e exclusao com HTTP real.

Pedidos aceitam `order_status` (`pago`, `pendente` ou `desconto`), mantendo `status` booleano para clientes existentes. Para `desconto`, `total_value` representa o valor final, maior que zero e no maximo o total calculado dos produtos. A resposta e a listagem preservam `order_status` e o total final. `test_resource_rest.py` cobre criacao, leitura e rollback sem consumo de estoque em valores invalidos; `test_order_status_migration.py` valida a migracao em SQLite isolado.
