# Instalación

La opción de instalación depende de tu caso de uso y objetivos.

---

## 1. CI/CD — Revisión Automatizada {#ci-cd}

El escenario más común: AI Code Reviewer se ejecuta automáticamente cuando se crea o actualiza un PR/MR.

### GitHub Actions

La forma más sencilla para GitHub — usa la GitHub Action lista para usar:

```yaml
# .github/workflows/ai-review.yml
name: AI Code Review

on:
  pull_request:
    types: [opened, synchronize, reopened]

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

**Configuración requerida:**

| Qué se necesita | Dónde configurar |
|---------------|-------------------|
| `GOOGLE_API_KEY` | Repository → Settings → Secrets → Actions |

:point_right: [Ejemplo completo con concurrencia y filtrado →](quick-start.md#github-actions)

:point_right: [Guía detallada de GitHub →](github.md)

---

### GitLab CI

Para GitLab, usa la imagen Docker en `.gitlab-ci.yml`:

```yaml
# .gitlab-ci.yml
ai-review:
  image: ghcr.io/konstziv/ai-code-reviewer:1
  stage: test
  script:
    - ai-review
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
  allow_failure: true
  variables:
    GOOGLE_API_KEY: $GOOGLE_API_KEY
```

**Configuración requerida:**

| Qué se necesita | Dónde configurar |
|---------------|-------------------|
| `GOOGLE_API_KEY` | Project → Settings → CI/CD → Variables (Masked) |
| `GITLAB_TOKEN` | Opcional, para comentarios en línea ([detalles](gitlab.md#tokens)) |

:point_right: [Ejemplo completo →](quick-start.md#gitlab-ci)

:point_right: [Guía detallada de GitLab →](gitlab.md)

---

## 2. Pruebas Locales / Evaluación {#local}

### ¿Por qué es necesario?

1. **Evaluación antes del despliegue** — pruébalo en un PR real antes de añadirlo al CI
2. **Depuración** — si algo no funciona en CI, ejecuta localmente con `--log-level DEBUG`
3. **Revisión retrospectiva** — analiza un PR/MR antiguo
4. **Demo** — muestra al equipo/gerencia cómo funciona

### Cómo funciona

```
Terminal local
       │
       ▼
   ai-review CLI
       │
       ├──► API de GitHub/GitLab (lee PR/MR, diff, issues vinculados)
       │
       ├──► API de Gemini (obtiene la revisión)
       │
       └──► API de GitHub/GitLab (publica comentarios)
```

### Variables de Entorno Requeridas

| Variable | Descripción | Cuándo se necesita | Cómo obtener |
|----------|-------------|-------------|------------|
| `GOOGLE_API_KEY` | Clave API de Gemini | **Siempre** | [Google AI Studio](https://aistudio.google.com/) |
| `GITHUB_TOKEN` | Personal Access Token de GitHub | Para GitHub | [Instrucciones](github.md#get-token) |
| `GITLAB_TOKEN` | Personal Access Token de GitLab | Para GitLab | [Instrucciones](gitlab.md#get-token) |

---

### Opción A: Docker (recomendado)

No se requiere instalación de Python — todo está en el contenedor.

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

---

### Opción B: pip / uv

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
|----------|---------|--------|
| `LANGUAGE` | `en` | Idioma de respuesta (ISO 639) |
| `LANGUAGE_MODE` | `adaptive` | Modo de detección de idioma |
| `GEMINI_MODEL` | `gemini-2.5-flash` | Modelo Gemini |
| `LOG_LEVEL` | `INFO` | Nivel de logging |

:point_right: [Lista completa de variables →](configuration.md#optional)

---

## 3. Entorno Corporativo (air-gapped) {#airgapped}

Para entornos con acceso limitado a internet.

### Limitaciones

!!! warning "Se requiere acceso a la API de Gemini"
    AI Code Reviewer usa la API de Google Gemini para análisis de código.

    **Acceso requerido a:** `generativelanguage.googleapis.com`

    El soporte para modelos LLM desplegados localmente **aún no está implementado**.

### Despliegue de Imagen Docker

**Paso 1: En una máquina con acceso a internet**

```bash
# Descargar la imagen
docker pull ghcr.io/konstziv/ai-code-reviewer:1

# Guardar en archivo
docker save ghcr.io/konstziv/ai-code-reviewer:1 > ai-code-reviewer.tar
```

**Paso 2: Transferir el archivo al entorno cerrado**

**Paso 3: Cargar en el registro interno**

```bash
# Cargar desde archivo
docker load < ai-code-reviewer.tar

# Re-etiquetar para el registro interno
docker tag ghcr.io/konstziv/ai-code-reviewer:1 \
    registry.internal.company.com/devops/ai-code-reviewer:1

# Subir
docker push registry.internal.company.com/devops/ai-code-reviewer:1
```

**Paso 4: Usar en GitLab CI**

```yaml
ai-review:
  image: registry.internal.company.com/devops/ai-code-reviewer:1
  script:
    - ai-review
  variables:
    GITLAB_URL: https://gitlab.internal.company.com
    GOOGLE_API_KEY: $GOOGLE_API_KEY
```

---

## 4. Contribuidores / Desarrollo {#development}

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
