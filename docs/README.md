# Documentação — Dairy Backend (FastAPI)

Backend de um app Flutter de distribuição de laticínios. Esta pasta contém docs vivas mantidas em paralelo ao código.

## Índice

- [`overview.md`](overview.md) — visão geral: stack, estrutura de pastas, convenções, pontos de atenção
- [`api/endpoints.md`](api/endpoints.md) — inventário completo dos endpoints HTTP (referência para o cliente Flutter)
- [`logic/domain-model.md`](logic/domain-model.md) — modelos SQLAlchemy, diagrama ER, schemas Pydantic, histórico de migrations, domínio inferido
- [`logic/auth-and-security.md`](logic/auth-and-security.md) — fluxo de login, JWT, hashing, CORS, env vars, pontos de atenção
- [`logic/scope-discussion.md`](logic/scope-discussion.md) — working doc: evolução para PDV, Estoque robusto e Fidelidade — base para próximas ADRs
- [`logic/architecture-laticinios.md`](logic/architecture-laticinios.md) — **direção adotada**: foco em laticínios, dono único multi-filial; roadmap atualizado de ADRs
- [`logic/flutter-client-analysis.md`](logic/flutter-client-analysis.md) — análise do repo Flutter do dono: estado real + intenção declarada nos docs `.github/`
- [`logic/two-repos-workflow.md`](logic/two-repos-workflow.md) — como os dois repos (backend aqui + Flutter lá) coordenam via contrato
- [`logic/glossario.md`](logic/glossario.md) — **glossário canônico** pt-BR de entidades, colunas, enums e convenções (referência rápida da ADR-0004)
- [`logic/backlog.md`](logic/backlog.md) — **backlog de desenvolvimento** em 6 fases com tasks ordenadas por dependência
- [`logic/generic-core-strategy.md`](logic/generic-core-strategy.md) — alternativa rejeitada (núcleo genérico + presets) — mantido como registro
- [`adr/`](adr/) — Architecture Decision Records (decisões arquiteturais com contexto e consequências)
  - [`0001-record-architecture-decisions.md`](adr/0001-record-architecture-decisions.md) — adoção de ADRs
  - [`0002-domain-driven-routing.md`](adr/0002-domain-driven-routing.md) — reorganizar routers por domínio
  - [`0003-filiais-operadores-clientes.md`](adr/0003-filiais-operadores-clientes.md) — separar SalePoint em Filial + Operador + Cliente
  - [`0004-idioma-ptbr-dominio.md`](adr/0004-idioma-ptbr-dominio.md) — pt-BR como idioma do modelo de domínio
  - [`0005-pontos-extensao-verticais.md`](adr/0005-pontos-extensao-verticais.md) — `Produto.metadata` JSONB + `Filial.tipo` (porta aberta pra comércios similares sem over-engineering)

## Como manter

- Mudou rota / payload / schema → atualize `api/endpoints.md` no mesmo PR
- Mudou modelo / migration → atualize `logic/domain-model.md`
- Decisão arquitetural relevante → crie um novo ADR em `adr/NNNN-titulo.md` seguindo o template
- Achados de análise gerados por agentes ficam em `overview.md` e podem ser regenerados — preserve seções editadas manualmente marcando-as

## Contexto

- **Branch de trabalho:** `hzd4m`
- **Branch principal:** `main` (mantida pelo dono do projeto)
- Alterações fluem via PR `hzd4m → main`
