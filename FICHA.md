# Ficha — vega-for-agents

> Ficha NORTE de esta herramienta. La lee su experto (`.claude/agents/experto.md`) en cada PR.
> Se mantiene con las reglas internas del mantenedor: su norte es `FICHA.md` y el agente `experto`
> fusiona contra ella.
> Cambiarla exige una nueva aprobación de Cristóbal.

## Qué es

- **Qué construye y para quién:** la referencia de Vega y Vega-Lite para agentes de IA. Dos
  catálogos en un repo (Vega-Lite v5 y Vega v5), con cada nombre válido —mark, canal de encoding,
  transform, tipo de escala y propiedad— **extraído de los JSON Schemas oficiales**, no de la
  memoria del modelo. Cada nombre lleva las trampas que no cuenta la documentación y un ejemplo
  validado contra el schema. Es para quien escribe specs de Vega/Vega-Lite con un agente.
- **Papel** (`repo-roles`): tool (plugin de skills)
- **Gemelo público/privado:** la capa de autoría y *craft* de Deneb para Power BI (`pbiFormat`,
  plantillas, cross-filter) vive aparte, en una capa privada. Hermanos de familia públicos:
  `spark-for-agents`, `dax-for-agents`, `powerquery-m-for-agents`.

## Norte

- **Plan vigente:** [épica v0.1 — catálogos desde los JSON Schemas](https://github.com/CSalcedoDataBI/vega-for-agents/issues/2)
- **Lo que esta herramienta NO es:**
  - No es la capa de autoría de Deneb/Power BI: eso vive en una capa privada aparte.
  - No es un tutorial de Vega/Vega-Lite: es una referencia que un agente consulta.
  - No ejecuta ni renderiza specs: eso es el motor de Vega y, en Power BI, Vega Studio.

## Zonas protegidas

Lo que no se toca sin un paso del plan que lo nombre:

- `exports/*.catalog.json`: solo los escribe `scripts/extract_catalog.py`. Un catálogo a mano rompe
  la promesa de «ningún nombre inventado».
- `exports/*.schema.json`: los schemas oficiales son la fuente de verdad. Cambiar uno es fijar una
  versión nueva (con su SHA-256 en el `meta` del catálogo), no una edición a mano.
- `LICENSE` (MIT) y la visibilidad pública del repo.

## Capa y feedback

- **Capa de nodo** (ADR 0023): `visual`
- **Skill de feedback:** `vega-feedback` (planeada en la v0.1)

## Check y experto

- **Check de CI requerido:** `Validate` (ruleset `main protegida` de `main`)
- **Suite de pruebas:** `python scripts/check_repo.py` y `python -m unittest discover -s tests`
- **Runner:** GitHub (repo público)
- **Formato de tag:** `vX.Y.Z`, con release-please (`release-please-config.json`).
- **Experto:** `.claude/agents/experto.md`
- **¿Plugin del directorio?:** todavía no. Se envía cuando salga de pre-release; desde entonces,
  `stable` no se toca y publicar sigue R5.
- **Partes visibles que aprueba Cristóbal:** el README de cara al público, la salida de
  pre-release, y las cards/plugin cuando se promuevan.

## Aprobación

Aprobada:
