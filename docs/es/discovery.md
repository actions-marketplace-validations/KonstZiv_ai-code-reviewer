# Análisis de proyecto (Discovery)

AI ReviewBot incluye un sistema automático de **Project Discovery** que analiza tu repositorio antes de cada revisión de código. Discovery aprende tu stack, pipeline CI y convenciones para que el revisor proporcione feedback más inteligente y menos ruidoso.

---

## Cómo funciona

Discovery ejecuta un **pipeline de 4 capas** en el primer PR/MR:

| Capa | Fuente | Costo |
|------|--------|-------|
| **Capa 0** — Platform API | Lenguajes, árbol de archivos, topics de GitHub/GitLab API | Gratis (solo API) |
| **Capa 1** — Análisis CI | Parsing de GitHub Actions / GitLab CI / Makefile | Gratis (parsing local) |
| **Capa 2** — Archivos de config | Lectura de `pyproject.toml`, `package.json`, configs de linters | Gratis (lectura de archivos) |
| **Capa 3** — Interpretación LLM | IA interpreta datos ambiguos (solo cuando las capas 0-2 son insuficientes) | ~50-200 tokens |

Cada capa degrada de forma elegante — si una falla, el pipeline continúa con lo que tiene.

---

## Attention Zones

Discovery clasifica cada área de calidad en una de tres **Attention Zones** según la cobertura de tu CI/herramientas:

| Zona | Emoji | Significado | Comportamiento del revisor |
|------|-------|-------------|---------------------------|
| **Well Covered** | ✅ | Las herramientas de CI cubren esta área | El revisor la **omite** |
| **Weakly Covered** | ⚠️ | Cobertura parcial, hay margen de mejora | El revisor **presta atención** + sugiere mejoras |
| **Not Covered** | ❌ | No se detectó automatización | El revisor **se enfoca** en esta área |

### Ejemplo de zonas

| Área | Estado | Razón |
|------|--------|-------|
| Formatting | ✅ Well Covered | ruff format en CI |
| Type checking | ✅ Well Covered | mypy --strict en CI |
| Security scanning | ❌ Not Covered | No se detectó scanner de seguridad en CI |
| Test coverage | ⚠️ Weakly Covered | pytest se ejecuta pero sin umbral de cobertura |

---

## Qué sucede automáticamente

1. **Discovery analiza** tu repositorio (lenguajes, herramientas CI, archivos de config).
2. **Se calculan las Attention Zones** — cada área de calidad se clasifica como Well Covered, Weakly Covered o Not Covered.
3. **El prompt de revisión se enriquece** con instrucciones basadas en zonas (~200-400 tokens).
4. **El revisor omite** las áreas Well Covered y **se enfoca** en las Not Covered.

### Comentario de Discovery

Si Discovery encuentra **brechas** o zonas no cubiertas, publica un comentario resumen único en el PR/MR:

> ## 🔍 AI ReviewBot: Project Analysis
>
> **Stack:** Python (FastAPI) 3.13, uv
>
> **CI:** ✅ .github/workflows/tests.yml — ruff, mypy, pytest
>
> ### Not Covered (focusing in review)
> - ❌ **Security scanning** — No security scanner detected in CI
>   💡 Consider adding bandit or safety to your pipeline
>
> ### Could Be Improved
> - ⚠️ **Test coverage** — pytest runs but no coverage threshold enforced
>   💡 Add `--cov-fail-under=80` to enforce minimum coverage
>
> **Questions / Gaps:**
> - No security scanner detected in CI
>   *Question:* Do you use any security scanning tools?
>   *Assumption:* Will check for common vulnerabilities manually
>
> ---
> 💡 *Create `.reviewbot.md` in your repo root to customize.*

En **modo verbose** (`discovery_verbose=true`), el comentario también incluye las zonas Well Covered:

> ### Well Covered (skipping in review)
> - ✅ **Formatting** — ruff format in CI
> - ✅ **Type checking** — mypy --strict in CI

---

## Watch-Files y Caching

Discovery utiliza **watch-files** para evitar re-ejecutar el análisis LLM cuando la configuración del proyecto no ha cambiado.

### Cómo funciona

1. **Primera ejecución:** Discovery ejecuta el pipeline completo, el LLM devuelve una lista de `watch_files` (ej., `pyproject.toml`, `.github/workflows/tests.yml`).
2. **Ejecuciones posteriores:** Discovery calcula el hash de cada watch-file y lo compara con el snapshot almacenado en caché.
3. **Si no ha cambiado:** se usa el resultado en caché — **0 tokens LLM** consumidos.
4. **Si ha cambiado:** el LLM re-analiza el proyecto.

Esto significa que PRs repetidos en la misma rama cuestan **cero tokens adicionales** para discovery, siempre que los archivos de configuración observados no hayan cambiado.

!!! tip "Ahorro de tokens"
    En un proyecto típico, el segundo PR y los posteriores usan 0 tokens para discovery. Solo los cambios en config de CI, `pyproject.toml`, `package.json` o archivos similares disparan una nueva llamada LLM.

---

## Comando `discover` (CLI)

Puedes ejecutar discovery de forma independiente (sin crear una revisión) usando el comando `discover`:

```bash
ai-review discover owner/repo
```

### Opciones

| Opción | Corto | Descripción | Por defecto |
|--------|-------|-------------|-------------|
| `--provider` | `-p` | Proveedor Git | `github` |
| `--json` | | Salida en formato JSON | `false` |
| `--verbose` | `-v` | Mostrar todos los detalles (convenciones, herramientas CI, watch-files) | `false` |

### Ejemplos

```bash
# Discovery básico
ai-review discover owner/repo

# Salida JSON para scripting
ai-review discover owner/repo --json

# Verbose con todos los detalles
ai-review discover owner/repo --verbose

# Proyecto GitLab
ai-review discover group/project -p gitlab
```

