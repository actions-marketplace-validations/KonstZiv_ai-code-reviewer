# GitLab

Guía detallada para integración con GitLab CI.

---

## Tokens {#tokens}

### CI_JOB_TOKEN (automático)

En GitLab CI, `CI_JOB_TOKEN` está disponible automáticamente:

```yaml
variables:
  AI_REVIEWER_GITLAB_TOKEN: $CI_JOB_TOKEN
```

**Limitaciones de `CI_JOB_TOKEN`:**

| Funcionalidad | Estado |
|---------|--------|
| Leer MR | :white_check_mark: |
| Leer diff | :white_check_mark: |
| Publicar notas | :white_check_mark: |
| Crear discusiones | :x: |

!!! warning "Permisos limitados"
    `CI_JOB_TOKEN` no puede crear discusiones en línea.

    Para funcionalidad completa, usa un Personal Access Token.

### Personal Access Token (PAT) {#get-token}

Para **todos los planes de GitLab** (incluido Free). Recomendado para ejecuciones locales o funcionalidad completa en CI.

**Cómo crear:**

1. Ve a **User Settings → Access Tokens → Add new token**
    - URL: `https://gitlab.com/-/user_settings/personal_access_tokens`
2. Completa los campos:
    - **Token name:** `ai-code-reviewer`
    - **Expiration date:** configura según necesidad (ej. 1 año)
    - **Scopes:** marca **`api`**
3. Haz clic en **Create personal access token**
4. **Copia el token inmediatamente** — GitLab lo muestra solo una vez!

**Cómo usar en CI:**

1. Ve a **Settings → CI/CD → Variables → Add variable**
2. Añade la variable:
    - **Key:** `AI_REVIEWER_GITLAB_TOKEN` (o `GITLAB_TOKEN`)
    - **Value:** pega tu token
    - **Flags:** marca **Masked** y **Protected**
3. Usa en `.gitlab-ci.yml`:

```yaml
variables:
  AI_REVIEWER_GITLAB_TOKEN: $GITLAB_TOKEN  # Personal Access Token desde CI/CD Variables
```

!!! warning "Guarda el token"
    GitLab muestra el token **solo una vez**. Guárdalo en un lugar seguro inmediatamente.

### Project Access Token (:material-crown: Premium/Ultimate) {#project-token}

Disponible solo en planes **GitLab Premium** y **Ultimate**. Una buena opción si prefieres un token con alcance de proyecto en lugar de uno personal.

**Ventajas sobre PAT:**

- Limitado a un solo proyecto (sin acceso a otros proyectos)
- Puede ser revocado por los maintainers del proyecto (sin dependencia de un usuario específico)
- Mejor para equipos — no está vinculado a una cuenta personal

**Cómo crear:**

1. Ve a **Project → Settings → Access Tokens**
    - URL: `https://gitlab.com/<owner>/<repo>/-/settings/access_tokens`
2. Completa los campos:
    - **Token name:** `ai-code-reviewer`
    - **Role:** `Developer` (mínimo requerido)
    - **Scopes:** marca **`api`**
3. Haz clic en **Create project access token**
4. **Copia el token inmediatamente**

**Cómo usar en CI:**

Igual que PAT — añade como `AI_REVIEWER_GITLAB_TOKEN` en CI/CD Variables:

```yaml
variables:
  AI_REVIEWER_GITLAB_TOKEN: $GITLAB_PROJECT_TOKEN  # Project Access Token desde CI/CD Variables
```

!!! info "¿Qué token elegir?"
    | | CI_JOB_TOKEN | Personal Access Token | Project Access Token |
    |---|---|---|---|
    | **Plan** | Todos | Todos (incluido Free) | Solo Premium/Ultimate |
    | **Configuración** | Automática | Manual | Manual |
    | **Alcance** | Solo el job actual | Todos los proyectos del usuario | Un solo proyecto |
    | **Comentarios inline** | :x: | :white_check_mark: | :white_check_mark: |
    | **Mejor para** | Inicio rápido | Plan Free + funciones completas | Equipos en Premium/Ultimate |

---

## Variables CI/CD

### Añadir Variables

`Settings → CI/CD → Variables → Add variable`

| Variable | Valor | Opciones |
|----------|-------|---------|
| `AI_REVIEWER_GOOGLE_API_KEY` | Clave API de Gemini | Masked |
| `AI_REVIEWER_GITLAB_TOKEN` | PAT (si es necesario) | Masked |

!!! tip "Masked"
    Siempre activa **Masked** para secretos — no se mostrarán en los logs.

---

## Triggers

### Trigger Recomendado

```yaml
rules:
  - if: $CI_PIPELINE_SOURCE == "merge_request_event"
```

Esto ejecuta el job solo para pipelines de Merge Request.

### Trigger Alternativo (only/except)

```yaml
only:
  - merge_requests
```

!!! note "rules vs only"
    `rules` — sintaxis más nueva, recomendada por GitLab.

---

## Ejemplos de Jobs

### Mínimo

```yaml
ai-review:
  image: ghcr.io/konstziv/ai-code-reviewer:1
  script:
    - ai-review
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
  variables:
    AI_REVIEWER_GOOGLE_API_KEY: $GOOGLE_API_KEY
    AI_REVIEWER_GITLAB_TOKEN: $CI_JOB_TOKEN  # Automático, no requiere configuración
```

