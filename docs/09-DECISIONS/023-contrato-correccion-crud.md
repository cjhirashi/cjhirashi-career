# ADR-023 — Contrato de corrección: CRUD 100% Admin para Grupos/Secciones + niveles de visibilidad

> Este documento **corrige** `023-contrato-implementacion.md` en lo que toca a Grupos y
> Secciones (L1/L2/L3), según la sección **"Corrección — Grupos/Secciones pasan a gestión
> 100% Admin (2026-08-28, post-QA en producción)"** de
> [`023-admin-sections-hierarchy-views.md`](023-admin-sections-hierarchy-views.md). Esa
> sección del ADR **manda** sobre cualquier regla anterior en conflicto (en particular sobre
> el Ruling #1 del contrato original, que diferían el cambio de nivel a un lote posterior).
>
> **No implementa nada.** Es el contrato que consume `api-rest-developer`. El código de
> producción (`develop`, commit `babd50f`) queda intacto hasta que se implemente este
> contrato.
>
> Alcance: **NO** toca el modelo de vistas (`admin_views`), sus 3 paneles del sidebar
> derecho, la tool Bedrock `admin_view_settings`, `resolve_profile_for_turn` ni
> `match_active_view` — todo eso queda "confirmado correcto" por el ADR y fuera de esta
> corrección, salvo el único campo nuevo que se abre en `AdminViewUpdateRequest` (§2).

---

## 0. Qué cambia y qué no cambia respecto al contrato original

| Pieza | Estado original (`023-contrato-implementacion.md`) | Estado corregido (este documento) |
|---|---|---|
| 6 tablas, PKs `grp-N`/`s1-N`/`s2-N`/`s3-N`/`vw-N` | vigente | **sin cambio** |
| Grupos/Secciones L1/L2/L3: quién las crea/edita/borra | seeder de código (`sync_structure`), API solo reorder/re-parent mismo nivel | **API CRUD completo** (crear, editar campos, eliminar, reordenar, mover de nivel). Seeder deja de tocarlas tras el primer arranque. |
| `origin` en `admin_sections_l1/l2/l3` | `'code'` para todo; prune del seeder activo | Filas creadas por el Admin nacen `origin='admin'`. El prune de grupos/secciones **se retira** de `sync_structure` (§5) — ya no corre en ningún arranque. |
| `admin_views` (código, prune, upsert) | vigente, seeder sigue sembrando/pruneando vistas | **sin cambio** — las vistas siguen naciendo en código |
| `owner_l1_id`/`owner_l2_id`/`owner_l3_id` de una vista | fijo, asignado por el seeder | **reasignable desde el Admin** vía `PUT /admin/views/{vw_id}` (§2) |
| Cambio de nivel de sección (L1↔L2↔L3) | diferido a lote posterior (Ruling #1) | **implementado en este contrato** (§1.6) |
| Restricción de visibilidad de grupo/sección/vista | no existe | **columna `visibility_level: String` nueva en las 4 tablas** `admin_section_groups`, `admin_sections_l1/l2/l3` y **`admin_views`** (§3) — mecanismo genérico, extensible a más niveles sin migrar el schema, no un boolean amarrado a un solo grupo |
| `users.is_superuser` | no existe | **columna nueva** (Boolean); es la única pieza binaria del diseño — determina qué `visibility_level` puede ver el usuario, no reemplaza el campo de la fila (§3) |
| `init_db()` | llama `sync_structure()` (grupos+secciones+vistas) | llama una versión reducida: solo vistas + alta idempotente del grupo/sección `admin` (§4) |

---

## 1. Endpoints — Grupos y Secciones (CRUD completo)

Prefijo `/admin`, JWT en todos (`get_current_user`), router `routes/admin_sections.py`.
Las rutas de vistas (§2) y `GET /admin/nav-tree` no cambian de forma, solo de contenido
disponible (ahora hay más grupos/secciones porque el operador puede crear).

Todas las mutaciones de este bloque exigen el **gate de nivel de visibilidad** (§3) cuando
el `visibility_level` de la fila tocada exige más que lo que el usuario actual satisface —
en la práctica hoy eso solo aplica al grupo `admin` y a su sección "Secciones del Admin"
(las únicas dos filas con `visibility_level="superuser"`); el resto de grupos/secciones
(los ~65 actuales: 11 grupos + 54 secciones, todas `visibility_level="standard"`) son
editables/eliminables por **cualquier** usuario autenticado del Admin, igual que hoy. El
gate compara el `visibility_level` de la fila contra el nivel del usuario de forma
**genérica** — no hay ningún `if system_name == "admin"` en el código de permisos; el caso
`admin` es simplemente la única fila con ese nivel hoy, ver §3.

### 1.1 `POST /admin/section-groups` — crear grupo

Request:
```jsonc
{ "name": "Marketing",           // requerido, 1-120 chars, único (case-sensitive, igual que hoy)
  "system_name": "marketing",    // requerido, 1-60 chars, único, slug (regex ^[a-z][a-z0-9-]*$)
  "sort_order": 200,             // opcional; default = (max(sort_order) existente + 10)
  "visibility_level": "standard" } // opcional; default "standard" — ver §3 (VISIBILITY_LEVELS)
```
Response `201`:
```jsonc
{ "id": "grp-12", "system_name": "marketing", "name": "Marketing", "sort_order": 200,
  "visibility_level": "standard" }
```
Errores: `409` si `name` o `system_name` ya existen; `422` shape/regex, o `visibility_level`
fuera de `VISIBILITY_LEVELS` (§3.1); `400 "system_name 'admin' is reserved for the
protected admin group"` si `system_name == "admin"` — **siempre rechazado por este
endpoint**, incluso para un superusuario: el grupo `admin` es único, sembrado una sola vez
por la migración (§5), y **no forma parte del CRUD genérico** (no se crea por API bajo
ninguna circunstancia, ver §3.3).

`system_name` pasa a ser **requerido en el body** (antes solo lo asignaba el código). Es
obligatorio porque `"admin"` sigue siendo la clave estable con la que el resto del sistema
localiza el grupo protegido (§3.2) — de ahí que se valide y rechace explícitamente en vez de
dejarlo colisionar con el índice único y devolver un `409` genérico menos claro.

`SectionGroupItem` (schema de respuesta) gana los campos `origin: str` (ver §1.7) y
`visibility_level: str` (ver §3).

### 1.2 `DELETE /admin/section-groups/{grp_id}`

**Decisión: bloquear el borrado si el grupo tiene secciones L1 hijas.** No hay cascada.

- `404` si `grp_id` no existe.
- `403 "the admin group is protected and cannot be deleted"` si `grp_id` es el grupo
  protegido `admin` — **siempre**, sin importar el nivel del usuario ni aunque sea
  superusuario (ver §3.3: el grupo `admin` no forma parte del CRUD genérico, no se borra
  por API bajo ninguna circunstancia).
- `409 "group grp-N has 3 child section(s); move or delete them first"` si `admin_sections_l1`
  tiene filas con `group_id = grp_id`.
- `204` si está vacío y no es el grupo `admin`.

Nótese que este `403` **no** depende de comparar `visibility_level` — es una protección
distinta y más fuerte ("no forma parte del CRUD", ni con el nivel más alto) que el gate
general de lectura/escritura por nivel de visibilidad (§3.3). El gate por `visibility_level`
aplica a lectura y a las mutaciones permitidas (editar `sort_order`); el borrado del grupo
`admin` está bloqueado siempre, independientemente de ese gate.

**Por qué bloquear en vez de cascada:** un grupo con secciones vivas casi siempre representa
un error del operador (arrastró el grupo equivocado) más que una intención real de borrar
en bloque decenas de vistas y su configuración de agente/instrucciones. Igual que en
ADR-021/ADR-018 (`RESTRICT` en la FK `admin_sections_l1.group_id`, ya así en el modelo
actual — `ondelete="RESTRICT"`), el patrón del proyecto es **explícito antes que
destructivo**: forzar a vaciar el contenedor primero (mover o borrar sus secciones) hace el
borrado accidental imposible sin pasos deliberados. La FK ya es `RESTRICT`, así que un
`DELETE` sin este chequeo previo fallaría igual con un `IntegrityError` 500 sin mensaje
útil — el `409` explícito es solo mejor UX del mismo comportamiento que ya impone la BD.

### 1.3 `POST /admin/sections` — crear sección L1/L2/L3

Request:
```jsonc
{ "level": 1,                    // requerido, 1|2|3
  "label": "Campañas",           // requerido, 1-120 chars
  "system_name": "campaigns",    // requerido, 1-80 chars, único GLOBAL (no solo por nivel — ver nota)
  "path": "/campaigns",          // opcional; único global L1+L2+L3 si no-NULL (índice parcial existente)
  "section_type": "table",       // requerido, enum: table|functional|metrics|bucket
  "group_id": "grp-12",          // requerido SI level==1; ignorado si viene con level!=1 -> 422
  "parent_id": "s1-9",           // requerido SI level in (2,3); ignorado si level==1 -> 422
  "visibility_level": "standard" } // opcional; default "standard" — ver §3
```
Response `201` — mismo shape que `SectionDetail` (con `views: []`, `origin: "admin"`,
`visibility_level`).

Validaciones:
- `422` si falta `group_id` cuando `level==1`, o falta `parent_id` cuando `level in (2,3)`,
  o vienen ambos, o `level` fuera de `{1,2,3}`, o `visibility_level` fuera de
  `VISIBILITY_LEVELS` (§3.1).
- `400` si `group_id` no existe (level 1); `400` si `parent_id` no existe o su nivel no es
  `level - 1` (level 2 → padre debe ser `s1-N`; level 3 → padre debe ser `s2-N`).
- `409` si `system_name` ya existe (unicidad global, ver nota) o si `path` ya existe
  (índice parcial único existente, compartido entre los 3 niveles).
- `400 "cannot create a section inside the protected admin group"` si `group_id`/
  `parent_id` resuelve (directa o transitivamente) al grupo protegido `admin` — **siempre**
  bloqueado, sin importar el rol del usuario ni su `visibility_level` (§3.3: el grupo
  `admin` y su única sección son sembrados una sola vez por la migración, cerrados a alta
  por API). No es un `403` de permisos insuficientes — es un `400` porque la operación no
  existe para nadie, igual que crear un segundo grupo `system_name="admin"` (§1.1).

**Nota — unicidad de `system_name`:** el modelo actual declara `unique=True` **por tabla**
(`admin_sections_l1.system_name`, `l2`, `l3` cada una con su propio índice unique), no un
unique global entre las tres. Con el cambio de nivel (§1.6, que reasigna la fila a otra
tabla conservando el mismo `system_name`) esto es suficiente — el valor viaja con la fila,
nunca colisiona consigo mismo. Se mantiene así (no se agrega un unique cross-tabla): sería
una migración adicional sin beneficio, dado que el cambio de nivel ya migra la fila
completa (§1.6) y no hay caso en que dos filas de niveles distintos compitan por el mismo
`system_name` salvo que el operador cree deliberadamente uno duplicado — en ese caso el
`409` de la tabla destino en el momento de crear ya lo evita.

`origin` de una fila creada por este endpoint es siempre `"admin"` — el seeder de código
nunca la tocará ni la podrá prunear (§5). `visibility_level` de una sección creada por el
operador es libre (cualquier valor de `VISIBILITY_LEVELS`, default `"standard"`) — nada
impide que el operador cree, por ejemplo, una sección nueva con `visibility_level=
"superuser"` fuera del grupo `admin` si en el futuro quiere restringir otra área; el
mecanismo es genérico y no está amarrado a ese grupo (§3).

### 1.4 `PUT /admin/sections/{sid}` — ampliado (reemplaza `SectionReparentRequest`)

Antes solo `sort_order`/`group_id`/`parent_id`. Ahora también `label`, `system_name`,
`path`, `section_type`. **El cambio de nivel NO va en este endpoint** — va en `POST
/admin/sections/{sid}/move` (§1.6), porque implica migrar la fila entre tablas (no es un
UPDATE de columna) y necesita su propio contrato de request/response.

```jsonc
// Nuevo schema: SectionUpdateRequest (reemplaza SectionReparentRequest)
{ "label": "Campañas 2026",        // opcional
  "system_name": "campaigns-2026", // opcional, único en su tabla de nivel
  "path": "/campaigns-2026",       // opcional; "" explícito = poner a NULL (nodo sin layout)
  "section_type": "functional",    // opcional, enum
  "sort_order": 30,                // opcional
  "visibility_level": "standard",  // opcional — ver §3
  "group_id": "grp-3",             // opcional; solo L1 (re-parent dentro del mismo nivel)
  "parent_id": "s1-9" }            // opcional; solo L2/L3 (re-parent dentro del mismo nivel)
```
`model_config = ConfigDict(extra="forbid")` se mantiene.

Comportamiento (extiende, no reemplaza, la lógica ya implementada de `group_id`/`parent_id`
en `section_catalog.update_section`):
- `label`/`section_type`: reemplazo directo tras validar tipo/enum.
- `system_name`: `409` si colisiona con otra fila de la misma tabla de nivel.
- `path`: `""` → `NULL` (nodo agrupador sin layout); valor no vacío → `409` si colisiona con
  el índice parcial único (global L1+L2+L3); se valida formato (`^/`).
- `visibility_level`: `422` si no está en `VISIBILITY_LEVELS` (§3.1); sin restricción
  adicional de "quién puede subir/bajar el nivel de una fila" en este lote — cualquier
  usuario que ya pase el gate de escritura de esa fila (§3.3) puede cambiar su
  `visibility_level` a cualquier valor válido, incluido asignarle `"superuser"` a una
  sección propia. Es una decisión deliberadamente simple para el alcance actual (un único
  nivel adicional); si en el futuro se necesita "solo un superuser puede *otorgar* nivel
  superuser", es un endurecimiento posterior, no bloquea este contrato.
- `sort_order`, `group_id`, `parent_id`: sin cambio de comportamiento respecto al código
  actual (`update_section` en `section_catalog.py`), incluida la detección de ciclo directo
  (`parent_id == sid` → `409 CycleError`) y el chequeo de nivel del padre.
- Response: `200 SectionDetail` (igual que hoy, + `visibility_level`).
- Errores: `404` sid; `400` referencias inválidas/nivel incorrecto; `409` unicidad/ciclo;
  `422` shape; `403` si el `visibility_level` **actual** de `sid` excede lo que el usuario
  satisface (§3.3, gate genérico por nivel — no un chequeo de `system_name`).

**Excepción — la sección "Secciones del Admin" no se edita en absoluto por este endpoint**,
ni siquiera por un superusuario: `403 "the admin sections screen is protected and cannot be
edited"` para cualquier campo. Es la única sección de todo el sistema completamente cerrada
a `PUT` (a diferencia del grupo `admin`, que sí permite cambiar su `sort_order` — ver
§1.2/§3.3). No hay nada configurable en ella (no tiene vistas propias reasignables, su
`label`/`path`/`system_name` son fijos) — bloquear el `PUT` entero es más simple y más
seguro que abrir solo un subconjunto de campos que en la práctica nadie necesita tocar.

### 1.5 `DELETE /admin/sections/{sid}`

**Decisión: bloquear si tiene subsecciones hijas O vistas propias.** Igual criterio que
§1.2 (grupos): sin cascada de estructura.

- `404` si `sid` no existe.
- `403 "the admin sections screen is protected and cannot be deleted"` si `sid` **es** la
  sección "Secciones del Admin" — **siempre**, sin importar el nivel del usuario (no forma
  parte del CRUD genérico, §3.3, mismo tratamiento que el grupo `admin` en §1.2).
- `403` (gate genérico por nivel, §3.3) si `sid` tiene un `visibility_level` que el usuario
  actual no satisface — en la práctica hoy esto nunca dispara para otra sección aparte de
  la de arriba, porque es la única con `visibility_level != "standard"`, pero el chequeo es
  genérico (compara nivel de la fila vs. nivel del usuario), no un `if` especial para ella.
- `409 "section s1-N has 2 child section(s); move or delete them first"` si tiene hijas
  (L1 con hijas L2, o L2 con hijas L3).
- `409 "section s1-N owns 3 view(s); reassign them to another section first"` si tiene
  `admin_views` propias (`owner_l{n}_id = sid`) — **incluyendo** vistas con
  `responsible_agent_profile_id`/`instructions` en NULL (una vista "vacía" de configuración
  sigue siendo una vista viva que pertenece a una pantalla real construida en código; no se
  puede huérfanar).
- `204` si no tiene hijas ni vistas.

**Por qué bloquear (y no cascada) en ambos casos (§1.2 y §1.5):** las vistas no son
estructura efímera — cada una es una pantalla real (`resource_key`/`data_source`/
`tool_names` de código) que un desarrollador construyó y que el sidebar del Admin necesita
para renderizar. Borrar en cascada una sección con vistas dejaría "pantallas huérfanas"
(código que sigue existiendo, ruta que ya no aparece en ningún sidebar, y el operador sin
darse cuenta de cuántas vistas mató). Forzar `reasignar → luego borrar` (mover cada vista a
otra sección vía `PUT /admin/views/{id}` con nuevo `owner_*`, o mover las subsecciones hijas
a otro padre vía `POST /admin/sections/{sid}/move` o `PUT .../group_id|parent_id`) hace el
borrado deliberado y auditable, coherente con el patrón `RESTRICT` que ya usan las FKs de
`group_id` y con la decisión de grupos de §1.2. Es más estricto que el `ON DELETE CASCADE`
que hoy tienen las FKs `admin_sections_l2.parent_l1_id` / `l3.parent_l2_id` /
`admin_views.owner_l1_id` — ese CASCADE queda como red de seguridad a nivel BD para casos
fuera de la API (migraciones, `downgrade`), pero el **endpoint** nunca debe ejercitarlo
directamente sin el paso explícito de vaciar primero.

### 1.6 Mover una sección entre niveles — `POST /admin/sections/{sid}/move`

Diseño de endpoint: **ruta dedicada `POST`, no fusionada en el `PUT`**. Un `PUT` que además
puede cambiar de tabla-PK-prefijo (efecto secundario: la URL del recurso deja de ser válida
tras la propia llamada que la invocó) es una violación de semántica REST más seria que la de
`group_id`/`parent_id` dentro del mismo nivel (ahí el recurso sigue siendo `sid`, solo cambia
su padre). Un `POST` a un sub-recurso de acción dedicado (`/move`) dice explícitamente "esto
es una operación, no una actualización de campos" y permite devolver el **nuevo id** de forma
inequívoca sin sobrecargar la semántica de `200 PUT` (que normalmente implica "mismo recurso,
campos actualizados").

Request:
```jsonc
POST /admin/sections/{sid}/move
{ "target_level": 2,              // requerido, 1|2|3, distinto del nivel actual de sid
  "target_parent_id": "s1-9" }    // requerido; grp-N si target_level==1, s1-N si ==2, s2-N si ==3
```
Response `200`:
```jsonc
{ "id": "s2-15",                  // NUEVO id (prefijo del nivel destino)
  "previous_id": "s1-42",         // id anterior, para que el front actualice caché/URLs abiertas
  "level": 2,
  "system_name": "campaigns",
  "label": "Campañas",
  "path": "/campaigns",
  "section_type": "table",
  "sort_order": 30,               // ver regla de sort_order abajo
  "origin": "admin",
  "group_id": null,
  "parent_id": "s1-9",
  "view_count": 3,
  "views": [ /* AdminViewItem[], con owner_l2_id ahora apuntando al nuevo id */ ]
}
```

**Regla de alcance (documentada en el ADR): la sección a mover NO puede tener subsecciones
hijas propias.** Si `sid` es L1 con hijas L2, o L2 con hijas L3, el move devuelve:

```
409 "section s1-N has 2 child section(s); move or delete them first (moving a section
     with children between levels is not supported yet)"
```

**Por qué esta restricción (documentado explícitamente, reemplaza el diferimiento total del
Ruling #1 original):** el ADR pide soportar mover-entre-niveles, pero no especifica qué pasa
con los descendientes de una sección que se mueve. Hay dos lecturas posibles: (a) re-anidar
recursivamente todo el subárbol (una L1 con 3 hijas L2 que se mueve a L2 tendría que
convertir esas 3 hijas en... ¿nietas L3? — pero L3 es la hoja, no puede tener hijas, así que
una L1→L2 con hijas L2 existentes rompería el árbol en cuanto una de esas hijas tuviera a su
vez hijas L3); o (b) permitir el move solo cuando la sección está "limpia" de hijas (deja el
subárbol intacto, el operador decide explícitamente qué hacer con las hijas antes). Se elige
**(b)** para el alcance de este contrato porque: la migración recursiva de un subárbol
completo con reasignación en cascada de owners de vistas en cada nivel es una operación de
mucho mayor superficie de bugs (validar que ningún nivel resultante exceda L3, recalcular
[¿reordenar?] `sort_order` en cada nivel migrado, decidir qué pasa si una hija L3 terminaría
necesitando ser L4 inexistente) que no está pedida explícitamente por el dueño del producto
— lo que pidió es "mover secciones entre niveles", que la UI puede resolver perfectamente
pidiendo al operador "vacía esta sección primero" (mismo patrón de UX que el borrado, §1.5).
Si más adelante se necesita mover subárboles completos, es un **follow-up separado**
(anotado en §7) con su propio contrato — no bloquea este.

Algoritmo paso a paso (una única transacción DB; cualquier fallo revierte todo):

```
1.  level_actual = nivel de sid por prefijo (s1→1, s2→2, s3→3)
    if target_level == level_actual: 400 "target_level must differ from the current level"
    if target_level not in (1,2,3): 422

2.  row = SELECT de la tabla de level_actual WHERE id = sid
    if row is None: 404

3.  hijas = SELECT COUNT(*) de la tabla de (level_actual+1) WHERE parent_col = sid
    (si level_actual == 3, hijas = 0 siempre, L3 no tiene tabla hija)
    if hijas > 0: 409 "has N child section(s); move or delete them first"

4.  # Validar el padre/contenedor destino
    if target_level == 1:
        target = SELECT admin_section_groups WHERE id = target_parent_id
        if target is None: 400 "unknown section group: target_parent_id"
    else:
        parent_level_esperado = target_level - 1
        target = SELECT tabla(parent_level_esperado) WHERE id = target_parent_id
        if target is None: 400 "unknown parent section: target_parent_id"
        # (target_parent_id ya trae su propio nivel codificado en el prefijo;
        #  si target_parent_id es s1-N pero target_level pide un padre L2, es un 400
        #  "target_parent_id must be a level {target_level-1} section")

5.  # Gate genérico por nivel de visibilidad (§3.3)
    if sid == "sección Secciones del Admin": 403 "protected, cannot be moved"
    if visibility_level(sid) no satisfecho por current_user: 403
    if visibility_level(target contenedor) no satisfecho por current_user: 403
    # target contenedor = el grupo (target_level==1) o la sección padre (target_level 2/3)
    # resuelto en el paso 4. Comparación genérica contra VISIBILITY_LEVELS (§3.1), no un
    # chequeo de system_name=="admin".

6.  # Asignar nuevo id con el prefijo del nivel destino
    new_id = next value de la secuencia del nivel destino (s1_id_seq / s2_id_seq / s3_id_seq)
             -- MISMO mecanismo que register_id_listener, pero invocado a mano
                (nextval('{prefix}_id_seq')) porque esto NO es un INSERT nuevo desde
                SQLAlchemy vía before_insert: es un INSERT explícito + DELETE del original,
                dentro de la misma función de servicio.

7.  # Crear la fila en la tabla destino con el nuevo id, copiando todas las columnas
    #  de dominio + operador (label, system_name, path, section_type, sort_order [ver
    #  nota], origin, created_at) y el nuevo FK de contenedor:
    INSERT INTO tabla(target_level) (
        id=new_id,
        group_id=target_parent_id (si target_level==1) | NULL,
        parent_l1_id=target_parent_id (si target_level==2) | NULL,
        parent_l2_id=target_parent_id (si target_level==3) | NULL,
        system_name=row.system_name, label=row.label, path=row.path,
        section_type=row.section_type,
        sort_order = MAX(sort_order) + 10 entre las hermanas ya existentes bajo
                     target_parent_id  -- ver nota "sort_order" abajo
        visibility_level=row.visibility_level,  -- viaja intacto con la fila
        origin=row.origin, created_at=row.created_at
    )

8.  # Reasignar las vistas propias de la sección al nuevo id
    UPDATE admin_views SET owner_l{target_level}_id = new_id, owner_l{level_actual}_id = NULL
    WHERE owner_l{level_actual}_id = sid

9.  # Borrar la fila original (ya no tiene hijas -- paso 3 -- ni vistas -- paso 8)
    DELETE FROM tabla(level_actual) WHERE id = sid

10. invalidate_cache()  # section_catalog._CACHE
11. COMMIT
12. return sección recién creada (new_id) con sus vistas, shape SectionDetail + previous_id
```

**Nota — `sort_order` en el destino:** no se conserva el `sort_order` original (perdería
sentido comparado con las hermanas del nuevo contenedor). Se asigna al final de la lista de
hermanas del `target_parent_id` (mismo patrón `idx*10` que usa `reorder_sections`, aquí
`MAX(sort_order) + 10`, o `10` si el contenedor destino no tiene hijas todavía). El operador
puede reordenar después con `PUT /admin/sections/order`.

**Nota — por qué DELETE+INSERT y no `UPDATE ... SET tableoid`:** PostgreSQL no soporta mover
una fila entre tablas con un UPDATE (son relaciones distintas); es inherente a que L1/L2/L3
son 3 tablas separadas (decisión ya tomada y confirmada correcta por el ADR — no se
introduce una tabla `admin_sections` unificada con columna `level` porque el ADR raíz
descarta explícitamente esa alternativa por las FKs de contenedor tipadas por nivel). El
DELETE+INSERT dentro de una única transacción con `invalidate_cache()` al final es
equivalente a una operación atómica desde la perspectiva del cliente.

**Nota — por qué recalcular las FKs de vistas (paso 8) y no dejarlas apuntando al id viejo:**
el CHECK `ck_admin_views_single_owner` exige que la vista apunte a una fila que exista en
la tabla del nivel correspondiente; si `sid` se borra de `admin_sections_l1` sin reasignar
sus vistas primero, el `ON DELETE CASCADE` de `admin_views.owner_l1_id` las **borraría** —
efecto claramente no deseado (perdería configuración de agente/instrucciones de código real).
Por eso el paso 8 ocurre **antes** del paso 9 en la misma transacción.

Errores totales del endpoint: `404` sid; `400` target inválido/mismo nivel/nivel de padre
incorrecto; `409` tiene hijas; `403` gate de visibilidad (origen, destino, o intento de
mover la sección protegida); `422` shape.

### 1.7 Cambios de schema (`schemas/admin_sections.py`)

- `SectionGroupItem`: **+ `origin: str`**, **+ `visibility_level: str`**.
- `SectionListItem` / `SectionDetail`: **+ `origin: str`** (ya existe en el modelo, faltaba
  exponerlo), **+ `visibility_level: str`** (nueva columna, §3).
- `NavGroup`, `NavSection`, `NavView` (nav-tree, §3.4): **+ `visibility_level: str`** en los
  tres, para que el front pueda, si quiere, mostrar un indicador visual de "esto es
  restringido" a un superusuario que sí ve la fila (uso opcional de UI; el filtrado real es
  server-side, no depende de que el front lea este campo).
- **Nuevo** `SectionGroupCreateRequest` (`name`, `system_name`, `sort_order: Optional[int]`,
  `visibility_level: Optional[str]` default `"standard"`).
- **Nuevo** `SectionCreateRequest` (`level`, `label`, `system_name`, `path: Optional[str]`,
  `section_type`, `group_id: Optional[str]`, `parent_id: Optional[str]`,
  `visibility_level: Optional[str]` default `"standard"`) con validador a nivel Pydantic
  (`model_validator`) que exige exactamente uno de `group_id`/`parent_id` según `level`
  (falla temprano con `422` antes de tocar la BD), y valida `visibility_level ∈
  VISIBILITY_LEVELS`.
- `SectionReparentRequest` → renombrado **`SectionUpdateRequest`**, gana `label`,
  `system_name`, `path`, `section_type`, `visibility_level` (todos opcionales,
  `extra="forbid"` se mantiene).
- **Nuevo** `SectionMoveRequest` (`target_level: int`, `target_parent_id: str`).
- **Nuevo** `SectionMoveResponse` = `SectionDetail` + `previous_id: str` (incluye
  `visibility_level`, que viaja intacto en el move, §1.6).
- `AdminViewItem` (§2): **+ `visibility_level: str`**.
- `VISIBILITY_LEVELS` (§3.1) se define en `services/section_catalog.py` (o
  `services/admin_sections.py`, junto al resto del registro de código) e importa en
  `schemas/admin_sections.py` para el validador Pydantic — una única fuente de verdad para
  el enum, no duplicada entre capa de servicio y capa de schema.

---

## 2. Reasignación de sección dueña de una vista

Amplía `AdminViewUpdateRequest` y `PUT /admin/views/{vw_id}` (sin tocar el resto del
contrato de vistas — chat contextual, instrucciones, tool Bedrock `admin_view_settings`,
todo eso sigue igual).

```jsonc
// AdminViewUpdateRequest — todos opcionales, extra="forbid"
{ "responsible_agent_profile_id": "agent_search_operations",  // sin cambio (ya existía)
  "instructions": "...",                                       // sin cambio (ya existía)
  "owner_l1_id": "s1-9",     // NUEVO — mueve la vista a esta sección L1
  "owner_l2_id": null,       // NUEVO
  "owner_l3_id": null }      // NUEVO
```

Reglas:
- **Exactamente uno** de `owner_l1_id`/`owner_l2_id`/`owner_l3_id` no-nulo, si se envía
  cualquiera de los tres — mismo CHECK que ya existe en el modelo
  (`ck_admin_views_single_owner`). Enviar los tres como `null` es inválido; enviar dos no
  nulos es inválido.
- Si **ninguno** de los tres campos de owner viene en el body (`model_fields_set` no los
  incluye) → no se toca el owner actual (comportamiento actual preservado, retrocompatible).
- Si **alguno** viene, se interpreta como "reemplazar el owner completo": el servicio arma
  el nuevo trío `(owner_l1_id, owner_l2_id, owner_l3_id)` a partir de los campos presentes
  en el body (ausentes = se asume `null` para ese campo del trío nuevo — es decir, para
  mover de L1 a L2 basta con enviar `{"owner_l2_id": "s2-3"}`; el servicio pone
  `owner_l1_id=NULL` automáticamente).
- El id destino debe existir en la tabla del nivel correspondiente → `400 "unknown target
  section: s2-3"` si no.
- La unicidad de `key` por sección (los 3 índices parciales únicos existentes) sigue
  aplicando: si la sección destino ya tiene una vista con el mismo `key`, `409 "section
  s2-3 already has a view with key 'main'"`.
- `404` si `vw_id` no existe.
- Gate de superusuario: **no aplica** a vistas (las vistas nunca cuelgan del grupo `admin`
  en este lote — la única sección del grupo `admin` es "Secciones del Admin", que es
  `data_source=functional`/`external` de código sin necesidad de reasignación por el
  operador; si en el futuro se le agregan vistas reasignables, se revisita).

Response: `200 AdminViewItem` (mismo shape ya existente, con `owner` reflejando la nueva
sección).

`section_catalog.update_view(...)` gana los kwargs `owner_l1_id`/`owner_l2_id`/`owner_l3_id`
(mismo patrón `_UNSET` sentinel ya usado para `responsible`/`instructions` — "ausente" ≠
"null explícito").

---

## 3. `is_superuser` y el grupo protegido `admin`

### 3.1 Columna nueva en `users`

```python
is_superuser = Column(Boolean, nullable=False, default=False, server_default=text("false"))
```
Ubicación: bloque "Estado de cuenta" de `models/user.py`, junto a `is_active`/`is_verified`.

Migración (§5) hace `ALTER TABLE users ADD COLUMN is_superuser BOOLEAN NOT NULL DEFAULT
false`, luego **backfill `UPDATE users SET is_superuser = true`** para todas las filas
existentes — el sistema es single-tenant hoy (solo Carlos tiene cuenta), así que "todos los
usuarios existentes son superusuario" preserva exactamente el acceso actual sin romper nada;
cuentas nuevas creadas después de la migración nacen con `is_superuser=false` por el
`default=False` del modelo (una futura invitación de colaborador no hereda superuso por
accidente).

### 3.2 Cómo se identifica "el grupo admin"

**Por `system_name` fijo `"admin"`** — mismo patrón que ya usa el código para localizar
constructos especiales por su clave estable (p. ej. `_GROUP_SYSTEM_BY_NAME` hoy resuelve por
`name`/`system_name` de código, nunca por PK numérico, precisamente porque el PK es
consecutivo y no memorizable). `system_name="admin"` es un valor **reservado**: `POST
/admin/section-groups` rechaza con `400` cualquier intento de crear otro grupo con ese
`system_name` (§1.1) — así el gate de las rutas puede resolver el grupo protegido con un
único `SELECT ... WHERE system_name = 'admin'` sin ambigüedad, sin depender de un PK
hardcodeado que se rompería en un entorno donde el grupo nace con otro consecutivo.

No se agrega una columna `is_protected`/`is_system` en `admin_section_groups`: sería
redundante con el `system_name` reservado y abriría la puerta a "proteger" grupos
arbitrarios sin que el ADR lo haya pedido — el alcance de esta corrección es un único grupo
protegido, conocido de antemano.

### 3.3 Mecanismo de gate

**Regla general:** el gate aplica a nivel de **grupo `admin` y todo su subárbol** (secciones
L1/L2/L3 que cuelguen, directa o transitivamente, de `grp-admin`), no a la sección
individual "Secciones del Admin" — así cualquier sección nueva que se cree en el futuro
*dentro* de ese grupo hereda la protección automáticamente sin tener que enumerar
excepciones.

**Lectura — `GET /admin/nav-tree`:**
```
if not current_user.is_superuser:
    filtrar del árbol devuelto el/los grupo(s) con system_name == "admin" (y todo su
    subárbol de secciones/vistas) ANTES de serializar la respuesta
```
Filtrado **server-side**, no un flag `visible: bool` en el JSON — el objetivo es que un
usuario no-superuser ni siquiera sepa que existe la pantalla de gestión de Secciones del
Admin (coherente con "visible solo para is_superuser" del ADR, no "visible pero
deshabilitado"). `list_nav_tree` recibe el `current_user` (o su `is_superuser: bool`) como
parámetro nuevo.

**Lectura — `GET /admin/section-groups`, `GET /admin/sections/{l1|l2|l3}`, `GET
/admin/sections/{sid}`:** mismo filtro — excluyen filas del subárbol `admin` si
`not is_superuser`. Un `GET /admin/sections/{sid}` directo a una sección protegida sin ser
superusuario devuelve `404` (no `403`) para no confirmar la existencia del recurso a un
usuario sin permiso — mismo patrón de "no filtrar por enumeración" que ya usan otras rutas
protegidas del proyecto.

**Escritura — todas las de §1 (`POST`/`PUT`/`DELETE` de grupos y secciones) y el `move`
de §1.6:** antes de mutar, resolver si el recurso afectado (el propio grupo/sección, o —
para `move`/`group_id`/`parent_id` — el contenedor **origen o destino**) pertenece al
subárbol `admin`; si sí y `not current_user.is_superuser` → `403 "forbidden: the admin
group is restricted to superusers"`. Si el usuario **sí** es superusuario, todas las
operaciones de §1 se permiten **salvo**:
- **Borrar el grupo `admin`** (`DELETE /admin/section-groups/{grp-admin}`): siempre `403`,
  incluso siendo superusuario — igual que no se puede borrar la tabla `error_reports` desde
  la UI. Es infraestructura del propio sistema de administración, no un grupo de contenido.
- **Borrar la sección "Secciones del Admin"** (`DELETE /admin/sections/{sid}` donde `sid`
  es esa sección): mismo `403` permanente — sin ella no hay pantalla desde la que
  administrar nada.
- Mover la sección "Secciones del Admin" a otro grupo, o mover otra sección **hacia dentro**
  del grupo `admin`: **permitido** para superusuarios (no hay razón funcional para
  impedirlo — el operador podría querer reorganizar qué otras pantallas de administración
  viven ahí en el futuro), solo el borrado total de esos dos recursos específicos está
  bloqueado.

**Implementación:** helper `_is_admin_subtree(db, section_or_group_id) -> bool` en
`section_catalog.py` (resuelve hacia arriba hasta el grupo raíz y compara `system_name ==
"admin"`, usando la caché en memoria ya existente — sin queries extra en el camino
caliente). Dependency FastAPI `require_superuser_for_admin_group` que envuelve
`get_current_user` + el helper, usada como `Depends()` adicional (no reemplaza
`get_current_user`) en las rutas de §1 que mutan.

**Nota — por qué gate en cada ruta y no un middleware global:** el 99% de grupos/secciones
NO están protegidos (son de contenido de carrera, libres para cualquier usuario del Admin);
un middleware global que exigiera superuso para *todo* `/admin/section-groups` y
`/admin/sections/*` rompería el caso común. El gate tiene que ser condicional al recurso
tocado, no a la ruta — de ahí que viva en la capa de servicio (`section_catalog`) donde ya
se resuelve la jerarquía, y no en un decorator de ruta genérico.

---

## 4. Qué corre y qué no corre en `init_db()`

Estado actual (`database.py::init_db()`, líneas 67-89): `create_all` → crear secuencias →
`sync_structure(session)` (grupos + secciones L1 + vistas, upsert + prune completo).

**Estado corregido:**

```python
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        for prefix in TABLE_PREFIXES.values():
            await conn.execute(text(f"CREATE SEQUENCE IF NOT EXISTS {prefix}_id_seq START 1"))

    from services.admin_sections_seed import sync_views, ensure_admin_group_and_section

    async with AsyncSessionLocal() as session:
        await ensure_admin_group_and_section(session)   # NUEVO — solo-alta, idempotente
        await sync_views(session)                         # RENOMBRADO/RECORTADO de sync_structure
        await session.commit()
```

**Se elimina** de `sync_structure()` (y del arranque) todo lo que tocaba **grupos y
secciones L1/L2/L3**: el upsert de `GROUPS`, el upsert de `admin_sections_l1` a partir de
`list_section_specs()`, y su prune. Esa función se **divide en dos**:

1. **`ensure_admin_group_and_section(session)`** (nueva, en
   `services/admin_sections_seed.py`) — corre en **cada arranque**, pero es **puramente
   de alta idempotente** (nunca hace UPDATE ni prune sobre filas existentes):
   ```
   grp = SELECT admin_section_groups WHERE system_name = 'admin'
   if grp is None:
       INSERT admin_section_groups(id='grp-admin' o el siguiente de la secuencia grp_id_seq,
                                    system_name='admin', name='Administración',
                                    sort_order=0)
   sec = SELECT admin_sections_l1 WHERE system_name = 'admin-sections'
   if sec is None:
       INSERT admin_sections_l1(group_id=grp.id, system_name='admin-sections',
                                 label='Secciones del Admin', path='/settings/sections',
                                 section_type='table', sort_order=0, origin='code')
   # Si ya existen (creadas por la migración, §5, o por un arranque anterior), NO TOCAR
   # NADA — ni siquiera refrescar label/path. A partir de la migración, esta fila es
   # 100% propiedad del operador igual que cualquier otra sección (puede renombrarla,
   # aunque no borrarla — §3.3).
   ```
   Por qué sigue corriendo en cada arranque (a diferencia del resto de grupos/secciones,
   que dejan de sembrarse): es la **única** garantía de que un entorno nuevo (dev local,
   CI, un clon fresco de la BD) tenga el grupo protegido disponible sin depender de que
   alguien recuerde correr la migración a mano primero — mismo razonamiento que ya aplica
   hoy a la creación de secuencias en cada arranque. Al ser puramente "crear si no existe",
   no reintroduce el problema que motivó la corrección (nunca pisa ediciones del operador).

2. **`sync_views(session)`** (renombrado de la porción de vistas de `sync_structure`,
   **sin cambios de comportamiento** — sigue upsert + prune de `admin_views` por
   `(owner_l1_id, key)`, siempre acotado a las columnas de código, nunca toca
   `responsible_agent_profile_id`/`instructions`). Sigue corriendo en cada arranque porque
   las vistas **siguen naciendo en código** — un desarrollador agrega una vista nueva a
   `services/admin_sections.py` (o al registro que corresponda tras esta corrección, ver
   nota abajo) y necesita que aparezca sin migración manual, igual que hoy.

   **Nota — `sync_views` ya no puede leer `list_section_specs()` con la forma actual**,
   porque esa función asumía que las secciones también las sembraba el código (recorría
   `GROUPS` + `AdminSectionSpec.group`/`.system_name` para resolver `l1_id_by_system` antes
   de tocar vistas). Tras esta corrección, `sync_views` debe resolver el **owner** de cada
   vista de código por su `system_name` de sección **contra lo que ya exista en la tabla**
   (no crear la sección si falta — si un desarrollador registra una vista nueva para una
   sección que el operador borró, es un error de configuración a loguear, no una sección a
   recrear):
   ```
   for spec in list_section_specs():   # sigue siendo el registro de código, ahora SOLO
                                         # describe vistas + a qué system_name de sección
                                         # de código pertenecen — ya no crea la sección
       l1 = SELECT admin_sections_l1 WHERE system_name = spec.system_name
       if l1 is None:
           logger.warning("sync_views: sección de código %r ya no existe en BD (borrada "
                           "por el operador); sus vistas de código no se sincronizan",
                           spec.system_name)
           continue
       # upsert de spec.views bajo owner_l1_id = l1.id, igual que hoy
   ```
   Esto es una diferencia de comportamiento real que hay que documentar bien: **si el
   operador borra o mueve de nivel una sección que en código todavía tiene vistas
   registradas, esas vistas de código dejan de sincronizarse silenciosamente** (con
   warning en log). Es la consecuencia esperada de que la estructura ahora manda desde la
   BD — no hay forma de "recrear automáticamente" una sección que el operador eliminó
   deliberadamente sin reintroducir el problema que motivó la corrección completa. Un
   desarrollador que registre una vista nueva debe verificar contra el árbol vivo (`GET
   /admin/nav-tree`) que la sección destino sigue existiendo con ese `system_name`.

**Resumen de qué corre en cada arranque de la API, tras la corrección:**

| Paso | Antes | Después |
|---|---|---|
| `create_all` + crear secuencias | sí | sí (sin cambio) |
| Upsert/prune de **grupos** | sí (`sync_structure`) | **no** |
| Upsert/prune de **secciones L1** | sí (`sync_structure`) | **no** |
| Alta idempotente del grupo+sección **`admin`** (solo si faltan) | — | **sí** (nuevo) |
| Upsert/prune de **vistas** | sí (`sync_structure`) | sí (`sync_views`, misma lógica, resolución de owner ajustada) |
| L2/L3 | nunca las sembró (nacen vacías) | sin cambio |

---

## 5. Migración Alembic

**Archivo nuevo:** `alembic/versions/<rev>_admin_sections_crud_is_superuser.py`.

> ⚠️ **Verificar `down_revision` antes de implementar.** Al momento de escribir este
> contrato, `c4d5e6f7a8b9` (ADR-023 original) es el head de la cadena de migraciones de
> secciones/vistas, pero el repo tiene **dos heads divergentes** en `alembic/versions/`
> (`c4d5e6f7a8b9` y `e5f6a7b8c9d0`, este último de otra rama de trabajo no relacionada). `
> api-rest-developer` debe correr `alembic heads` contra el estado real de `develop` en el
> momento de implementar y encadenar `down_revision` al head efectivo (probablemente
> requiriendo una migración de *merge* si los dos heads siguen divergentes) — no asumir
> `down_revision="c4d5e6f7a8b9"` a ciegas.

### 5.1 `upgrade()`

```python
def upgrade() -> None:
    # 1. is_superuser en users
    op.add_column("users", sa.Column("is_superuser", sa.Boolean(), nullable=False,
                                       server_default=sa.text("false")))
    # server_default cubre el backfill de filas existentes automáticamente (mismo
    # patrón que is_active/is_verified ya usan) -- no hace falta un UPDATE explícito
    # porque server_default="false" + backfill deseado es "true" para preservar acceso:
    op.execute("UPDATE users SET is_superuser = true")
    # (el server_default queda para las filas nuevas que se inserten DESPUÉS de esta
    # migración con is_superuser omitido explícitamente por código legado -- no debería
    # ocurrir ya que el modelo tiene default=False en la capa de app, pero server_default
    # es la red de seguridad a nivel BD)
    # Tras el backfill, endurecer el server_default a 'false' (ya está) -- sin cambio
    # adicional necesario, el UPDATE de arriba solo afecta filas EXISTENTES al momento
    # del upgrade.

    # 2. Grupo + sección `admin` (única siembra determinista de aquí en adelante para
    #    grupos/secciones -- ver mapa congelado, coherente con _FROZEN_GROUPS de
    #    c4d5e6f7a8b9)
    conn = op.get_bind()
    admin_group_id = "grp-12"   # siguiente libre tras _FROZEN_GROUPS (grp-1..grp-11)
    admin_section_id = "s1-55"  # siguiente libre tras _SEC_TO_S1 (s1-1..s1-54)
    now = sa.text("now()")

    existing_group = conn.execute(
        sa.text("SELECT id FROM admin_section_groups WHERE system_name = 'admin'")
    ).scalar_one_or_none()
    if existing_group is None:
        conn.execute(sa.text(
            "INSERT INTO admin_section_groups (id, system_name, name, sort_order, "
            "created_at, updated_at) VALUES (:id, 'admin', 'Administración', 0, now(), now())"
        ), {"id": admin_group_id})
        existing_group = admin_group_id

    existing_section = conn.execute(
        sa.text("SELECT id FROM admin_sections_l1 WHERE system_name = 'admin-sections'")
    ).scalar_one_or_none()
    if existing_section is None:
        conn.execute(sa.text(
            "INSERT INTO admin_sections_l1 (id, group_id, system_name, label, path, "
            "section_type, sort_order, origin, created_at, updated_at) VALUES "
            "(:id, :gid, 'admin-sections', 'Secciones del Admin', '/settings/sections', "
            "'table', 0, 'code', now(), now())"
        ), {"id": admin_section_id, "gid": existing_group})

    # 3. Bump de las secuencias grp_id_seq / s1_id_seq si el valor insertado a mano
    #    (grp-12 / s1-55) es mayor que el valor actual de la secuencia -- evita colisión
    #    si el operador crea un grupo/sección por API inmediatamente después del deploy
    conn.execute(sa.text("SELECT setval('grp_id_seq', 12, true)"))
    conn.execute(sa.text("SELECT setval('s1_id_seq', 55, true)"))
```

**Por qué el grupo/sección `admin` se siembra en la migración (una sola vez, determinista)
y NO en `sync_structure`/`init_db` como upsert recurrente:** es exactamente el patrón que
pide la corrección — "de aquí en adelante la BD es la única fuente de verdad". Si
`init_db()` reinsertara con upsert en cada arranque (como hacía antes para las 54
secciones), estaría pisando ediciones del operador sobre el propio grupo/sección `admin`
(p. ej. si Carlos le cambia el `label` a "Secciones del Admin" por otra cosa, un upsert de
código lo revertiría en el próximo restart — el mismo bug que motivó toda esta corrección,
ahora aplicado a un solo grupo en vez de 54 secciones). Por eso `init_db()` solo tiene la
salvaguarda de **alta si falta** (§4.1) —no upsert—, y la siembra determinista real (con
`label`/`path` "oficiales" la primera vez) vive en la migración, igual que el resto de la
estructura congelada de `c4d5e6f7a8b9`.

**IDs `grp-12` / `s1-55`:** siguientes libres tras los rangos congelados de
`c4d5e6f7a8b9` (`_FROZEN_GROUPS` = `grp-1..grp-11`; `_SEC_TO_S1` = `s1-1..s1-54`). Mismo
patrón "congelado a mano" que ya rige `sec-N`/`agent-N` (ADR-021/ADR-022): **verificar
contra el estado real de la BD al implementar** — si entre el diseño de este contrato y su
implementación se hubiera creado ya algún grupo/sección adicional por otra vía, ajustar el
siguiente entero libre en consecuencia.

### 5.2 `downgrade()`

```python
def downgrade() -> None:
    op.execute("DELETE FROM admin_sections_l1 WHERE system_name = 'admin-sections'")
    op.execute("DELETE FROM admin_section_groups WHERE system_name = 'admin'")
    op.drop_column("users", "is_superuser")
```

Best-effort: si el operador ya creó grupos/secciones propios por API (§1) dentro del árbol
`admin` desde el upgrade, el `downgrade` **no** los toca (no hay FK que fuerce cascada desde
`admin_sections_l1` hacia abajo salvo la ya existente `ON DELETE CASCADE`/`RESTRICT` normal
— un `DELETE` del grupo `admin` con secciones hijas fallaría por la FK `RESTRICT` de
`group_id`, igual que fallaría un `DELETE /admin/section-groups/{id}` por API, §1.2). Se
documenta como limitación conocida del downgrade, igual que el de `c4d5e6f7a8b9`.

### 5.3 Nota de deploy

Mismo procedimiento que ADR-019/ADR-021/ADR-023: la migración **no** corre en `init_db()`
(sigue usando `create_all`, ya no siembra grupos/secciones vía `sync_structure` de todas
formas). Requiere `alembic upgrade head` manual **inmediatamente después del rebuild**, en
el mismo paso de despliegue. Ventana de regresión: entre el arranque del código nuevo y la
migración, `ensure_admin_group_and_section` (§4, corre en cada `init_db`) ya crea el
grupo/sección `admin` con id no determinista (usa la secuencia normal, no `grp-12`/`s1-55`
fijos) si la migración todavía no corrió — **para evitar esa doble vía de creación con ids
distintos**, `ensure_admin_group_and_section` debe usar los **mismos IDs fijos**
`grp-12`/`s1-55` que la migración (no dejarlos a la secuencia) en su `INSERT`, y la
migración debe hacer su `INSERT` con `ON CONFLICT (system_name) DO NOTHING` (o el
`existing_group is None` check ya cubre esto por `system_name`, que es lo que realmente
evita el duplicado — el id fijo es solo para que ambos caminos, si llegan a competir,
converjan en el mismo valor). Recomendación operativa: encadenar `alembic upgrade head`
justo después del rebuild, igual que en ADR-019/021/023, para minimizar la ventana.

---

## 6. Resumen de archivos a tocar (para `api-rest-developer`)

**Fase 1 — modelo + migración:**
- `models/user.py` (+ `is_superuser`)
- `alembic/versions/<rev>_admin_sections_crud_is_superuser.py` (nuevo, §5)

**Fase 2 — schemas:**
- `schemas/admin_sections.py`: `+origin` en `SectionGroupItem`/`SectionListItem`;
  `SectionGroupCreateRequest`, `SectionCreateRequest`, `SectionMoveRequest`,
  `SectionMoveResponse` (nuevos); `SectionReparentRequest` → `SectionUpdateRequest`
  (renombrar + ampliar campos); `AdminViewUpdateRequest` (+3 campos owner).

**Fase 3 — servicio:**
- `services/section_catalog.py`: `create_group`, `delete_group`, `create_section`,
  `update_section` (ampliar con nuevos campos), `delete_section`, `move_section` (nuevo,
  algoritmo §1.6), `update_view` (+3 kwargs owner_*), `_is_admin_subtree` (helper de gate),
  `list_nav_tree`/`list_section_groups`/`list_sections`/`get_section` (+ filtro
  `is_superuser` cuando aplique).
- `services/admin_sections_seed.py`: dividir `sync_structure` en `sync_views` (recortada)
  + `ensure_admin_group_and_section` (nueva); retirar todo el bloque de upsert/prune de
  grupos y secciones L1.
- `database.py::init_db()`: reemplazar la llamada a `sync_structure` por
  `ensure_admin_group_and_section` + `sync_views` (§4).

**Fase 4 — rutas:**
- `routes/admin_sections.py`: `POST /section-groups`, `DELETE /section-groups/{id}`,
  `POST /sections`, `DELETE /sections/{sid}`, `POST /sections/{sid}/move`; ampliar `PUT
  /sections/{sid}` con los nuevos campos; dependency `require_superuser_for_admin_group`
  aplicada donde corresponda (§3.3); `GET /nav-tree` y demás lecturas de §1 reciben
  `current_user` para el filtro de superusuario.

**Fase 5 — tests** (cobertura ≥80% de lo nuevo, `qa-engineer` valida):
- Grupos: crear, `409` duplicado, borrar vacío `204`, borrar con hijas `409`, gate
  superusuario en el grupo `admin` (`403` no-superuser / `200`+`204` superuser, salvo
  borrado del grupo `admin` mismo → siempre `403`).
- Secciones: crear en cada nivel (`422` shape inválido), editar campos nuevos, borrar sin
  hijas/vistas `204`, borrar con hijas `409`, borrar con vistas `409`.
- Move: L1→L2 y L2→L3 exitoso (verificar nuevo id, `previous_id`, vistas reasignadas,
  `sort_order` al final de hermanas destino); `409` con hijas propias; `400` mismo nivel;
  `400` `target_parent_id` de nivel incorrecto; transacción atómica (simular fallo a mitad
  y verificar rollback completo — ni fila nueva, ni vieja borrada, ni vistas movidas).
- Vistas: `PUT /admin/views/{id}` con `owner_l2_id` mueve la vista; `400` destino
  inexistente; `409` `key` duplicado en destino; sin campos owner → no cambia owner
  (retrocompatibilidad).
- `is_superuser`: migración backfill `true` en filas existentes (test de migración, mismo
  patrón que `test_admin_sections_migration_map.py`); usuario nuevo nace `false`.
- `init_db()`: `ensure_admin_group_and_section` es idempotente (dos llamadas seguidas no
  duplican ni pisan ediciones); `sync_views` no recrea una sección borrada por el operador
  (solo loguea warning y sigue).

Después: `admin-panel-specialist` (formularios crear/editar/eliminar grupo y sección,
control de mover entre niveles en `AdminSectionsPage.tsx`, reasignación de owner en
`AdminViewsPage.tsx`, ocultar grupo `admin` en `Sidebar.tsx` para no-superuser, actualizar
copy de la pantalla). Luego `code-quality-guardian` + `qa-engineer` + `git-especialista`.

---

## 7. Fuera de alcance de esta corrección (follow-ups)

- **Mover un subárbol completo entre niveles** (una sección con hijas propias) — diferido,
  ver justificación en §1.6. Requiere decidir la semántica de re-anidado recursivo.
- **Catálogo de componentes UI** para crear vistas 100% desde el Admin (`data_source`/
  `resource_key`/`tool_names`/`origin` ya preparan el terreno, ADR-023 §Seguimiento (b)) —
  esta corrección solo abre la **reasignación de owner** de una vista existente, no la
  creación de vistas nuevas por API.
- **Rol granular más allá de `is_superuser` booleano** (p. ej. roles intermedios,
  permisos por grupo) — el ADR pide específicamente un gate binario para un único grupo
  protegido; cualquier sistema de roles más fino es un ADR aparte si el producto lo
  necesita más adelante.
- **UI de confirmación / doble-check para `DELETE` de grupos/secciones** — es
  responsabilidad de `admin-panel-specialist`, no de este contrato de API.

---

**Creado por**: Arquitecto de Soluciones (vía especialista `api-rest-specialist`)
**Basado en**: [ADR-023](023-admin-sections-hierarchy-views.md) §"Corrección — Grupos/Secciones
pasan a gestión 100% Admin (2026-08-28, post-QA en producción)"
**Referencia de formato**: [`023-contrato-implementacion.md`](023-contrato-implementacion.md)
(contrato original — algunas de sus reglas quedan revertidas aquí, ver §0)
**Fecha**: 2026-08-28
**Estado**: Diseño — pendiente de implementación por `api-rest-developer`. No se ha tocado
código de producción.
