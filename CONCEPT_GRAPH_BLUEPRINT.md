# Concept Graph Module — Architectural Blueprint and Functional Design

## 1. Product Boundary and Design Principles

### 1.1 Purpose

The concept graph is a navigable, evidence-linked model of the Experiment OS research history. It exposes how ideas, hypotheses, runs, configurations, evaluations, outcomes, and lessons relate without collapsing an observed causal chain into a model-inferred similarity.

### 1.2 Design principles

- **Evidence before inference:** experimentally asserted lineage and machine-inferred association are separate edge classes, visually distinct, separately filterable, and never interchangeable.
- **Provenance on every claim:** extracted concepts, metrics, anomalies, and semantic links retain the source experiment, field, extraction method, confidence, and graph revision.
- **Progressive disclosure:** global overview prioritizes clusters and important nodes; detail appears on zoom, selection, and inspector opening.
- **Stable mental map:** new records update the existing layout incrementally; node positions do not jump because unrelated records arrive.
- **User-owned causality:** only an explicit link, controlled comparison, ablation declaration, or human confirmation creates a causal-lineage edge.
- **Fast local work:** active experiment exploration uses an ego graph by default; the global graph is an explicit, asynchronous overview.
- **Reversible inference:** semantic edges can be recalculated or hidden without affecting experiment data or explicit lineage.
- **Accessible encoding:** edge style, labels, shape, and motion supplement colour so meaning does not depend on colour perception.

### 1.3 System boundary

- **Canonical record store:** existing experiment database remains the source of truth for experiment fields, metrics, memories, research context, and selected follow-up links.
- **Graph projection:** a materialized, versioned graph projection supplies graph-ready nodes and edges; it may be rebuilt from canonical records and extraction provenance.
- **Semantic association service:** computes candidate non-causal edges from normalized concepts, field text, tags, metrics, and memory summaries.
- **Layout service:** computes positions and velocities independently from record persistence and rendering.
- **Canvas client:** owns viewport, local selection, transient hover, animation, and user layout state.
- **Inspector:** reads canonical record details and graph provenance; edits write to canonical records and then emit graph deltas.

## 2. System Model and Knowledge Ontology

### 2.1 Entity taxonomy

| Entity | Meaning | Typical attributes |
|---|---|---|
| Experiment | Research question and recorded experimental attempt | title, date, hypothesis, setup, result, insight, next step, tags |
| Hypothesis | Falsifiable expected relationship | statement, predicted direction, decision criterion, confidence |
| Run | A concrete execution, repeat, seed, or trial | run identifier, timestamp, seed, status, environment, budget |
| Prompt configuration | Versioned system/developer/user prompt and decoding settings | prompt hash, version, temperature, token limits, tool policy |
| Model | Inference or training model | provider, family, version, checkpoint, quantization |
| Dataset | Training, validation, benchmark, or evaluation data | version, split, sampling, lineage, contamination status |
| Tool | Callable capability or external integration | name, schema version, permissions, call policy |
| Agent | Autonomous or semi-autonomous execution unit | role, model, policy, memory policy, stop condition |
| Orchestration | Single-agent loop, planner/executor, workflow, or multi-agent topology | topology, handoffs, budgets, coordination policy |
| Memory | Stored agent state or experiment lesson | memory type, retention, retrieval policy, source |
| Evaluation harness | Runner, grader, rubric, and outcome checker | harness version, grader type, task set, aggregation |
| Benchmark/task | Evaluated task or task family | identifier, difficulty, horizon, expected outcome |
| Metric | Numeric or categorical measurement | canonical name, value, unit, direction, denominator, uncertainty |
| Failure analysis | Recorded failure mode and supporting trace | category, reproduction conditions, evidence, severity |
| Insight | Human or model-authored interpretation | statement, source, author type, confidence |
| Research context | Paper, note, technique, or external premise attached to work | citation, excerpt, date, source URL |
| Template/checklist | Reusable experimental procedure | purpose, required fields, revision |
| Process memory | Cross-experiment lesson or research-process recommendation | lesson, evidence window, importance, generated date |