### Completo (recomendado)

```yaml
ai-review:
  image: ghcr.io/konstziv/ai-code-reviewer:1
  stage: test
  script:
    - ai-review
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
  allow_failure: true
  timeout: 10m
  variables:
    AI_REVIEWER_GOOGLE_API_KEY: $GOOGLE_API_KEY
    # CI_JOB_TOKEN (automático) o Personal Access Token para permisos completos:
    AI_REVIEWER_GITLAB_TOKEN: $CI_JOB_TOKEN    # o: $GITLAB_PAT (ver "Obtener token")
    AI_REVIEWER_LANGUAGE: uk
    AI_REVIEWER_LANGUAGE_MODE: adaptive
  interruptible: true
```

**Qué hace:**

- `allow_failure: true` — el MR no se bloquea si la revisión falla
- `timeout: 10m` — máximo 10 minutos
- `interruptible: true` — puede cancelarse con nuevo commit

### Con Stage Personalizado

```yaml
stages:
  - test
  - review
  - deploy

ai-review:
  stage: review
  image: ghcr.io/konstziv/ai-code-reviewer:1
  script:
    - ai-review
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
  needs: []  # No esperar por stages anteriores
```

---

## GitLab Self-hosted

### Configuración

```yaml
variables:
  AI_REVIEWER_GITLAB_URL: https://gitlab.mycompany.com
  AI_REVIEWER_GOOGLE_API_KEY: $GOOGLE_API_KEY
  AI_REVIEWER_GITLAB_TOKEN: $GITLAB_TOKEN
```

### Docker Registry

Si tu GitLab no tiene acceso a `ghcr.io`, crea un mirror:

```bash
# En una máquina con acceso
docker pull ghcr.io/konstziv/ai-code-reviewer:1
docker tag ghcr.io/konstziv/ai-code-reviewer:1 \
    gitlab.mycompany.com:5050/devops/ai-code-reviewer:latest
docker push gitlab.mycompany.com:5050/devops/ai-code-reviewer:latest
```

```yaml
ai-review:
  image: gitlab.mycompany.com:5050/devops/ai-code-reviewer:latest
```

---

## Variables de GitLab CI

AI Code Reviewer usa automáticamente:

| Variable | Descripción |
|----------|-------------|
| `CI_PROJECT_PATH` | `owner/repo` |
| `CI_MERGE_REQUEST_IID` | Número del MR |
| `CI_SERVER_URL` | URL de GitLab |
| `CI_JOB_TOKEN` | Token automático |

No necesitas pasar `--repo` y `--pr` — se toman del CI automáticamente.

---

## Resultado de la Revisión

### Notas (comentarios)

AI Review publica comentarios en el MR como notas.

### Discusiones (en línea)

Para comentarios en línea, necesitas un token PAT completo (no `CI_JOB_TOKEN`).

Los comentarios en línea aparecen directamente junto a las líneas de código en la vista de diff.

### Resumen

Al final de la revisión, se publica una nota de Resumen con:

- Estadísticas generales
- Métricas
- Buenas prácticas

---

## Solución de Problemas

### La Revisión No Publica Comentarios

**Verifica:**

1. La variable `AI_REVIEWER_GOOGLE_API_KEY` (o `GOOGLE_API_KEY`) está configurada
2. `AI_REVIEWER_GITLAB_TOKEN` (o `GITLAB_TOKEN`) tiene permisos suficientes (scope: `api`)
3. El pipeline está ejecutándose para un MR (no para una rama)

### "401 Unauthorized"

**Causa:** Token inválido.

**Solución:**

- Verifica que el token no haya expirado
- Verifica el scope (necesita `api`)

### "403 Forbidden"

**Causa:** Permisos insuficientes.

**Solución:**

- Usa PAT en lugar de `CI_JOB_TOKEN`
- Verifica que el token tenga acceso al proyecto

### "404 Not Found"

**Causa:** MR no encontrado.

**Solución:**

- Verifica que el pipeline esté ejecutándose para un MR
- Verifica `CI_MERGE_REQUEST_IID`

### Rate Limit (429)

**Causa:** Límite de API excedido.

**Solución:**

- AI Code Reviewer reintenta automáticamente con backoff
- Si persiste — espera o aumenta los límites

---

## Mejores Prácticas

### 1. Usa PAT para funcionalidad completa

```yaml
variables:
  AI_REVIEWER_GITLAB_TOKEN: $GITLAB_TOKEN  # PAT, no CI_JOB_TOKEN
```

### 2. Añade allow_failure

```yaml
allow_failure: true
```

El MR no se bloqueará si la revisión falla.

### 3. Establece timeout

```yaml
timeout: 10m
```

### 4. Haz el job interruptible

```yaml
interruptible: true
```

La revisión anterior se cancelará con un nuevo commit.

### 5. No esperes por otros stages

```yaml
needs: []
```

La revisión comenzará inmediatamente, sin esperar por build/test.

---

## Siguiente Paso

- [Integración con GitHub →](github.md)
- [Referencia CLI →](api.md)
