# Instalación

La opción de instalación depende de tu caso de uso y objetivos.

---

## 1. CI/CD — Revisión Automatizada {#ci-cd}

El escenario más común: AI Code Reviewer se ejecuta automáticamente cuando se crea o actualiza un PR/MR.

Configura en 5 minutos:

- :octicons-mark-github-16: **[Configuración de revisión para GitHub →](quick-start.md)**

    :point_right: [Ejemplos de workflows →](examples/github-minimal.md) · [Guía detallada de GitHub →](github.md)

- :simple-gitlab: **[Configuración de revisión para GitLab →](quick-start.md)**

    :point_right: [Ejemplos de workflows →](examples/gitlab-minimal.md) · [Guía detallada de GitLab →](gitlab.md)

Para ajuste fino, consulta [Configuración →](configuration.md)

---

## 2. Despliegue Autónomo: CLI/Docker {#standalone}

CLI y la imagen Docker permiten ejecutar AI Code Reviewer fuera del pipeline CI estándar.

### Escenarios de uso

| Escenario | Cómo implementar |
|-----------|------------------|
| **Ejecución manual** | Terminal local — debugging, demo, evaluación |
| **Scheduled review** | GitLab Scheduled Pipeline / GitHub Actions `schedule` / cron |
| **Batch review** | Script que itera sobre PR/MR abiertos |
| **Servidor propio** | Docker en servidor con acceso a Git API |
| **On-demand review** | Webhook → ejecutar contenedor |

### Variables de Entorno Requeridas

