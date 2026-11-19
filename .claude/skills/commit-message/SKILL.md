---
name: commit-message
description: >-
  Use when writing or proposing any Git commit message, to follow Drubico's
  Spanish gitmoji template. Do not use for staging, secrets, or versioning.
metadata:
  author: Drubico
  tags:
    - git
    - commit
    - gitmoji
    - spanish
---

# Mensajes de Commit (español + gitmoji)

## Purpose

Objetivo: redactar cada mensaje de commit con el mismo formato técnico en español, con tipo gitmoji, título imperativo y cuerpo Motivo / Cambios clave / Beneficio, deducido solo del diff y sin relleno.

## When To Use

- Siempre que un agente (Claude, Antigravity/Gemini, Copilot) vaya a crear, corregir (`--amend`) o proponer un commit.
- Cuando el usuario pida "dame el mensaje de commit" o revisar uno existente.
- No decide qué archivos entran ni la versión: eso es de `repo-commit-version`, que llama a esta skill para el mensaje.

## Prerequisites

- Git instalado y cambios en staged (`git diff --cached` no vacío).
- Si el diff es enorme, leer primero `git diff --cached --stat` y después por bloques.

## Usage

1. Run `git diff --cached --stat` y `git diff --cached` para leer el diff real. Nunca redactes de memoria.
2. Si el diff mezcla objetivos sin relación, propón separarlo en varios commits antes de escribir.
3. Sigue el PROCESO de abajo para elegir tipo y variante.
4. Redacta con la plantilla exacta y comprueba los límites de longitud.
5. Run `scripts/validate_commit_msg.py -` con el mensaje por stdin; si falla, corrige lo que indique antes de seguir.
6. Use `git commit -F -` para crear el commit pasando el mensaje por stdin, que conserva la sangría.
7. Si el agente o el repositorio exige un trailer (por ejemplo `Co-Authored-By:`), añádelo al final, tras 1 línea en blanco.
8. Verifica con `git log -1 --format=%B` que el formato quedó intacto.

## Available Scripts

En agentes compatibles invoca `run_script`; en terminal ejecútalos directamente.

| Script | Purpose | Arguments |
|:---|:---|:---|
| `scripts/validate_commit_msg.py` | Valida un mensaje contra estas reglas (exit 0 cumple, 1 no cumple) | `<archivo>`, `-` (stdin) o `--rev <commit>` |
| `scripts/install_hooks.sh` | Activa el hook global y lista repos con hooksPath propio | Ninguno |
| `hooks/commit-msg` | Hook que llama al validador y luego al `commit-msg` local del repo | Lo invoca git |

## Garantía: hook global

- `hooks/commit-msg` rechaza todo commit que no cumpla las reglas, venga de un agente, de la terminal o de un editor que use git.
- Se activa una vez con `scripts/install_hooks.sh`, que fija `git config --global core.hooksPath` a la carpeta `hooks/` de esta skill.
- Aplica en repos con `origin` bajo Drubico o sin `origin`; en repos de terceros no valida. Forzar por repo: `git config commitstandard.enforce true|false`.
- Exentos: mensajes `Merge …`, `Revert "…"`, `fixup!`, `squash!` y `amend!`.
- Como git deja de mirar la carpeta de hooks del repo al usar un hooksPath global, `hooks/_dispatch` vuelve a ejecutar los hooks locales de cada repo (pre-commit, pre-push, LFS, etc.).
- Repos con hooksPath propio (husky, .githooks) no pasan por el hook global: añade allí un `commit-msg` que llame a `scripts/validate_commit_msg.py`.

## Reglas

SALIDA: cuando solo se pide el mensaje, devuelve SOLO el texto del commit, sin saludos, explicaciones, comillas, backticks ni bloques de código.

PROCESO (en orden):
1. Si el diff cambia la versión del proyecto en un manifiesto (package.json, pom.xml, build.gradle, pyproject.toml, etc.) → 🔖 RELEASE. Anula la prioridad de la taxonomía.
2. Si no, elige el tipo del cambio de mayor prioridad presente en el diff.
3. Cuenta las áreas lógicas: 1 área → Variante A. 2 o más áreas, o RELEASE con más cambios → Variante B.
4. Redacta y comprueba los límites antes de responder.