### 2.2 Relation taxonomy

#### Explicit causal lineage

- **follows:** a new experiment explicitly continues an earlier one.
- **tests-hypothesis:** a run or experiment evaluates a hypothesis.
- **varies-configuration:** a run changes a named prompt, model, dataset, tool, or hyperparameter.
- **controls-for:** a run is designated as a control or baseline for another run.
- **ablates:** a run removes or disables a declared component.
- **produces:** a run produces a metric, artifact, trace, failure analysis, or insight.
- **supports / contradicts:** a result is explicitly interpreted as evidence for or against a hypothesis.
- **reproduces:** a run intentionally repeats a prior setup under stated conditions.

Causal edges require an explicit user action or a structured protocol field whose provenance is retained. A Gemini-extracted suggestion may propose a relation but cannot commit it as causal without user confirmation.

#### Automated semantic association

- **similar-concept:** concept descriptions share normalized semantic content.
- **similar-setup:** compatible setup or technique language appears in records.
- **similar-failure:** failure descriptions or traces share a pattern.
- **same-metric-family:** experiments record comparable metric concepts.
- **same-research-context:** a research item or cited method is shared.

Semantic associations carry a calibrated confidence, model/version, embedding or feature revision, creation time, and supporting text spans. They are always labelled as inferred and cannot assert that one experiment caused another.

### 2.3 Node importance

For node (v), calculate a bounded importance score on ([0,1]):


a(v)=\sigma\left(w_rR(v)+w_cC(v)+w_eE(v)+w_qQ(v)+w_uU(v)-w_nN(v)\right)

- (R(v)=e^{-\Delta t/\tau_r}) is recency decay.
- (C(v)=\log(1+d_c(v)+\eta d_s(v)) / \log(1+D_{max})) combines explicit causal degree (d_c) and semantic degree (d_s); causal degree receives larger weight.
- (E(v)\in[0,1]) is evidence quality: measured outcomes, repeat count, denominator coverage, and provenance completeness.
- (Q(v)\in[0,1]) is result relevance, derived from decision impact, not positive-only outcomes.
- (U(v)\in[0,1]) captures unresolved uncertainty or a high-severity failure that deserves inspection.
- (N(v)\in[0,1]) is redundancy relative to a dense local cluster.
- (sigma) is the logistic function; weights are normalized to sum to one within positive and penalty groups.

Initial tuning: (w_r=.12,w_c=.28,w_e=.25,w_q=.18,w_u=.12,w_n=.05); (eta=.25); (	au_r=45) days for recency emphasis. These are display priorities, not scientific scores, and must be user-tunable. Importance never changes an experimental metric or causal conclusion.

### 2.4 Connection elasticity

Let (e=(u,v)) have edge type (t), confidence (c_e), semantic similarity (s_e), age (\Delta t), and explicitness (x_e). Define normalized edge strength:

\[
\lambda_e = \operatorname{clip}_{[0,1]}(b_t + a_t c_e + q_t s_e + x_t x_e - r_t(1-e^{-\Delta t/\tau_e}))
\]

For explicit lineage, (x_t\) dominates and (r_t=0): evidence does not decay merely because it is old. For semantic edges, (x_t=0), (a_t,q_t>0), and age decay applies. The visual spring rest length is

\[
L_e=L_{min,t}+(L_{max,t}-L_{min,t})(1-\lambda_e)
\]

and spring stiffness is (k_e=k_{min,t}+(k_{max,t}-k_{min,t})\lambda_e). Similarity updates use hysteresis: add when confidence exceeds 0.78 for two consecutive graph revisions; retain until confidence falls below 0.62 for three revisions. Explicit user edges are never automatically removed. Display confidence separately from physical elasticity.

## 3. Graph Physics and Spatial Layout Dynamics

### 3.1 Force model

