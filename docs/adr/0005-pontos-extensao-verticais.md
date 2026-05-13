# ADR-0005 — Pontos de extensão minimais pra futuras verticais

- **Status:** Proposto
- **Data:** 2026-05-12
- **Relacionado:** ADR-0003 (Filial+Operador+Cliente), ADR-0004 (pt-BR), `architecture-laticinios.md`, `generic-core-strategy.md` (alternativa rejeitada)

## Contexto

A decisão estratégica foi **focar em laticínios** ([`architecture-laticinios.md`](../logic/architecture-laticinios.md)) e **rejeitar** o modelo "núcleo genérico + presets verticais" ([`generic-core-strategy.md`](../logic/generic-core-strategy.md)) por YAGNI — sem demanda real de outros ramos, a complexidade não se paga.

Porém, é razoável imaginar que o produto cresça para **comércios similares** (padaria, açougue, distribuidora de bebidas, hortifrúti) ou que **outros donos de laticínios** queiram contratar (SaaS de single-vertical).

A pergunta é: quanto custa **deixar uma porta aberta** sem cair na armadilha do over-engineering rejeitado pela `generic-core-strategy`?

Resposta: alguns campos opcionais bem colocados custam praticamente nada agora e derrubam o custo de adaptação futura. **ADR-0005 trava esses pontos** sem reabrir a discussão do preset system.

## Decisão

Adicionar **três pontos de extensão** ao modelo de domínio. Todos opcionais, todos sem regra rígida — caixa-livre intencional.

### 1. `Produto.metadata` — JSONB nullable

Coluna JSONB em `produtos`, default `null` ou `{}`.

```sql
ALTER TABLE produtos ADD COLUMN metadata JSONB NULL;
```

**Uso esperado por ramo:**

| Ramo | Chaves típicas em `metadata` |
|---|---|
| Laticínios | `{"validade_dias_padrao": 30, "temperatura_min": 2, "temperatura_max": 8, "pasteurizado": true}` |
| Padaria | `{"validade_horas": 48, "produzido_dia": true}` |
| Açougue | `{"corte": "alcatra", "origem": "bovino"}` |
| Distribuidora | `{"teor_alcoolico": 4.5, "volume_ml": 600}` |
| Farmácia | `{"principio_ativo": "...", "tarja": "vermelha", "requer_receita": true}` |

**Regras:**

- **Sem schema validation rígido na escrita** — Pydantic aceita `dict[str, Any]`. Caixa livre.
- **Queries críticas nunca dependem de `metadata`** — se uma chave virar regra de negócio, **promove pra coluna** (não consulta JSON em hot path).
- **`metadata` é OBSERVACIONAL**, não estrutural.
- Indexes GIN em `metadata` são permitidos pra busca textual eventual, não pra regra de negócio.

### 2. `Filial.tipo` — string default `'loja'`

Coluna `tipo` em `filiais`, default `'loja'`.

```sql
ALTER TABLE filiais ADD COLUMN tipo VARCHAR(20) NOT NULL DEFAULT 'loja';
```

**Valores típicos:**

- `loja` — filial padrão com venda balcão
- `deposito` — depósito central, sem venda direta
- `kiosk` — ponto de venda menor (food truck, feira)
- `franquia` — filial operada por terceiro sob mesmo CNPJ
- `online` — canal de venda digital (futuro)

**Regras:**

- **Não é enum fechado.** Lojistas futuros podem usar valores próprios sem migration.
- Endpoint pode filtrar (`GET /filiais/?tipo=loja`) mas **não impede** valor novo.
- Lógica de UI/relatórios pode tratar diferente (ex: ocultar `deposito` no seletor do PDV), mas backend é agnóstico.

### 3. Regra de naming: zero referências a "laticínios" no código

**Regra puramente cultural, sem coluna nova:**

Nunca usar termos específicos de laticínios em **nomes** de:
- Tabelas, colunas, funções, classes, módulos, paths, variáveis

Ou seja: **nada** de `LeiteProduto`, `QueijoLote`, `criar_iogurte()`. Sempre genérico (`Produto`, `Lote`, `criar_produto()`).

**Onde "laticínios" pode aparecer:**
- Strings literais de UI ("Bem-vindo à Laticínios Boa Esperança")
- Dados (seed de produtos, descrições)
- Documentação/comentários
- Nome da organização (se houver)

Essa regra **não tem como falhar silenciosamente** — basta revisão de PR.

## Alternativas consideradas

**A) Não fazer nada agora.** Se aparecer demanda de outro ramo, refator na hora. Risco: refator pode ser feio se já houver volume de dados ou se "laticínios" vazou pelo código. **Rejeitada** porque o custo de prevenir é trivial.

**B) Sistema completo de presets verticais** ([`generic-core-strategy.md`](../logic/generic-core-strategy.md)). **Já rejeitada** por YAGNI. Esta ADR é o ponto médio defensivo.

**C) Adicionar mais campos genéricos** (ex: `Cliente.metadata`, `Venda.metadata`). **Rejeitada por ora** — preferimos não criar `metadata` em toda entidade preventivamente. Se demanda real surgir, adiciona ADR posterior. YAGNI vale aqui também.

**D) Esta ADR (Produto.metadata + Filial.tipo + regra cultural).** **Aceita** — custo trivial, paga juros desproporcionais se algum vertical adjacente aparecer.

## Consequências

**Positivas**
- Adaptar pra padaria/açougue/distribuidora vira semana de trabalho, não mês
- Lojistas existentes podem usar `metadata` pra dados que não merecem coluna (campanhas, observações estruturadas)
- `Filial.tipo` destrava UX de seleção e relatórios sem refactor

**Negativas**
- `metadata` JSONB é "caixa-preta" se mal-usado — disciplina de PR é o controle
- `Filial.tipo` sem enum significa que typos viram valores válidos — UI deve oferecer dropdown com sugestões

**Neutras**
- Não introduz nada de multi-tenant nem de preset
- Compatível com ADRs anteriores (0003, 0004)

## Critério de aceite

- [ ] `produtos.metadata` JSONB nullable na migration de ADR-0003
- [ ] `filiais.tipo` VARCHAR(20) DEFAULT 'loja' na migration de ADR-0003
- [ ] Pydantic schemas (`ProdutoCriarDTO`, `ProdutoRespostaDTO`, `FilialCriarDTO`, `FilialRespostaDTO`) refletem os campos
- [ ] Glossário [`glossario.md`](../logic/glossario.md) atualizado com `metadata` e `tipo`
- [ ] Política "zero referências a laticínios no código" documentada na seção de convenções

## Pontos em aberto (não bloqueiam)

- **Indexação GIN em `metadata`** — só quando aparecer caso de uso real
- **Schema validation opcional em `metadata`** — pode vir como ADR-0005.1 se algum lojista pedir formulário guiado de cadastro
- **Versionamento do schema do `metadata`** — só preocupar se chave virar regra (e aí promove pra coluna)
