# Referencia CLI

Referencia de comandos de AI Code Reviewer.

---

## Comando Principal

```bash
ai-review [OPTIONS]
```

**Comportamiento:**

- En CI (GitHub Actions / GitLab CI) — detecta automáticamente el contexto
- Manualmente — necesitas especificar `--provider`, `--repo`, `--pr`

---

## Opciones

| Opción | Corto | Descripción | Por defecto |
|--------|-------|-------------|---------|
| `--provider` | `-p` | Proveedor CI | Auto-detectar |
| `--repo` | `-r` | Repositorio (owner/repo) | Auto-detectar |
| `--pr` | | Número de PR/MR | Auto-detectar |
| `--help` | | Mostrar ayuda | |
| `--version` | | Mostrar versión | |

---

## Proveedores

| Valor | Descripción |
|-------|-------------|
| `github` | GitHub (GitHub Actions) |
| `gitlab` | GitLab (GitLab CI) |

---

## Ejemplos de Uso

### En CI (automático)

```bash
# GitHub Actions — todo automático
ai-review

# GitLab CI — todo automático
ai-review
```

### Manual para GitHub

```bash
export GOOGLE_API_KEY=your_key
export GITHUB_TOKEN=your_token

ai-review --provider github --repo owner/repo --pr 123
```

<small>
**Dónde obtener los valores:**

- `--repo` — de la URL del repositorio: `github.com/owner/repo` → `owner/repo`
- `--pr` — número de la URL: `github.com/owner/repo/pull/123` → `123`
</small>

### Manual para GitLab

```bash
export GOOGLE_API_KEY=your_key
export GITLAB_TOKEN=your_token

ai-review --provider gitlab --repo owner/repo --pr 456
```

<small>
**Dónde obtener los valores:**

- `--repo` — ruta del proyecto de la URL: `gitlab.com/group/project` → `group/project`
- `--pr` — número del MR de la URL: `gitlab.com/group/project/-/merge_requests/456` → `456`
</small>

### Sintaxis Corta

```bash
ai-review -p github -r owner/repo --pr 123
```

---

## Variables de Entorno

CLI lee la configuración de las variables de entorno:

### Requeridas

| Variable | Descripción |
|----------|-------------|
| `GOOGLE_API_KEY` | Clave API de Gemini |
| `GITHUB_TOKEN` | Token de GitHub (para GitHub) |
| `GITLAB_TOKEN` | Token de GitLab (para GitLab) |

### Opcionales

| Variable | Descripción | Por defecto |
|----------|-------------|---------|
| `LANGUAGE` | Idioma de respuesta | `en` |
| `LANGUAGE_MODE` | Modo de idioma | `adaptive` |
| `GEMINI_MODEL` | Modelo Gemini | `gemini-2.5-flash` |
| `LOG_LEVEL` | Nivel de log | `INFO` |
| `GITLAB_URL` | URL de GitLab | `https://gitlab.com` |

:point_right: [Lista completa →](configuration.md)

---

## Auto-detección

### GitHub Actions

CLI usa automáticamente:

| Variable | Descripción |
|----------|-------------|
| `GITHUB_ACTIONS` | Detección de entorno |
| `GITHUB_REPOSITORY` | owner/repo |
| `GITHUB_EVENT_PATH` | JSON con detalles del PR |
| `GITHUB_REF` | Fallback para número de PR |

### GitLab CI

CLI usa automáticamente:

| Variable | Descripción |
|----------|-------------|
| `GITLAB_CI` | Detección de entorno |
| `CI_PROJECT_PATH` | owner/repo |
| `CI_MERGE_REQUEST_IID` | Número del MR |
| `CI_SERVER_URL` | URL de GitLab |

---

## Códigos de Salida

| Código | Descripción |
|------|-------------|
| `0` | Éxito |
| `1` | Error (configuración, API, etc.) |

---

## Logging

### Niveles

| Nivel | Descripción |
|-------|-------------|
| `DEBUG` | Información detallada para depuración |
| `INFO` | Información general (por defecto) |
| `WARNING` | Advertencias |
| `ERROR` | Errores |
| `CRITICAL` | Errores críticos |

### Configuración

```bash
export LOG_LEVEL=DEBUG
ai-review
```

### Salida

CLI usa [Rich](https://rich.readthedocs.io/) para salida formateada:

```
[12:34:56] INFO     Detected CI Provider: github
[12:34:56] INFO     Context extracted: owner/repo PR #123
[12:34:57] INFO     Fetching PR diff...
[12:34:58] INFO     Analyzing code with Gemini...
[12:35:02] INFO     Review completed successfully
```

---

## Errores

### Error de Configuración

```
Configuration Error: GOOGLE_API_KEY is too short (minimum 10 characters)
```

**Causa:** Configuración inválida.

**Solución:** Verifica las variables de entorno.

### Error de Contexto

```
Context Error: Could not determine PR number from GitHub Actions context.
```

**Causa:** El workflow no se está ejecutando para un PR.

**Solución:** Asegúrate de que el workflow tenga `on: pull_request`.

### Proveedor No Detectado

```
Error: Could not detect CI environment.
Please specify --provider, --repo, and --pr manually.
```

**Causa:** Ejecutando fuera de CI.

**Solución:** Especifica todos los parámetros manualmente.

---

## Docker

Ejecutar via Docker:

```bash
docker run --rm \
  -e GOOGLE_API_KEY=your_key \
  -e GITHUB_TOKEN=your_token \
  ghcr.io/konstziv/ai-code-reviewer:1 \
  --provider github \
  --repo owner/repo \
  --pr 123
```

---

## Versión

```bash
ai-review --version
```

```
AI Code Reviewer 0.1.0
```

---

## Ayuda

```bash
ai-review --help
```

```
Usage: ai-review [OPTIONS]

  Run AI Code Reviewer.

  Automatically detects CI environment and reviews the current Pull Request.
  Can also be run manually by providing arguments.

Options:
  -p, --provider [github|gitlab]  CI provider (auto-detected if not provided)
  -r, --repo TEXT                 Repository name (e.g. owner/repo). Auto-detected in CI.
  --pr INTEGER                    Pull Request number. Auto-detected in CI.
  --help                          Show this message and exit.
```

---

## Siguiente Paso

- [Solución de Problemas →](troubleshooting.md)
- [Ejemplos →](examples/index.md)
