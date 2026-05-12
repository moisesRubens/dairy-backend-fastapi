# Workflow entre Backend e Flutter (dois repos separados)

> **Pergunta que motivou este doc:** "vai ser tudo por aqui?"
> **Resposta curta:** o trabalho de **API** é todo aqui. O **cliente Flutter** mora em outro repo (não nosso) — coordenamos por contrato.

---

## 1. Os dois repos e o que cada um faz

| Repo | Quem é dono | O que faz | Onde fica |
|---|---|---|---|
| **dairy-backend-fastapi** (este) | colaborador (você, branch `hzd4m`) | API FastAPI, modelos, migrations, ADRs, docs | `/Users/hzd4m/Desktop/Zd4/dairy-backend-fastapi` |
| **moisesRubens/dairy** | dono do projeto (Moisés) | Cliente Flutter (PDV mobile) | `/Users/hzd4m/Desktop/Zd4/dairy-flutter-ref` (clone read-only de referência) |

**Regra geral:** os repos ficam separados. **Não vamos fundir** em monorepo. Cada um tem ciclo próprio (releases, deploy, testes).

## 2. Onde se trabalha cada coisa

### Aqui (backend)
- Toda decisão de **API**: rotas, payloads, autenticação, persistência
- Toda decisão de **modelo de dados**: entidades, relações, migrations
- Toda **ADR** que afete contrato ou domínio
- Toda **doc operacional**: `docs/api/`, `docs/logic/`, `docs/adr/`
- Branch de trabalho: `hzd4m` → PR para `main` (revisada pelo dono)

### Lá (cliente Flutter)
- Telas, navegação, state management (Provider)
- Repositories que consomem nossos endpoints
- Theming (ver `.github/interface-style.md` do repo deles)
- Branch de trabalho: do **dono** — ele decide se aceita PR de fora

### Onde **não** trabalhar
- ❌ Não criar `lib/` ou código Flutter dentro deste repo
- ❌ Não criar pasta `backend/` dentro do repo Flutter
- ❌ Não duplicar a doc da API no repo Flutter — link para o nosso é suficiente

## 3. Como os dois conversam (contrato)

A coordenação entre backend e cliente é por **contrato**, não por código compartilhado:

```
                      [contrato]
   Backend FastAPI  ◄────────────►  Cliente Flutter
   (este repo)                     (repo do dono)
        │                                  │
        ▼                                  ▼
  /docs (OpenAPI auto)        repositories/*.dart
  docs/api/endpoints.md       models/*.dart com fromJson
```

### Fontes de verdade do contrato (ordem de prioridade)

1. **OpenAPI gerado pelo FastAPI** em `/docs` (Swagger UI) e `/openapi.json` — é a verdade técnica gerada do código, atualizada a cada deploy.
2. **`docs/api/endpoints.md`** — versão curada, em PT-BR, com observações que o OpenAPI não captura (gotchas, status codes não-padrão, fluxos multi-passo).
3. **ADRs** — racional das decisões; ler quando dúvida sobre o "porquê".

### Como o dono usa
- Antes de implementar uma tela, abre `docs/api/endpoints.md` e/ou `/docs` da API.
- Para gerar models Dart: `dart run build_runner` com `json_serializable` apontando para os schemas Pydantic (manualmente, ou ferramentas como `openapi-generator` rodando contra `/openapi.json`).

## 4. Quando muda o contrato (breaking change)

Toda mudança que afeta o cliente Flutter precisa de **comunicação explícita**:

### Checklist quando uma ADR muda contrato
1. [ ] ADR aprovada e mergeada na `main` deste repo
2. [ ] `docs/api/endpoints.md` atualizado refletindo o novo contrato
3. [ ] **Tag de release** com versão semântica (`v0.X.0` para breaking, `v0.X.Y` para aditivo)
4. [ ] **Changelog** no PR ou em `CHANGELOG.md` listando o que mudou
5. [ ] **Issue aberta no repo Flutter** (ou comunicação direta com o dono) avisando: "API v0.X muda os endpoints A, B, C — ver doc atualizada"
6. [ ] **Período de paralelo** (Fase 1 do ADR-0002): manter rotas antigas marcadas `[deprecated]` por N releases até cliente migrar

