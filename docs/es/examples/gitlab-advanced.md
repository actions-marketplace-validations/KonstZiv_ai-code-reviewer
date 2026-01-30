# GitLab: Ejemplo Avanzado

Configuración lista para producción con todas las mejores prácticas.

---

## Paso 1: Crear un PAT

`User Settings → Access Tokens → Add new token`

| Campo | Valor |
|-------|-------|
| Name | `ai-code-reviewer` |
| Scopes | `api` |
| Expiration | Según necesidad |

---

## Paso 2: Añadir Variables

`Settings → CI/CD → Variables`

| Nombre | Valor | Opciones |
|--------|-------|----------|
| `GOOGLE_API_KEY` | Clave API de Gemini | Masked |
| `GITLAB_TOKEN` | PAT del Paso 1 | Masked |

---

## Paso 3: Añadir un Job

`.gitlab-ci.yml`:

```yaml
stages:
  - test
  - review

# ... otros jobs ...

ai-review:
  stage: review
  image: ghcr.io/konstziv/ai-code-reviewer:1

  script:
    - ai-review

  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"

  # No bloquear MR si la revisión falla
  allow_failure: true

  # Protección de timeout
  timeout: 10m

  # Puede cancelarse con nuevo commit
  interruptible: true

  # No esperar por otros stages
  needs: []

  variables:
    GOOGLE_API_KEY: $GOOGLE_API_KEY
    GITLAB_TOKEN: $GITLAB_TOKEN
    LANGUAGE: uk
    LANGUAGE_MODE: adaptive
```

---

## Qué Incluye

| Funcionalidad | Estado | Descripción |
|---------------|--------|-------------|
| Discusiones en línea | :white_check_mark: | Con token PAT |
| No bloqueante | :white_check_mark: | `allow_failure: true` |
| Timeout | :white_check_mark: | 10 minutos |
| Interruptible | :white_check_mark: | Se cancela con nuevo commit |
| Ejecución paralela | :white_check_mark: | `needs: []` |
| Idioma personalizado | :white_check_mark: | `LANGUAGE: uk` |

---

## Variaciones

### GitLab Self-hosted

```yaml
ai-review:
  # ...
  variables:
    GOOGLE_API_KEY: $GOOGLE_API_KEY
    GITLAB_TOKEN: $GITLAB_TOKEN
    GITLAB_URL: https://gitlab.mycompany.com
```

### Con Docker Registry Personalizado

```yaml
ai-review:
  # Si ghcr.io no es accesible
  image: registry.mycompany.com/devops/ai-code-reviewer:latest
```

### Con Logs DEBUG

```yaml
ai-review:
  # ...
  variables:
    GOOGLE_API_KEY: $GOOGLE_API_KEY
    GITLAB_TOKEN: $GITLAB_TOKEN
    LOG_LEVEL: DEBUG
```

### Solo para Ramas Específicas

```yaml
ai-review:
  # ...
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
      when: always
    - if: $CI_MERGE_REQUEST_TARGET_BRANCH_NAME == "main"
      when: always
```

---

## Solución de Problemas

### La Revisión No Publica Comentarios

1. Revisa los logs del job
2. Verifica que `GITLAB_TOKEN` tenga scope `api`
3. Verifica que el pipeline esté ejecutándose para un MR

### "401 Unauthorized"

El token es inválido o ha expirado. Crea un nuevo PAT.

### "403 Forbidden"

El token no tiene acceso al proyecto. Verifica los permisos.

---

## Ejemplo Completo de .gitlab-ci.yml

```yaml
stages:
  - lint
  - test
  - review
  - deploy

lint:
  stage: lint
  image: python:3.13
  script:
    - pip install ruff
    - ruff check .

test:
  stage: test
  image: python:3.13
  script:
    - pip install pytest
    - pytest

ai-review:
  stage: review
  image: ghcr.io/konstziv/ai-code-reviewer:1
  script:
    - ai-review
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
  allow_failure: true
  timeout: 10m
  interruptible: true
  needs: []
  variables:
    GOOGLE_API_KEY: $GOOGLE_API_KEY
    GITLAB_TOKEN: $GITLAB_TOKEN
    LANGUAGE: uk

deploy:
  stage: deploy
  script:
    - echo "Deploying..."
  rules:
    - if: $CI_COMMIT_BRANCH == "main"
```

---

## Siguiente Paso

:point_right: [Configuración →](../configuration.md)