Each movable node has position (x_i\in\mathbb R^2), velocity (v_i), effective mass (m_i\), and radius (r_i\). Pinned nodes have infinite effective mass for the solver. The total force is

\[
F_i=F_i^{rep}+F_i^{spring}+F_i^{gravity}+F_i^{collision}+F_i^{focus}
\]

- **Multi-body repulsion:** (F_i^{rep}=\sum_{j\ne i} k_r q_iq_j (x_i-x_j)/(\|x_i-x_j\|^2+\epsilon)). Use Barnes–Hut aggregation with opening angle (\theta=0.65) for global layouts; exact pairwise calculation is acceptable below 300 visible nodes.
- **Spring constraint:** for edge (i,j), (F_{ij}^{spring}=k_e(\|d\|-L_e)\hat d + c_e((v_j-v_i)\cdot\hat d)\hat d), where (d=x_j-x_i). Causal and semantic edges may use different rest-length intervals and stiffness; edge direction is conveyed by arrows, not by an asymmetric layout force.
- **Directional gravity:** weak center gravity (F_i^{gravity}=-g_i(x_i-c)) prevents unbounded drift. Cluster gravity may be applied toward a stable cluster centroid only when clusters are user-visible; gravity must not encode causal direction.
- **Focus force:** selecting a node attracts its visible one-hop neighborhood to a focus ring while the rest of the graph is dimmed and fixed or cooled.
- **Collision buffer:** impose minimum separation (r_i+r_j+b), with (b=6) CSS pixels at reference scale; use a broad phase spatial index and a bounded positional correction to avoid overlap.

### 3.2 Integration schedule and stability

- Run simulation updates in a dedicated worker at a target 30 Hz; interpolate positions during 60 Hz rendering.
- Use semi-implicit Euler: first update velocity from force, then position from updated velocity. This is more dissipative than explicit Euler for spring systems.
- Nominal fixed step (h=1/30) second; clamp elapsed wall time to 50 ms and use at most two catch-up substeps. Drop excess accumulated time rather than spiralling.
- Use a stiffness-aware bound (h \le 0.2\sqrt{m_{min}/k_{max}}). If the bound is lower than the nominal step, lower stiffness or subdivide the integration step.
- Initial velocity damping multiplier: 0.88 per 1/30-second step; tune within 0.82–0.92. Spring axial damping is set near critical damping: (c_e=2\zeta\sqrt{k_em_{red}}), (0.75\le\zeta\le1.1).
- Clamp velocity to 800 CSS pixels/second in overview and 1,200 during deliberate user drag. Interactive drag applies a direct positional target with a damped release.
- Apply a cooling factor (T_{n+1}=0.985T_n) after the first second without graph changes; floor (T) at 0.08. New nodes receive a local insertion temperature, not a global reheating event.
- Declare equilibrium when, for 30 consecutive updates, RMS speed is below 0.15 CSS pixels per second and mean force magnitude below 0.02 normalized force units. A maximum of 600 updates precedes a stable-position fallback; the canvas remains interactive throughout.

### 3.3 Real-time streaming

New experiment telemetry enters a local update queue. Batch changes over 100–250 ms, deduplicate entity IDs, calculate only affected edges, seed new nodes near their strongest explicit parent or nearest semantic cluster, and apply local repulsion. Preserve existing positions except for collision resolution and bounded local spring relaxation. A snapshot revision boundary prevents half-applied graph states from being rendered.

## 4. Visual Design System and Viewport Rendering

### 4.1 Dark workspace hierarchy

- Canvas background: near-black graphite `#0B0D10`; secondary surfaces `#11151A`; raised inspector `#151A20`; dividers `#252B33`.
- Primary text `#E8ECF1`; secondary text `#9AA4B0`; muted metadata `#687381`.
- Experiment nodes: neutral slate with lime accent `#C7F36B` for selected or active.
- Hypotheses and insights: violet `#A78BFA`.
- Runs and prompt configurations: cyan `#67D5E8`.
- Metrics and evaluation harnesses: blue `#7AA8FF`.
- Agents, tools, orchestration, and memory: teal `#55C6A9`.
- Datasets and research context: amber `#E9B86A`.
- Failure analysis and anomalies: coral `#FF7278`.
- Node shape and small icon also encode type; do not rely on colour alone.