| Variable | Descripción | Cuándo se necesita | Cómo obtener |
|----------|-------------|-------------------|--------------|
| `GOOGLE_API_KEY` | Clave API de Gemini | **Siempre** | [Google AI Studio](https://aistudio.google.com/) |
| `GITHUB_TOKEN` | GitHub Personal Access Token | Para GitHub | [Instrucciones](github.md#get-token) |
| `GITLAB_TOKEN` | GitLab Personal Access Token | Para GitLab | [Instrucciones](gitlab.md#get-token) |

---

### Ejecución Manual

Para debugging, demo, evaluación antes del despliegue, análisis retrospectivo de PR/MR.

#### Docker (recomendado)

No requiere instalación de Python — todo está en el contenedor.

**Paso 1: Descargar la imagen**

```bash
docker pull ghcr.io/konstziv/ai-code-reviewer:1
```

**Paso 2: Ejecutar la revisión**

=== "GitHub PR"

    ```bash
    docker run --rm \
      -e GOOGLE_API_KEY=your_api_key \
      -e GITHUB_TOKEN=your_token \
      ghcr.io/konstziv/ai-code-reviewer:1 \
      --repo owner/repo --pr-number 123
    ```

=== "GitLab MR"

    ```bash
    docker run --rm \
      -e GOOGLE_API_KEY=your_api_key \
      -e GITLAB_TOKEN=your_token \
      ghcr.io/konstziv/ai-code-reviewer:1 \
      --provider gitlab --project owner/repo --mr-iid 123
    ```

!!! tip "Imágenes Docker"
    Disponibles en dos registros:

    - `ghcr.io/konstziv/ai-code-reviewer:1` — GitHub Container Registry
    - `koszivdocker/ai-reviewbot:1` — DockerHub

#### pip / uv

Instalación como paquete Python.

**Paso 1: Instalar**

=== "pip"

    ```bash
    pip install ai-reviewbot
    ```

=== "uv"

    ```bash
    uv tool install ai-code-reviewer
    ```

=== "pipx"

    ```bash
    pipx install ai-code-reviewer
    ```

!!! note "Versión de Python"
    Requiere Python **3.13+**

**Paso 2: Configurar variables**

```bash
export GOOGLE_API_KEY=your_api_key
export GITHUB_TOKEN=your_token  # o GITLAB_TOKEN para GitLab
```

**Paso 3: Ejecutar**

=== "GitHub PR"

    ```bash
    ai-review --repo owner/repo --pr-number 123
    ```

=== "GitLab MR"

    ```bash
    ai-review --provider gitlab --project owner/repo --mr-iid 123
    ```

---

### Variables Opcionales

Variables adicionales disponibles para ajuste fino:

| Variable | Por defecto | Efecto |
|----------|-------------|--------|
| `LANGUAGE` | `en` | Idioma de respuesta (ISO 639) |
| `LANGUAGE_MODE` | `adaptive` | Modo de detección de idioma |
| `GEMINI_MODEL` | `gemini-2.5-flash` | Modelo Gemini |
| `LOG_LEVEL` | `INFO` | Nivel de logging |

:point_right: [Lista completa de variables →](configuration.md#optional)

---

### Scheduled reviews

Ejecución de revisiones programadas — para ahorrar recursos o cuando no se necesita feedback inmediato.

=== "GitLab Scheduled Pipeline"

    ```yaml
    # .gitlab-ci.yml
    ai-review-scheduled:
      image: ghcr.io/konstziv/ai-code-reviewer:1
      script:
        - |
          # Obtener lista de MR abiertos
          MR_LIST=$(curl -s --header "PRIVATE-TOKEN: $GITLAB_TOKEN" \
            "$CI_SERVER_URL/api/v4/projects/$CI_PROJECT_ID/merge_requests?state=opened" \
            | jq -r '.[].iid')

          # Ejecutar revisión para cada MR
          for MR_IID in $MR_LIST; do
            echo "Reviewing MR !$MR_IID"
            ai-review --provider gitlab --project $CI_PROJECT_PATH --pr $MR_IID || true
          done
      rules:
        - if: $CI_PIPELINE_SOURCE == "schedule"
      variables:
        GOOGLE_API_KEY: $GOOGLE_API_KEY
        GITLAB_TOKEN: $GITLAB_TOKEN
    ```

    **Configuración del horario:** Project → Build → Pipeline schedules → New schedule

=== "GitHub Actions Schedule"

    ```yaml
    # .github/workflows/scheduled-review.yml
    name: Scheduled AI Review

    on:
      schedule:
        - cron: '0 9 * * *'  # Diariamente a las 9:00 UTC

    jobs:
      review-open-prs:
        runs-on: ubuntu-latest
        steps:
          - name: Get open PRs and review
            env:
              GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
              GOOGLE_API_KEY: ${{ secrets.GOOGLE_API_KEY }}
            run: |
              # Obtener lista de PR abiertos
              PRS=$(gh pr list --repo ${{ github.repository }} --state open --json number -q '.[].number')

              for PR in $PRS; do
                echo "Reviewing PR #$PR"
                docker run --rm \
                  -e GOOGLE_API_KEY -e GITHUB_TOKEN \
                  ghcr.io/konstziv/ai-code-reviewer:1 \
                  --repo ${{ github.repository }} --pr $PR || true
              done
    ```

---

### Servidor propio / entorno privado

Para despliegue en infraestructura propia con acceso a Git API.

**Opciones:**

- **Docker en servidor** — ejecución mediante cron, systemd timer, o como servicio
- **Kubernetes** — CronJob para scheduled reviews
- **Self-hosted GitLab** — añadir variable `GITLAB_URL` (ver ejemplo abajo)

**Ejemplo de cron job:**

```bash
# /etc/cron.d/ai-review
# Diariamente a las 10:00 ejecutar revisión para todos los MR abiertos
0 10 * * * reviewer /usr/local/bin/review-all-mrs.sh
```

```bash
#!/bin/bash
# /usr/local/bin/review-all-mrs.sh
export GOOGLE_API_KEY="your_key"
export GITLAB_TOKEN="your_token"

MR_LIST=$(curl -s --header "PRIVATE-TOKEN: $GITLAB_TOKEN" \
  "https://gitlab.company.com/api/v4/projects/123/merge_requests?state=opened" \
  | jq -r '.[].iid')

for MR_IID in $MR_LIST; do
  docker run --rm \
    -e GOOGLE_API_KEY -e GITLAB_TOKEN \
    ghcr.io/konstziv/ai-code-reviewer:1 \
    --provider gitlab --project group/repo --pr $MR_IID
done
```

!!! tip "Self-hosted GitLab"
    Para self-hosted GitLab añadir variable `GITLAB_URL`:

    ```bash
    -e GITLAB_URL=https://gitlab.company.com
    ```

---

## 3. Contribuidores / Desarrollo {#development}

Si tienes el tiempo e inspiración para ayudar a desarrollar el paquete, o quieres usarlo como base para tu propio desarrollo — ¡sinceramente damos la bienvenida y alentamos tales acciones!

### Instalación de Desarrollo

```bash
# Clonar el repositorio
git clone https://github.com/KonstZiv/ai-code-reviewer.git
cd ai-code-reviewer

# Instalar dependencias (usamos uv)
uv sync

# Verificar
uv run ai-review --help

# Ejecutar tests
uv run pytest

# Ejecutar verificaciones de calidad
uv run ruff check .
uv run mypy .
```

!!! info "uv"
    Usamos [uv](https://github.com/astral-sh/uv) para gestión de dependencias.

    Instalar: `curl -LsSf https://astral.sh/uv/install.sh | sh`

### Estructura del Proyecto

```
ai-code-reviewer/
├── src/ai_reviewer/      # Código fuente
│   ├── core/             # Modelos, config, formateo
│   ├── integrations/     # GitHub, GitLab, Gemini
│   └── utils/            # Utilidades
├── tests/                # Tests
├── docs/                 # Documentación
└── examples/             # Ejemplos de configuración CI
```

:point_right: [Cómo contribuir →](https://github.com/KonstZiv/ai-code-reviewer/blob/main/CONTRIBUTING.md)

---

## Requisitos {#requirements}

### Requisitos del Sistema

| Componente | Requisito |
|-----------|-------------|
| Python | 3.13+ (para instalación con pip) |
| Docker | 20.10+ (para Docker) |
| SO | Linux, macOS, Windows |
| RAM | 256MB+ |
| Red | Acceso a `generativelanguage.googleapis.com` |

### Claves API

| Clave | Requerida | Cómo obtener |
|-----|----------|------------|
| Google Gemini API | **Sí** | [Google AI Studio](https://aistudio.google.com/) |
| GitHub PAT | Para GitHub | [Instrucciones](github.md#get-token) |
| GitLab PAT | Para GitLab | [Instrucciones](gitlab.md#get-token) |

### Límites de API de Gemini

!!! info "Nivel gratuito"
    Google Gemini tiene un nivel gratuito:

    | Límite | Valor |
    |-------|-------|
    | Solicitudes por minuto | 15 RPM |
    | Tokens por día | 1M |
    | Solicitudes por día | 1500 |

    Esto es suficiente para la mayoría de los proyectos.

---

## Siguiente Paso

:point_right: [Inicio Rápido →](quick-start.md)
