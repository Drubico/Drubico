<!-- commit-standard:start -->
## Commits

Este repo usa el estándar único de commits de Drubico: la skill `commit-message` (`.claude/skills/commit-message/SKILL.md`). Es obligatorio para cualquier agente (Claude, Copilot, Antigravity/Gemini) y para commits manuales; reemplaza a Conventional Commits y a cualquier otra convención.

- Título: `<EMOJI> <TYPE>: <Verbo> <qué cambia y dónde>`, máx. 72 caracteres y sin punto final. Release: `🔖 RELEASE: vX.Y.Z`.
- Cuerpo: `· Motivo:`, `· Cambios clave:` y `· Beneficio:`, en español, con 1 línea en blanco entre bloques.
- Antes de commitear valida el mensaje: `python3 .claude/skills/commit-message/scripts/validate_commit_msg.py -` (mensaje por stdin). Crea el commit con `git commit -F -`.
- Reglas completas, taxonomía y ejemplos: `.claude/skills/commit-message/SKILL.md`.
<!-- commit-standard:end -->