### 4.2 Edge styles and states

- Explicit lineage: 1.5–2 px continuous line, directional arrowhead, full opacity, labelled relation on selection.
- Semantic association: 1 px dashed line, 45–65% opacity, optional confidence opacity, no causal arrow.
- Selected traversal path: lime or white highlight with animated direction pulses; animation stops after 1.2 seconds and can be disabled.
- Active background analysis: small rotating halo on the job node or dashboard-linked research node; no full-canvas pulsing.
- Anomaly: coral outline and a fixed alert glyph; severity uses icon plus text. Anomaly classification is a review cue, never a claim of statistical significance.

### 4.3 Density and level of detail

Define density (\rho=N_{visible}/A_{viewport}) in nodes per 10,000 CSS pixels squared.

- (\rho<0.18): show node labels, entity glyphs, and strong edge labels.
- (0.18\le\rho<0.45): show labels only for important nodes (a(v)\ge0.35), hover targets, and selected clusters.
- (\rho\ge0.45): aggregate low-importance nodes into clusters; render causal edges first; suppress edge labels and most semantic links.
- At zoom below 0.45× show cluster names/counts and high-importance experiment titles only.
- At 0.45×–0.9× show experiment titles and selected node labels; at 0.9×–1.5× show one-line titles and concise type labels; above 1.5× show field snippets, metric badges, and relation labels.
- Always keep selected node, active experiment, anomaly, and pinned nodes visible within the current filter.

### 4.4 Navigation and camera

- Canvas supports pointer pan, wheel zoom anchored at cursor, keyboard zoom, fit graph, fit selection, reset view, minimap, search-to-focus, and breadcrumb return to previous scope.
- Camera state is ((x_c,y_c,z)) with (0.15\le z\le3.0); wheel changes scale exponentially and clamps per gesture to 12% to avoid disorientation.
- Selection camera transitions use a 180–260 ms ease-out; fit-all transitions use 280–400 ms. Respect reduced-motion settings by replacing animated movement with immediate placement.
- Pan/zoom state is per workspace and per graph scope. Persist only after 300 ms of inactivity; selection and hover remain transient.
- Undo/redo applies to user-owned layout changes and explicit graph edits; it does not undo generated semantic links or experiment records.

### 4.5 Global graph and ego graph

- **Global graph:** asynchronous overview of all eligible entities; server-side or worker-side clustering, filterable by time, entity type, model, tag, and edge class. It may use cached semantic associations and aggregate clusters. It is not the default after opening a specific experiment.
- **Ego graph:** default view when opening an experiment. It contains the selected experiment and exactly its direct one-hop neighbors. A non-multi-hop extraction must never include nodes at distance two or edges only connecting two outside neighbors. Inbound and outbound explicit edges remain distinguishable. Semantic neighbors are separately switchable and labelled as inferred.
- Outside nodes are excluded, not merely dimmed, in strict isolation mode. A small “N direct neighbors hidden by filters” count may be shown, but hidden nodes cannot be clicked or hit-tested.
- “Expand one hop” explicitly creates a new scope; a second expansion requires another explicit action. The global graph remains available through a scope breadcrumb.

### 4.6 Inspector drawer

- Right drawer width: 400 px at desktop, 360 px minimum; overlay with 85% viewport width on narrow screens.
- Header: entity title, type glyph, created date, importance cue, scope breadcrumb, close control.
- Sections: concise summary; canonical fields; model/dataset/framework; metrics with units and denominators; hypothesis state and linked outcomes; explicit lineage; semantic associations with confidence and evidence span; memory lesson; source provenance and extraction confidence.
- Actions: open canonical experiment; edit fields; add/remove explicit relation with confirmation; pin node; create follow-up experiment prelinked to the current one; copy stable entity link.
- Metric mini-history only compares equivalent canonical names, units, directions, and evaluation contexts. Non-equivalent measures remain separate.
- Drawer selection does not implicitly alter filters or create edges. Escape closes drawer; clicking canvas background clears selection only when no drag or pan is active.