!!! info "Compatibilidad hacia atrás"
    `ai-review` (sin subcommand) sigue ejecutando una revisión como antes. El subcommand `discover` es nuevo.

---

## `.reviewbot.md`

Crea un archivo `.reviewbot.md` en la raíz de tu repositorio para proporcionar contexto explícito del proyecto. Cuando este archivo existe, Discovery **omite el pipeline automático** y usa tu configuración directamente.

### Formato

```markdown
<!-- Auto-generated by AI ReviewBot. Feel free to edit. -->
# .reviewbot.md

## Stack
- **Language:** Python 3.13
- **Framework:** FastAPI
- **Package manager:** uv
- **Layout:** src

## Automated Checks
- **Linting:** ruff
- **Formatting:** ruff
- **Type checking:** mypy
- **Testing:** pytest
- **Security:** bandit
- **CI:** github_actions

## Review Guidance

### Skip (CI handles these)
- Import ordering (ruff handles isort rules)
- Code formatting and style (ruff format in CI)
- Type annotation completeness (mypy --strict in CI)

### Focus
- SQL injection and other OWASP Top 10 vulnerabilities
- API backward compatibility
- Business logic correctness

### Conventions
- All endpoints must return Pydantic response models
- Use dependency injection for database sessions
```

### Secciones

| Sección | Propósito |
|---------|-----------|
| **Stack** | Lenguaje principal, versión, framework, gestor de paquetes, layout |
| **Automated Checks** | Herramientas ya ejecutándose en CI (el revisor omitirá estas áreas) |
| **Review Guidance → Skip** | Áreas específicas que el revisor no debe comentar |
| **Review Guidance → Focus** | Áreas que quieres que reciban atención extra |
| **Review Guidance → Conventions** | Reglas específicas del proyecto que el revisor debe aplicar |

!!! tip "Auto-generación"
    Puedes dejar que Discovery se ejecute una vez, luego copiar sus hallazgos en `.reviewbot.md` y ajustar según necesites. El bot incluye un enlace en el pie sugiriendo este flujo de trabajo.

---

## Configuración

| Variable | Por defecto | Descripción |
|----------|-------------|-------------|
| `AI_REVIEWER_DISCOVERY_ENABLED` | `true` | Activar o desactivar el análisis de proyecto |
| `AI_REVIEWER_DISCOVERY_VERBOSE` | `false` | Siempre publicar comentario de discovery (por defecto: solo cuando hay brechas/zonas no cubiertas) |
| `AI_REVIEWER_DISCOVERY_TIMEOUT` | `30` | Timeout del pipeline de discovery en segundos (1-300) |

Establece `AI_REVIEWER_DISCOVERY_ENABLED` a `false` para omitir discovery completamente. El revisor seguirá funcionando, pero sin contexto específico del proyecto.

```yaml
# GitHub Actions — desactivar discovery
- uses: KonstZiv/ai-code-reviewer@v1
  with:
    github_token: ${{ secrets.GITHUB_TOKEN }}
    google_api_key: ${{ secrets.AI_REVIEWER_GOOGLE_API_KEY }}
    discovery_enabled: 'false'
```

---

## Modo silencioso (Silent Mode)

El comentario de discovery **no se publica** cuando:

1. **`.reviewbot.md` existe** en el repositorio — el bot asume que ya lo configuraste.
2. **No hay brechas ni zonas no cubiertas** — todo está Well Covered, no hay preguntas que hacer.
3. **Detección de duplicados** — ya se publicó un comentario de discovery en este PR/MR.

En los tres casos, discovery sigue ejecutándose y enriqueciendo el prompt de revisión — simplemente no publica un comentario visible.

---

## FAQ

### ¿Puedo desactivar discovery?

Sí. Establece `AI_REVIEWER_DISCOVERY_ENABLED=false`. El revisor funcionará sin contexto del proyecto, igual que antes de que se añadiera la funcionalidad de Discovery.

### ¿Discovery cuesta tokens LLM adicionales?

En la **primera ejecución**: las capas 0-2 son gratis (llamadas API y parsing local). La capa 3 (interpretación LLM) solo se invoca cuando las primeras tres capas no proporcionan suficientes datos — típicamente 50-200 tokens, lo cual es insignificante comparado con la revisión en sí (~1,500 tokens).

En **ejecuciones posteriores**: si tus watch-files no han cambiado, discovery usa el **resultado en caché** y cuesta **0 tokens**.

### ¿Puedo editar el `.reviewbot.md` auto-generado?

Sí, por supuesto. El archivo está diseñado para edición manual. Cambia lo que necesites — el parser tolera contenido adicional y secciones faltantes.

### ¿Se ejecuta discovery en cada PR?

Discovery enriquece el prompt de revisión en cada PR. La **llamada LLM** se cachea mediante watch-files (0 tokens cuando no hay cambios). El **comentario de discovery** se publica solo una vez (la detección de duplicados previene publicaciones repetidas).

### ¿Cómo veo todas las zonas incluyendo Well Covered?

Establece `AI_REVIEWER_DISCOVERY_VERBOSE=true`. Esto fuerza que el comentario de discovery siempre se publique e incluya todas las zonas (Well Covered, Weakly Covered, Not Covered).

### ¿Qué pasa si discovery tarda demasiado?

Establece `AI_REVIEWER_DISCOVERY_TIMEOUT` a un valor más alto (por defecto: 30 segundos, máximo: 300). Si discovery excede el timeout, la revisión continúa sin el contexto de discovery.

---

## Siguiente paso

- [Configuración →](configuration.md)
- [Integración GitHub →](github.md)
- [Integración GitLab →](gitlab.md)
