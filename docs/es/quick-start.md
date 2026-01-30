# Inicio Rápido

Pon en marcha AI Code Reviewer en 1 minuto.

---

## GitHub Actions

### Paso 1: Añadir un secreto

`Settings → Secrets and variables → Actions → New repository secret`

| Nombre | Valor |
|------|-------|
| `GOOGLE_API_KEY` | Tu clave API de Gemini |

:point_right: [Obtén tu clave](https://aistudio.google.com/)

### Paso 2: Crear un workflow

En la raíz de tu proyecto, crea el archivo `.github/workflows/ai-review.yml`

`.github/workflows/ai-review.yml`:

```yaml
name: AI Code Review

on:
  pull_request:
    types: [opened, synchronize, reopened]

concurrency:
  group: ai-review-${{ github.event.pull_request.number }}
  cancel-in-progress: true

jobs:
  review:
    runs-on: ubuntu-latest
    # No ejecutar para PRs de forks (sin acceso a secretos)
    if: github.event.pull_request.head.repo.full_name == github.repository
    permissions:
      contents: read
      pull-requests: write

    steps:
      - uses: KonstZiv/ai-code-reviewer@v1
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          google_api_key: ${{ secrets.GOOGLE_API_KEY }}
```

### Paso 3: Crear un PR

¡Listo! La revisión de IA aparecerá automáticamente.

---

## GitLab CI

### Paso 1: Añadir una variable

`Settings → CI/CD → Variables`

| Nombre | Valor | Opciones |
|------|-------|---------|
| `GOOGLE_API_KEY` | Tu clave API de Gemini | Masked, Protected |

:point_right: [Obtén tu clave](https://aistudio.google.com/)

### Paso 2: Añadir un job

En la raíz de tu proyecto, crea el archivo `.gitlab-ci.yml`

`.gitlab-ci.yml`:

```yaml
ai-review:
  image: ghcr.io/konstziv/ai-code-reviewer:1
  stage: test
  script:
    - ai-review
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
  allow_failure: true
  variables:
    GITLAB_TOKEN: $CI_JOB_TOKEN
    GOOGLE_API_KEY: $GOOGLE_API_KEY
```

!!! note "Para comentarios inline"
    `CI_JOB_TOKEN` tiene limitaciones. Para funcionalidad completa use [Personal Access Token](gitlab.md#personal-access-token).

### Paso 3: Crear un MR

¡Listo! La revisión de IA aparecerá como comentarios en el MR.

---

## Ejecución Local

Para pruebas locales necesitas:

- **GOOGLE_API_KEY** — [obtenerla en Google AI Studio](https://aistudio.google.com/)
- **GITHUB_TOKEN** o **GITLAB_TOKEN** — dependiendo de la plataforma:
    - GitHub: [cómo obtener PAT](github.md#get-token)
    - GitLab: [cómo obtener PAT](gitlab.md#get-token)

=== "GitHub"

    ```bash
    # Instalar
    pip install ai-reviewbot

    # Configurar
    export GOOGLE_API_KEY=your_key
    export GITHUB_TOKEN=your_github_pat

    # Ejecutar para GitHub PR
    ai-review --repo owner/repo --pr-number 123
    ```

=== "GitLab"

    ```bash
    # Instalar
    pip install ai-reviewbot

    # Configurar
    export GOOGLE_API_KEY=your_key
    export GITLAB_TOKEN=your_gitlab_pat

    # Ejecutar para GitLab MR
    ai-review --provider gitlab --project owner/repo --mr-iid 123
    ```

---

## ¿Qué Sigue?

| Tarea | Documento |
|------|----------|
| Configurar idioma | [Configuración](configuration.md) |
| Optimizar para GitHub | [Guía de GitHub](github.md) |
| Optimizar para GitLab | [Guía de GitLab](gitlab.md) |
| Ver ejemplos | [Ejemplos](examples/index.md) |

---

## Resultado de Ejemplo

Después de ejecutar, verás comentarios en línea:

![Ejemplo de AI Review](https://via.placeholder.com/800x400?text=AI+Review+Inline+Comment)

Cada comentario contiene:

- :red_circle: / :yellow_circle: / :blue_circle: Distintivo de severidad
- Descripción del problema
- Botón **"Apply suggestion"**
- Explicación desplegable "¿Por qué importa esto?"

---

## Solución de Problemas

### ¿No aparece la revisión?

1. Revisa los logs del job de CI
2. Verifica que `GOOGLE_API_KEY` sea correcta
3. Para GitHub: verifica `permissions: pull-requests: write`
4. Para PRs de forks: los secretos no están disponibles

### ¿Rate limit?

Nivel gratuito de Gemini: 15 RPM. Espera un minuto.

:point_right: [Todos los problemas →](troubleshooting.md)