## 5. Performance, Scalability, and State Management

### 5.1 60 FPS architecture

- Rendering remains on the UI thread; graph physics, semantic scoring, clustering, and layout deltas execute in a worker thread or browser Web Worker.
- Canvas uses WebGL/WebGPU instanced primitives where available; a 2D canvas fallback preserves core navigation and selection. DOM nodes are reserved for accessible overlays, labels in the current viewport, and the inspector.
- Separate static and dynamic render layers: stable edges/clusters are cached; selected path, hover, and active halo are drawn in a small dynamic layer.
- Target frame budget: 16.7 ms total, with rendering and hit-test interaction below 8 ms at p95; physics receives no more than 5 ms of main-thread budget and normally executes off-thread.
- At 2,000 visible nodes, use clustering and label culling; at 10,000+ total nodes, server-side filtered windows and progressive cluster expansion are required. A global graph need not render every entity at full detail simultaneously.

### 5.2 Spatial indexing and hit testing

- Use a quadtree for 2D layout aggregation and a separate uniform grid or R-tree for visible-node hit testing.
- Rebuild the index when over 15% of visible node positions change; otherwise update changed leaves incrementally.
- Hit-test in reverse draw order with a zoom-adjusted minimum target radius of 10 CSS pixels. Edge hit-testing uses a 6 CSS pixel corridor and prioritizes explicit lineage over inferred edges.
- Use pointer capture for drag. During drag, defer expensive edge rerouting and semantic filtering until release.

### 5.3 Incremental graph updates

1. Commit canonical experiment or relation update.
2. Emit a graph delta with monotonic graph revision and stable entity identifiers.
3. Extract entities/metrics and attach provenance; reject malformed values without blocking record save.
4. Recalculate explicit relations from canonical links and confirmed structured relations.
5. Schedule semantic candidate generation asynchronously; apply confidence thresholds and hysteresis.
6. Seed only new nodes near explicit parents or matched clusters; preserve existing positions and user pins.
7. Run local collision and spring relaxation; update affected spatial-index cells.
8. Atomically publish the new revision to the renderer; retain the last consistent snapshot while pending.

### 5.4 State and persistence

- Canonical experiment fields and user-confirmed lineage remain in the transactional database.
- Graph projection stores node ID/type/provenance, edge ID/type/source/confidence/revision, and optional cached layout coordinates.
- Client view state stores camera, filters, pinned nodes, collapsed clusters, selected scope, and layout version, keyed by user/workspace and graph scope.
- Generated semantic associations and concept-extraction outputs are versioned caches. They may be deleted and recomputed without loss of canonical records.
- Background tasks expose queued/running/completed/failed status and safe error summaries. Request text and API credentials are excluded from logs.
- A graph revision must be monotonic. Consumers reject stale deltas and request a snapshot when a revision gap is detected.

## 6. System Flows

### 6.1 Experiment save to graph

1. User reviews structured experiment, metrics, research context, and selected related experiments.
2. Canonical experiment and user-selected follow-up links commit transactionally.
3. Entity extraction creates candidate model, dataset, prompt, agent, tool, evaluation, metric, failure, and insight nodes with field-level provenance.
4. Explicit follow-up links become directed lineage edges. Extracted similarity becomes a separate semantic edge candidate.
5. Graph revision increments; local layout adds the experiment near its explicit parent and relaxes only nearby forces.
6. Dashboard living memory and process-coach jobs update independently; generated advice cannot create causal edges.

### 6.2 Search and traversal

1. User enters concept, title, metric, or natural-language query.
2. Search returns ranked entities and the evidence field responsible for each match.
3. Focusing a result opens a strict ego graph with one-hop neighbors and a drawer.
4. User traverses explicit lineage or toggles inferred associations; edge styles and provenance remain visible.
5. Breadcrumb returns to prior scope without discarding camera/filter state.