TAXONOMÍA (prioridad en diffs mixtos: T1 > T2 > T3 > T4 > T5 > T6):
- T1: 💥 BREAKING, 🚑️ HOTFIX, 🔒️ SECURITY
- T2: ✨ FEATURE, 💄 UI, ♿️ A11Y, 🔍️ SEO
- T3: 🐛 FIX, ⚡️ PERF, 👽️ API, 🗃️ DB, 🚨 LINT
- T4: ♻️ REFACTOR, 🎨 STYLE, 🚚 MOVE, 🔥 REMOVE, 🏷️ TYPES
- T5: 🔖 RELEASE, 🔧 CONFIG, 📦️ BUILD, 👷 CI, 🧱 INFRA, 🚀 DEPLOY
- T6: 📝 DOCS, ✅ TEST, 🌐 I18N, 🎉 INIT, 🚧 WIP, ⏪️ REVERT, 🔀 MERGE, 🍱 ASSETS, ✏️ TYPO

DESEMPATES:
- 💥 BREAKING: cambia o elimina firmas públicas, endpoints, esquemas o contratos sin compatibilidad.
- 🚑️ HOTFIX: solo si hay evidencia de corrección urgente en producción. Ante la duda, 🐛 FIX.
- ✨ FEATURE añade una capacidad nueva; 🐛 FIX corrige un comportamiento incorrecto existente.
- 💄 UI cambia lo que ve el usuario; 🎨 STYLE solo formatea código sin cambiar lógica.
- ♻️ REFACTOR conserva la conducta externa; si el objetivo es rendimiento, ⚡️ PERF.
- 🔧 CONFIG = archivos de configuración; 📦️ BUILD = dependencias o compilación; 👷 CI = pipelines.
- 👽️ API = adaptación a una API externa; 🗃️ DB = esquema, migraciones o consultas.
- Si el diff es SOLO formato o lockfiles, ese es el cambio: 🎨 STYLE o 📦️ BUILD.

TÍTULO (máx. 72 caracteres contando emoji y espacios, sin punto final):
- Formato: <EMOJI> <TYPE>: <Verbo> <qué cambia y dónde>
- Verbo en 3.ª persona del presente, uno de: Añade, Corrige, Elimina, Refactoriza, Extrae, Reemplaza, Simplifica, Configura, Actualiza, Optimiza, Migra, Mueve, Renombra, Integra, Activa, Valida, Documenta, Revierte.
- PROHIBIDOS títulos genéricos: "Actualiza archivos", "Mejoras varias", "Cambios menores", "Ajustes".
- RELEASE: formato único 🔖 RELEASE: vX.Y.Z (admite sufijos -alpha.N, -beta.N, -rc.N, -dev). Nunca CONFIG ni BUILD para un cambio de versión.
- ⏪️ REVERT: el título incluye el título del commit revertido.

CONTENIDO (rigor técnico, cero alucinaciones):
- Ignora el ruido (lockfiles, imports, formateo) cuando hay cambios lógicos.
- Nombra entidades exactas del diff (componentes, clases, servicios, hooks, métodos, endpoints, tablas). NUNCA rutas ni extensiones de archivo.
- En documentación o configuración sin entidades de código, nombra el documento y su sección (ej. Guía de commits: Taxonomía). NUNCA inventes nombres de clases.
- Motivo: el problema, defecto o carencia del estado ANTERIOR que el diff resuelve. PROHIBIDO empezar con "Se requiere", "Es necesario" o "Para mejorar".
- Beneficio: el efecto técnico concreto DESPUÉS del cambio. PROHIBIDO el relleno sin objeto ("mejora la calidad", "optimiza la claridad", "mayor mantenibilidad").
- No inventes tickets, métricas, usuarios ni contexto de negocio que no aparezca en el diff.
- Motivo y Beneficio no repiten el título ni se repiten entre sí.
- Longitud: Motivo y Beneficio de 1 oración (máx. 120 caracteres cada uno). Cambios clave: máx. 5 viñetas en total, 1 línea cada una (máx. 100 caracteres), con forma Entidad: Verbo + detalle.
- RELEASE sin otros cambios: Variante A con una sola viñeta (Versión: Incrementa de vA a vB.) sin inventar funcionalidades.

FORMATO (respeta exactamente líneas en blanco y sangría):
- Título, 1 línea en blanco, y luego · Motivo:, · Cambios clave: y · Beneficio:, en ese orden.
- Exactamente 1 línea en blanco entre cada bloque (título, encabezados, textos y categorías). Git junta las líneas en blanco dobles, así que no las uses.
- Variante A: viñetas con 2 espacios (  - ).
- Variante B: categorías con 2 espacios (  Categoría:) y viñetas con 4 espacios (    - ), con 1 línea en blanco entre categorías. Solo las categorías que apliquen, en este orden: Nuevas Funcionalidades, Mejoras, Correcciones, Refactorización, Configuración, Documentación, Pruebas.

