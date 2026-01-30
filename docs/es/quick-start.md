# Inicio Rápido

Pon en marcha AI Code Reviewer en 5 minutos en GitHub o GitLab.

---

## Paso 1: Obtener clave API

Para que AI Reviewer funcione, necesitas una clave de Google Gemini API.

1. Ve a [Google AI Studio](https://aistudio.google.com/)
2. Inicia sesión con tu cuenta de Google
3. Haz clic en **"Get API key"** → **"Create API key"**
4. Copia la clave (comienza con `AIza...`)

!!! warning "Guarda la clave"
    La clave solo se muestra una vez. Guárdala en un lugar seguro.

!!! tip "Nivel gratuito"
    Gemini API tiene un nivel gratuito: 15 solicitudes por minuto, suficiente para la mayoría de los proyectos.

---

## Paso 2: Añadir clave al entorno del repositorio

La clave debe añadirse como variable secreta en tu repositorio.

=== "GitHub"

    **Ruta:** Repository → `Settings` → `Secrets and variables` → `Actions` → `New repository secret`

    | Campo | Valor |
    |-------|-------|
    | **Name** | `GOOGLE_API_KEY` |
    | **Secret** | Tu clave (`AIza...`) |

    Haz clic en **"Add secret"**.

    ??? info "Instrucciones detalladas con capturas de pantalla"
        1. Abre tu repositorio en GitHub
        2. Haz clic en **Settings** (engranaje en el menú superior)
        3. En el menú izquierdo, busca **Secrets and variables** → **Actions**
        4. Haz clic en el botón verde **New repository secret**
        5. En el campo **Name** ingresa: `GOOGLE_API_KEY`
        6. En el campo **Secret** pega tu clave
        7. Haz clic en **Add secret**

    :material-book-open-variant: [Documentación oficial de GitHub: Encrypted secrets](https://docs.github.com/en/actions/security-for-github-actions/security-guides/using-secrets-in-github-actions)

=== "GitLab"

    Para GitLab necesitas crear un **Project Access Token** y añadir dos variables.

    ### Paso 2a: Crear Project Access Token

    !!! note "Se requieren permisos de Maintainer"
        Para crear un Project Access Token necesitas el rol **Maintainer** u **Owner** en el proyecto.

        :material-book-open-variant: [GitLab Docs: Roles and permissions](https://docs.gitlab.com/ee/user/permissions/)

    **Ruta:** Project → `Settings` → `Access Tokens`

    | Campo | Valor |
    |-------|-------|
    | **Token name** | `ai-reviewer` |
    | **Expiration date** | Elige una fecha (máx. 1 año) |
    | **Role** | `Developer` |
    | **Scopes** | :white_check_mark: `api` |

    Haz clic en **"Create project access token"** → **Copia el token** (¡solo se muestra una vez!)

    :material-book-open-variant: [GitLab Docs: Project access tokens](https://docs.gitlab.com/ee/user/project/settings/project_access_tokens.html)

    ### Paso 2b: Añadir variables en CI/CD

    **Ruta:** Project → `Settings` → `CI/CD` → `Variables`

    Añade **dos** variables:

    | Key | Value | Flags |
    |-----|-------|-------|
    | `GOOGLE_API_KEY` | Tu clave Gemini (`AIza...`) | :white_check_mark: Mask variable |
    | `GITLAB_TOKEN` | Token del paso 2a | :white_check_mark: Mask variable |

    ??? info "Instrucciones detalladas"
        1. Abre tu proyecto en GitLab
        2. Ve a **Settings** → **CI/CD**
        3. Expande la sección **Variables**
        4. Haz clic en **Add variable**
        5. Añade `GOOGLE_API_KEY`:
            - Key: `GOOGLE_API_KEY`
            - Value: tu clave Gemini API
            - Flags: Mask variable ✓
        6. Haz clic en **Add variable**
        7. Repite para `GITLAB_TOKEN`:
            - Key: `GITLAB_TOKEN`
            - Value: token del paso 2a
            - Flags: Mask variable ✓

    :material-book-open-variant: [GitLab Docs: CI/CD variables](https://docs.gitlab.com/ee/ci/variables/)

---

## Paso 3: Añadir AI Review al CI {#ci-setup}

=== "GitHub"

    ### Opción A: Nuevo archivo workflow

    Si aún no usas GitHub Actions, o quieres un archivo separado para AI Review:

    1. Crea la carpeta `.github/workflows/` en la raíz del repositorio (si no existe)
    2. Crea el archivo `ai-review.yml` en esa carpeta
    3. Copia este código:

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

    !!! info "Sobre `GITHUB_TOKEN`"
        `secrets.GITHUB_TOKEN` es un **token automático** que GitHub crea para cada workflow run. **No necesitas** añadirlo manualmente a los secretos — ya está disponible.

        Los permisos del token se definen en la sección `permissions` del archivo workflow.

        :material-book-open-variant: [GitHub Docs: Automatic token authentication](https://docs.github.com/en/actions/security-for-github-actions/security-guides/automatic-token-authentication)

    4. Haz commit y push del archivo

    ### Opción B: Añadir a workflow existente

    Si ya tienes `.github/workflows/` con otros jobs, añade este job a tu archivo existente:

    ```yaml
    # Añade este job a tu archivo workflow existente
    ai-review:
      runs-on: ubuntu-latest
      if: github.event_name == 'pull_request' && github.event.pull_request.head.repo.full_name == github.repository
      permissions:
        contents: read
        pull-requests: write
      steps:
        - uses: KonstZiv/ai-code-reviewer@v1
          with:
            github_token: ${{ secrets.GITHUB_TOKEN }}
            google_api_key: ${{ secrets.GOOGLE_API_KEY }}
    ```

    !!! note "Verifica triggers"
        Asegúrate de que tu workflow tenga `on: pull_request` entre los triggers.

=== "GitLab"

    ### Opción A: Nuevo archivo CI

    Si aún no tienes `.gitlab-ci.yml`:

    1. Crea el archivo `.gitlab-ci.yml` en la raíz del repositorio
    2. Copia este código:

    ```yaml
    stages:
      - review

    ai-review:
      image: ghcr.io/konstziv/ai-code-reviewer:1
      stage: review
      script:
        - ai-review
      rules:
        - if: $CI_PIPELINE_SOURCE == "merge_request_event"
      allow_failure: true
      variables:
        GITLAB_TOKEN: $GITLAB_TOKEN
        GOOGLE_API_KEY: $GOOGLE_API_KEY
    ```

    3. Haz commit y push del archivo

    ### Opción B: Añadir a CI existente

    Si ya tienes `.gitlab-ci.yml`:

    1. Añade `review` a la lista de `stages` (si necesitas un stage separado)
    2. Añade este job:

    ```yaml
    ai-review:
      image: ghcr.io/konstziv/ai-code-reviewer:1
      stage: review  # o test, u otro stage existente
      script:
        - ai-review
      rules:
        - if: $CI_PIPELINE_SOURCE == "merge_request_event"
      allow_failure: true
      variables:
        GITLAB_TOKEN: $GITLAB_TOKEN
        GOOGLE_API_KEY: $GOOGLE_API_KEY
    ```

---

## Paso 4: Verificar resultado

Ahora AI Review se ejecutará automáticamente cuando:

| Plataforma | Evento |
|------------|--------|
| **GitHub** | Crear PR, nuevos commits en PR, reopening PR |
| **GitLab** | Crear MR, nuevos commits en MR |

### Qué verás

Después de que el job de CI termine, en el PR/MR aparecerán:

- **Comentarios inline** — vinculados a líneas de código específicas
- **Botón "Apply suggestion"** — para aplicar correcciones rápidamente (GitHub)
- **Comentario Summary** — resumen general con métricas

Cada comentario contiene:

- :red_circle: / :yellow_circle: / :blue_circle: Badge de severidad
- Descripción del problema
- Sugerencia de corrección
- Sección colapsable "¿Por qué importa esto?"

---

## Solución de Problemas

### ¿No aparece la revisión?

Verifica la lista:

- [ ] ¿`GOOGLE_API_KEY` añadido como secreto?
- [ ] ¿`github_token` pasado explícitamente? (para GitHub)
- [ ] ¿El job de CI terminó exitosamente? (revisa logs)
- [ ] Para GitHub: ¿tiene `permissions: pull-requests: write`?
- [ ] Para PRs de forks: los secretos no están disponibles — comportamiento esperado

### ¿En los logs muestra `--help`?

Esto significa que el CLI no recibió los parámetros necesarios. Verifica:

- Si `github_token` / `GITLAB_TOKEN` se pasó explícitamente
- Si el formato YAML es correcto (¡indentación!)

### ¿Rate limit?

Gemini free tier: 15 solicitudes por minuto. Espera un minuto e intenta de nuevo.

:point_right: [Todos los problemas y soluciones →](troubleshooting.md)

---

## ¿Qué sigue?

| Tarea | Documento |
|-------|-----------|
| Configurar idioma de respuestas | [Configuración](configuration.md) |
| Configuración avanzada de GitHub | [Guía de GitHub](github.md) |
| Configuración avanzada de GitLab | [Guía de GitLab](gitlab.md) |
| Ejemplos de workflows | [Ejemplos](examples/index.md) |