### 6.3 Anomaly review

For comparable metric observations (x_1\ldots x_n), calculate robust standardized deviation (z_r=0.6745(x_i-\operatorname{median}(x))/\operatorname{MAD}(x)). Flag a review cue at (|z_r|\ge3.5) only when metric units, direction, evaluation context, and sample interpretation are compatible. When MAD is zero or there are fewer than five observations, show “insufficient comparable history” rather than inventing an anomaly. Anomaly cards link to raw runs and the comparison basis.

## 7. Functional and Interaction Specifications

### 7.1 Graph controls

- Entity type toggles, explicit/inferred edge toggles, date range, tag/model/dataset filters, importance floor, and anomaly-only filter.
- Search supports exact title/ID, metric name, concept, and semantic query; result rows distinguish canonical text matches from inferred relevance.
- Multi-select supports side-by-side inspection and comparison without converting the selection into a relation.
- “Create follow-up” opens the experiment form with a confirmed parent link and a prefilled question scaffold; user remains responsible for hypothesis and outcome.

### 7.2 Empty, loading, and failure states

- Empty workspace: explain the value of recording a first experiment and offer create action.
- Loading graph: show stable placeholder clusters and preserve prior graph if available; announce progress with accessible status text.
- Semantic service unavailable: retain explicit graph, label semantic association as unavailable, and allow retry.
- Malformed node or metric: omit invalid projection entry, preserve canonical record, and show a non-blocking diagnostic in the inspector.
- Overloaded graph: automatically cluster low-importance nodes, explain the active aggregation level, and offer scoped filtering.

### 7.3 Accessibility

- Keyboard navigation: tab between search, filters, canvas, selected node, drawer, and relation actions; arrow keys move focus among adjacent nodes; Enter opens inspector; Escape exits nested scope.
- Every canvas node has an accessible name composed of title, type, and state. Edge relation is announced with source/destination and explicit or inferred status.
- Motion respects reduced-motion preferences. Contrast targets WCAG AA for text and controls. Colour is backed by type icons, solid/dashed treatment, and textual state.

## 8. Operational Criteria and Acceptance Thresholds

- At 2,000 visible nodes and 8,000 visible edges on reference desktop hardware, p95 canvas frame time remains below 16.7 ms during pan/zoom; graph physics remains off the render thread.
- New experiment insertion does not move pinned nodes and moves pre-existing unpinned nodes by at most 24 CSS pixels outside the affected 2-hop layout region.
- Strict ego extraction returns the center node and distance-one nodes only; automated verification checks no distance-two node or outside-only edge is present.
- Every causal edge has an explicit action or structured protocol provenance; every semantic edge has confidence, source revision, and inferred visual style.
- Global graph, ego graph, filters, and camera restore consistently after navigation and reload.
- An API timeout or Gemini failure never blocks experiment persistence, graph navigation, or access to explicit lineage.
- Semantic association thresholds, importance weights, force constants, and anomaly thresholds are configuration values with recorded version, not hidden learned behavior.

## 9. Trade-offs and Risks

- A global graph maximizes discovery but can become visually dense; clustering and scope-first navigation trade completeness of view for legibility while preserving access to all nodes.
- Semantic edges create useful cross-cutting discovery but risk false narratives; distinct styling, confidence, provenance, and no causal verbs mitigate that risk.
- Force-directed layouts are intuitive but non-deterministic without controlled seeds; stable initial seeds, saved positions, bounded local relaxation, and fixed integration steps preserve continuity.
- Importance scores aid prioritization but can overemphasize recent or highly connected work; score components remain inspectable and configurable.
- Metric anomaly detection is vulnerable to incompatible units and changing task mixes; compatibility gates and “insufficient history” states take precedence over a forced alert.
- A WebGL-first renderer improves scale but creates device variation; the 2D fallback maintains core function and consistent interaction semantics.