### Quando não é breaking
- Adição de campos opcionais no response → cliente continua funcionando
- Adição de novos endpoints → cliente ignora
- Bugfix sem mudar contrato → libera

## 5. Versionamento da API (estratégia)

Recomendação para quando o produto crescer:

- **Hoje:** sem prefixo de versão (`/products/`, `/orders/`).
- **Após ADR-0002** (refactor de routing) e ADR-0003 (Branch/Operator/Customer): considerar `/v1/` como prefixo, abrindo caminho pra `/v2/` futuro sem partir cliente.
- **Política:** breaking change requer nova versão; cliente migra entre versões em janela combinada.

Não bloqueante hoje, mas não custa nada já incluir o prefixo na próxima refatoração de rotas.

## 6. Quem pode fazer o quê em cada repo

> **Atualização (2026-05-07):** você (`hzd4m`) tem acesso de commit aos **dois** repos. O quadro abaixo distingue suas permissões das minhas.

| Ação | Você (hzd4m) — Backend | Você (hzd4m) — Flutter | Eu (Claude) — Backend | Eu (Claude) — Flutter |
|---|---|---|---|---|
| Ler arquivos | ✅ | ✅ | ✅ | ✅ (via `../dairy-flutter-ref/`) |
| Editar arquivos | ✅ | ✅ | ✅ | ❌ (sem permissão de push) |
| Criar branch / commit | ✅ branch `hzd4m` → PR | ✅ direto na branch acordada com o dono | ✅ na sua branch | ❌ |
| Abrir PR | ✅ pra `main` | ✅ pra `main` ou branch acordada | ✅ | ❌ |
| Tag de release | ✅ | ✅ | ⚠️ pede confirmação primeiro | — |

**Tradução prática:**
- Você é a **ponte** entre os dois repos. Toda mudança que afeta os dois passa por você.
- Eu posso **rascunhar código Dart** aqui no backend pra você levar (ex: `_flutter-drafts/` no .gitignore, ou copiar pra área externa). Mas **eu não commito direto no repo do Flutter** — você faz o copy+commit lá.
- Se preferir, podemos **clonar o repo do Flutter como sibling editável** (não só `dairy-flutter-ref/` como referência) — basta combinar.

### Quer que eu trabalhe no Flutter também? — caminho recomendado

Como você tem acesso aos dois, vale considerar **clonar o `moisesRubens/dairy` como sibling editável** (ex: `../dairy-flutter/` ao lado do `dairy-flutter-ref/`). Eu trabalho lá em uma branch sua, você revisa, e abre PR no repo do dono. Esse setup faz com que:

- Posso escrever `models/`, `repositories/`, `pages/` Dart contra os contratos da API que eu mesmo defini aqui — alta consistência.
- Você revisa e empurra para o repo do dono via PR (com sua autoria).
- Os dois repos seguem ritmo síncrono: PR de backend e PR de Flutter saem em par quando há quebra de contrato.

Diferença vs `dairy-flutter-ref/` atual:
- `dairy-flutter-ref/` = read-only, espelho do que o dono publicou.
- `dairy-flutter/` (proposto) = working copy editável, branch sua, PR pro dono.

Me avise se quer adotar essa convenção e eu monto.

## 7. Como atualizar o clone de referência

O `dairy-flutter-ref/` continua sendo só leitura — espelho do que o dono publicou. Atualizar quando ele codar algo:

```
cd ../dairy-flutter-ref
git fetch --all --prune
git checkout main && git pull
# ou inspecionar branches dele:
git branch -a
git checkout origin/<branch-do-dono>
```

## 8. Cenário recomendado de comunicação

Pra fluir bem com o dono:

1. **Antes de começar uma ADR que muda contrato:** você avisa o dono ("vou propor mudança que afeta endpoint X").
2. **Quando ADR é mergeada na main do backend:** você comunica com link da ADR, doc atualizada e tag de release.
3. **Se você for quem implementa o Flutter:** PRs de backend e Flutter saem em par; o dono revisa o Flutter, você revisa o backend (ou inverso).
4. **Se o dono implementar:** ele abre issue **aqui** referenciando o endpoint quando tiver dúvida; respondemos com exemplo de payload/erro/edge case.
5. **Quando algo não bater em runtime:** logs/print do request → debugamos pelo lado da API.

Esse loop mantém os repos sincronizados sem precisar de monorepo.
