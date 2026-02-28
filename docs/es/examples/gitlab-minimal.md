# GitLab: Ejemplo Mínimo

La configuración más sencilla para GitLab CI.

---

## Paso 1: Añadir una Variable

`Settings → CI/CD → Variables → Add variable`

| Nombre | Valor | Opciones |
|--------|-------|----------|
| `AI_REVIEWER_GOOGLE_API_KEY` | Tu clave API de Gemini | Masked |
| `AI_REVIEWER_GITLAB_TOKEN` | Personal Access Token con scope `api` | Masked |

---

## Paso 2: Añadir un Job

`.gitlab-ci.yml`:

```yaml
ai-review:
  image: ghcr.io/konstziv/ai-code-reviewer:1
  script:
    - ai-review
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
```

---

## Paso 3: Crear un MR

¡Listo! La revisión de IA aparecerá como comentarios en el MR.

---

## Qué Incluye

| Funcionalidad | Estado |
|---------------|--------|
| Notas en MR | :white_check_mark: |
| Adaptabilidad de idioma | :white_check_mark: (adaptive) |
| Métricas | :white_check_mark: |
| Auto-reintento | :white_check_mark: |

---

## Limitaciones

| Limitación | Solución |
|------------|----------|
| MR bloqueado en error | Añadir `allow_failure: true` |

---

## Siguiente Paso

:point_right: [Ejemplo avanzado →](gitlab-advanced.md)
