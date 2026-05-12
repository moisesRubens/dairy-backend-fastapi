# ADR-0001 — Adoção de Architecture Decision Records

- **Status:** Aceito
- **Data:** 2026-05-05

## Contexto

Decisões arquiteturais (escolha de framework, padrão de auth, política de CORS, modelagem de domínio etc.) hoje vivem implícitas no código e na cabeça do dono do projeto. Conforme o backend cresce e novas pessoas (incluindo o time mobile Flutter) interagem com ele, fica caro reconstruir o "porquê" de cada decisão por arqueologia de git.

## Decisão

Adotar **Architecture Decision Records (ADRs)** versionados em `docs/adr/`, um arquivo por decisão, no formato:

```
docs/adr/NNNN-titulo-curto.md
```

Onde `NNNN` é numeração sequencial com 4 dígitos.

**Estrutura mínima de cada ADR:**
- **Status** — Proposto / Aceito / Rejeitado / Substituído por ADR-XXXX
- **Data** — ISO (YYYY-MM-DD)
- **Contexto** — qual problema motivou a decisão
- **Decisão** — o que foi decidido
- **Consequências** — efeitos positivos, negativos e neutros que assumimos

## Consequências

**Positivas**
- Time mobile e novos contribuidores entendem o porquê das decisões sem perguntar.
- Decisões antigas podem ser revisadas/substituídas explicitamente (status `Substituído por ADR-XXXX`) em vez de simplesmente esquecidas.
- PRs que mudam arquitetura têm um lugar natural de registro.

**Negativas**
- Custo marginal por decisão (poucos minutos para escrever).
- Risco de virar burocracia se aplicado a decisões triviais — ADRs devem ser reservados para decisões com impacto duradouro.

**Neutras**
- Não substitui documentação operacional (`overview.md`, `endpoints.md`) — são complementares.
