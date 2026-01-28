# GitHub: Ejemplo Avanzado

Configuración lista para producción con todas las mejores prácticas.

---

## Paso 1: Añadir un Secreto

`Settings → Secrets and variables → Actions → New repository secret`

| Nombre | Valor |
|------|-------|
| `GOOGLE_API_KEY` | Tu clave API de Gemini |

---

## Paso 2: Crear el Archivo

`.github/workflows/ai-review.yml`:

```yaml
name: AI Code Review

on:
  pull_request:
    types: [opened, synchronize, reopened]
    # Opcional: filtro de archivos
    # paths:
    #   - '**.py'
    #   - '**.js'
    #   - '**.ts'

# Cancelar ejecución anterior con nuevo commit
concurrency:
  group: ai-review-${{ github.event.pull_request.number }}
  cancel-in-progress: true

jobs:
  review:
    name: AI Review
    runs-on: ubuntu-latest

    # No ejecutar para PRs de forks (secretos no disponibles)
    if: github.event.pull_request.head.repo.full_name == github.repository

    # No bloquear PR si la revisión falla
    continue-on-error: true

    # Protección de timeout
    timeout-minutes: 10

    permissions:
      contents: read
      pull-requests: write

    steps:
      - name: Run AI Code Review
        uses: KonstZiv/ai-code-reviewer@v1
        with:
          google_api_key: ${{ secrets.GOOGLE_API_KEY }}
          language: uk
          language_mode: adaptive
          log_level: INFO
```

---

## Qué Incluye

| Funcionalidad | Estado | Descripción |
|---------|--------|-------------|
| Comentarios en línea | :white_check_mark: | Con Apply Suggestion |
| Concurrencia | :white_check_mark: | Cancela ejecuciones anteriores |
| Filtro de forks | :white_check_mark: | Omite PRs de forks |
| Timeout | :white_check_mark: | Máximo 10 minutos |
| No bloqueante | :white_check_mark: | PR no bloqueado |
| Idioma personalizado | :white_check_mark: | `language: uk` |

---

## Variaciones

### Con Filtro de Archivos

```yaml
on:
  pull_request:
    paths:
      - 'src/**'
      - '**.py'
    paths-ignore:
      - '**.md'
      - 'docs/**'
```

### Con Filtro de Ramas

```yaml
on:
  pull_request:
    branches:
      - main
      - develop
```

### Con Modelo Personalizado

```yaml
- uses: KonstZiv/ai-code-reviewer@v1
  with:
    google_api_key: ${{ secrets.GOOGLE_API_KEY }}
    gemini_model: gemini-1.5-pro  # Modelo más potente
```

### Con Logs DEBUG

```yaml
- uses: KonstZiv/ai-code-reviewer@v1
  with:
    google_api_key: ${{ secrets.GOOGLE_API_KEY }}
    log_level: DEBUG
```

---

## Opciones de Action

| Input | Descripción | Por defecto |
|-------|-------------|---------|
| `google_api_key` | Clave API de Gemini | **requerido** |
| `github_token` | Token de GitHub | `${{ github.token }}` |
| `language` | Idioma de respuesta | `en` |
| `language_mode` | `adaptive` / `fixed` | `adaptive` |
| `gemini_model` | Modelo Gemini | `gemini-2.0-flash` |
| `log_level` | Nivel de log | `INFO` |

---

## Solución de Problemas

### La Revisión No Aparece

1. Revisa los logs del workflow
2. Verifica que no sea un PR de fork
3. Verifica `permissions: pull-requests: write`

### Rate Limit

La concurrencia cancela automáticamente ejecuciones anteriores, reduciendo la carga.

---

## Siguiente Paso

:point_right: [Ejemplos de GitLab →](gitlab-minimal.md)
