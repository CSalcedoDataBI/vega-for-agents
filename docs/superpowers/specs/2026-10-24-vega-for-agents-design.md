# vega-for-agents — diseño inicial

*2026-10-24. Estado: borrador para la épica v0.1.*

## 1. Qué problema resuelve

Un agente que escribe specs de Vega o Vega-Lite inventa propiedades, confunde los dos lenguajes
y mezcla nombres que no existen (un mark `bubble`, un canal `radius2` donde no aplica, un transform
`pivot` mal colocado). `dax-for-agents` y `powerquery-m-for-agents` resolvieron lo mismo para DAX y
M: el catálogo sale de la fuente oficial, no de la memoria. Aquí la fuente oficial es el **JSON
Schema publicado** de cada lenguaje.

## 2. Fuente de verdad

| Qué | Cómo se extrae |
|---|---|
| Vega-Lite v5 | `exports/vega-lite-v5.schema.json` (schema oficial, draft-07, 456 definiciones) |
| Vega v5 | `exports/vega-v5.schema.json` (schema oficial, draft-07, 131 definiciones) |

`scripts/extract_catalog.py` lee cada schema y escribe `exports/<lenguaje>.catalog.json` con el
catálogo de nombres válidos: marks, canales de encoding (VL), transforms, tipos de escala y el
conjunto de todas las propiedades. La versión exacta del schema se fija por **SHA-256** en el
`meta` del catálogo; no se vuelve a bajar salvo para fijar una versión nueva.

Nota de provenance honesta: el schema de **Vega** deja `marktype` como `string` libre (no lo
enumera). Los marks primitivos de Vega son el mismo conjunto que el enum `MarkType` de Vega-Lite
(ambos del proyecto oficial Vega), así que el catálogo de Vega toma de ahí su lista de marks y lo
declara en `meta.notes`. Las propiedades y los `type` de transform/escala sí salen enumerados del
schema de Vega.

## 3. Antes de escribir nada (NORTE R2)

### 3.1 Hallazgo (2026-10-24)

Búsquedas en GitHub: `vega-lite claude skill`, `vega agent reference`,
`vega-lite json schema catalog`, `vega-lite mcp`, `vega-lite llm hallucination`,
`vega visualization mcp server`, `vega-lite spec generator agent`, `deneb agent`, con
`--sort=stars`.

| Qué existe | Qué hace | ¿Da un catálogo de nombres extraído del schema? |
|---|---|---|
| `inteligencianegociosmmx/vegaLite_mcp_server` (1★, 2025-10-09) | Servidor MCP que da acceso a documentación, ejemplos y validación de Vega-Lite | No. Sirve docs y valida un spec contra el schema; no publica el **catálogo de nombres válidos** versionado para que un agente lo lea sin invocar nada |
| `OneofGods/vegalite-mcp-troubleshooting` (0★) | Guía de troubleshooting de un server MCP de Vega-Lite | No |
| Resto de resultados | Agentes que generan specs desde la memoria del modelo, o repos sin relación | No. Generar desde memoria es justo el problema |

**Conclusión.** Nadie publica un catálogo de nombres de Vega y Vega-Lite **extraído del JSON
Schema oficial**, versionado y con un check de CI que prohíba cualquier nombre fuera de él. Ese es
el hueco. El `vegaLite_mcp_server` valida specs puntuales; aquí el objetivo es la referencia que un
agente consulta antes de escribir, y la red que atrapa el nombre inventado en lo que el repo
publica.

## 4. Piezas de la v0.1

1. Extractor del catálogo + los dos JSON (`exports/*.catalog.json`), fijando la versión por SHA-256. **(hecho)**
2. Check de CI (`scripts/check_repo.py`) que prohíbe cualquier mark/canal/transform/escala/propiedad
   fuera del schema, en las fichas y en los specs de ejemplo. **(hecho)**
3. Borradores de trampas + ejemplos, drafteados con el motor de Batch y validados nombre a nombre
   contra el schema. **(en curso)**
4. Fichas de referencia promovidas desde los borradores, y skill `vega-reference`.
5. Skill `vega-feedback` (reportar una ficha mala o un nombre que falta como issue público).
6. `.claude-plugin/` (plugin.json + marketplace.json) y `PRIVACY.md`.
7. Nodo de la capa `visual` (ADR 0023): `node.json`.

## 5. Dos lenguajes, dos catálogos

Vega-Lite y Vega son lenguajes distintos. Un nombre válido en uno no lo es automáticamente en el
otro. Por eso hay dos catálogos y el check sabe de qué lenguaje es cada ejemplo (por el bloque
```` ```vega ```` o ```` ```vega-lite ````, o por el `lang` del borrador). Es el equivalente a los
dos catálogos de `spark-for-agents` (Spark SQL + PySpark) en un solo repo.

## 6. Salida de pre-release

Cuando las piezas 1–6 estén en `main` y una prueba de invención (como la de
`powerquery-m-for-agents`) muestre la mejora, se quita el aviso de pre-release y se propone a
Cristóbal enviarlo al directorio de plugins.
