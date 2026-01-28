# GitHub: Ejemplo Mínimo

La configuración más sencilla para GitHub Actions.

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
    types: [opened, synchronize]

jobs:
  review:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      pull-requests: write

    steps:
      - uses: KonstZiv/ai-code-reviewer@v1
        with:
          google_api_key: ${{ secrets.GOOGLE_API_KEY }}
```

---

## Paso 3: Crear un PR

¡Listo! La revisión de IA aparecerá automáticamente.

---

## Qué Incluye

| Funcionalidad | Estado |
|---------|--------|
| Comentarios en línea | :white_check_mark: |
| Botón Apply Suggestion | :white_check_mark: |
| Adaptabilidad de idioma | :white_check_mark: (adaptive) |
| Métricas | :white_check_mark: |

---

## Limitaciones

| Limitación | Solución |
|------------|----------|
| Los PRs de forks no funcionan | Comportamiento esperado |
| Sin concurrencia | Ver [ejemplo avanzado](github-advanced.md) |
| Inglés por defecto | Añadir `language: uk` |

---

## Siguiente Paso

:point_right: [Ejemplo avanzado →](github-advanced.md)