## Examples

Variante A (un área lógica):

```text
🐛 FIX: Corrige error 500 en login por contraseña vacía

· Motivo:

Las peticiones de autenticación con contraseñas vacías o nulas provocaban una excepción no controlada en el servidor.

· Cambios clave:

  - AuthService: Añade guard clause para rechazar strings nulos o vacíos previo al hashing.
  - LoginController: Mapea el fallo de validación a HTTP 400 Bad Request en lugar de HTTP 500.

· Beneficio:

Previene caídas del servicio de autenticación y entrega respuestas HTTP semánticas a clientes web y móviles.
```

Variante B (varias áreas o release):

```text
🔖 RELEASE: v1.8.6

· Motivo:

Publica la versión estable v1.8.6 con vista de captura liviana, sincronización de permisos y ajustes de seguridad.

· Cambios clave:

  Nuevas Funcionalidades:
    - Módulo B (FS4): Habilita vista liviana con repeticiones anidadas, orden secuencial y soporte HTML.
    - Gestión SGCE: Integra sincronización masiva de asignaciones y permisos para gestores.

  Mejoras:
    - Auth / UX: Añade confirmación de contraseña en restablecimiento y errores detallados del backend.

  Correcciones:
    - Vista Liviana: Valida el XPath de la pregunta antes de abrir el modal de observaciones.

· Beneficio:

Amplía la cobertura en cuestionarios complejos, agiliza la administración SGCE y refuerza la seguridad en autenticación.
```

Crear el commit conservando el formato:

```bash
git diff --cached --stat
python3 scripts/validate_commit_msg.py - <<'EOF'
<mensaje completo según la plantilla>
EOF
git commit -F - <<'EOF'
<mensaje completo según la plantilla>
EOF
git log -1 --format=%B
# Validar un commit ya hecho:
python3 scripts/validate_commit_msg.py --rev HEAD
```

## Limitations

- Solo cubre el texto del mensaje; staging, secretos, versionado y push los cubre `repo-commit-version`.
- Este es el único estándar de commits en los repos propios; reemplaza a Conventional Commits y a cualquier regla anterior en AGENTS.md, prompts o scripts.
- En repos de terceros se respeta la convención del proyecto (el hook no valida ahí).
- Nunca saltes el hook (por ejemplo con `COMMIT_STANDARD_SKIP=1`) sin permiso explícito del usuario.
- Cada repo propio lleva una copia (SKILL.md y el validador) en .claude/skills/commit-message y una sección Commits en AGENTS.md; la fuente es shared-skills y se reparte con tools/sync_commit_standard.py (lista en tools/commit-standard-repos.txt). No edites las copias: cambia la skill y vuelve a sincronizar.
- El hook y su instalador solo viven en shared-skills; las copias en repos no los incluyen.
- Las mismas reglas viven en el repo Drubico/PromptEngineering (archivo gitkraken/gitkraken.instructions.md) para la IA de GitKraken; si cambian aquí, actualiza también esa copia.

## Troubleshooting

| Síntoma / Error | Causa | Solución |
|:---|:---|:---|
| El cuerpo pierde líneas en blanco o sangría | Se usó `git commit -m` varias veces o un editor que recorta | Usar `git commit -F - <<'EOF'` y verificar con `git log -1 --format=%B` |
| El título supera 72 caracteres | Impacto demasiado detallado | Mover el detalle a Cambios clave y dejar solo qué y dónde |
| `✖ El mensaje de commit no cumple el estándar` | El hook encontró errores | Corregir cada punto listado y repetir el commit; el texto queda en .git/COMMIT_EDITMSG |
| El hook no corre en un repo | El repo tiene hooksPath local o `origin` de terceros | Añadir un `commit-msg` local que llame al validador o usar `git config commitstandard.enforce true` |
| Un hook local del repo dejó de ejecutarse | hooksPath global sin despachador para ese nombre | Crear el enlace `hooks/<nombre> -> _dispatch` en esta skill |
| No hay entidades de código que nombrar | Cambio solo de docs o config | Nombrar documento y sección en lugar de inventar clases |
| `git diff --cached` vacío | Nada en staged | Preparar los archivos con `repo-commit-version` antes de redactar |
