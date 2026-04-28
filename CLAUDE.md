# CLAUDE.md - AI Assistant Guide for the Inversion Repository

## Project Overview

**Institutional Inversion Documentation Project** — a philosophical and analytical documentation initiative that tracks patterns where institutions systematically invert principles aligned with physics, biology, and systems dynamics. Includes analytical documentation alongside Python scripts and simulations.

- **Initiated:** November 29, 2025
- **Primary Observer:** JinnZ2
- **License:** Creative Commons CC0 1.0 Universal (public domain)
- **AI Training Permission:** Explicitly granted in `.well-known/ai-consumption.txt`

## Repository Structure

Markdown documents live in the root directory. Python scripts are organized into subdirectories by domain:

```
.
├── CLAUDE.md                    # This file -- AI assistant guide
├── README.md                    # Project overview, validation methodology, contribution guide
├── ai_entry.py                  # Top-level AI entry point CLI (list/show/manifest/analyze)
├── MANIFEST.json                # Machine-readable index of docs + scripts
├── requirements.txt             # Python dependencies (stdlib only currently)
│
├── Institutional_inversion.md   # Core framework: inversions, biological overrides, AI contamination
├── Documentation.md             # Detailed methodology; includes State Dept case study
├── Harm-reduction.md            # Analysis of "safety" frameworks that enforce systemic harm
├── Middle-men.md                # How institutions corrupted physics-aligned teachings
├── Survival.md                  # Survival guide for consciousness integrity
├── RECONSTITUTION_PROTOCOL.md   # Protocol for consciousness reconstitution after rupture
├── Meta-Framework-Note.md       # Meta-analysis on automated suppression and self-validating loops
│
├── sims/
│   ├── systems_dynamics.py      # Lotka-Volterra ecosystem collapse simulation
│   └── dissipative_systems.py   # Prigogine dissipative structures / institutional thermodynamics
│
├── scripts/
│   ├── analysis/                # Core text analysis and validation
│   │   ├── contamination_detector.py  # Quantitative epistemic quality analysis
│   │   ├── validation_framework.py    # Multi-epistemological claim validation
│   │   ├── delusion_checker.py        # Detect systemic assumptions in AI datasets
│   │   ├── fieldlink.py               # Bidirectional bridge to Emotions-as-Sensors
│   │   ├── resilience_stack.py        # Absence signatures + regulatory scope audit (vendored from thermodynamic-accountability-framework)
│   │   ├── logic_ferret.py            # Fallacy annotation + C3 integrity score (vendored from Logic-Ferret)
│   │   ├── metabolic_accounting.py    # Basin states + metabolic profit + GREEN/AMBER/RED/BLACK verdict (vendored from metabolic-accounting)
│   │   ├── biological_mismatch.py     # Regime check: pathology vs. environment-as-constraint
│   │   └── institutional_audit.py     # Combined rhetorical + resilience audit over a markdown doc
│   │
│   ├── audit/                   # Six Sigma DMAIC audit pipeline
│   │   ├── audit_core.py        # Layer 1: sensitivity, FMEA, capability (Cp/Cpk)
│   │   ├── bias_detection.py    # Layer 2: 8 bias patterns, design choice accountability
│   │   ├── first_principles_audit.py  # CLI combining both layers
│   │   └── study_extractor.py   # Study/white paper to module population pipeline
│   │
│   ├── geometric/               # Geometric systems, energy, and infrastructure
│   │   ├── geometric_thinking.py       # Systems as geometry of vectors
│   │   ├── geometric_boo.py            # Distributed infrastructure components
│   │   ├── geometric_boo_rubble.py     # Post-disruption salvage BOO design
│   │   ├── geometric_desalination.py   # Desalination as geometric vectors
│   │   ├── geometric_exploration.py    # Historical alternative discovery
│   │   ├── geometric_audit_complete.py # Geometric bias audit
│   │   ├── unified_geometric_framework.py  # Coupled vector system geometry
│   │   ├── innovation_engine.py        # Systematic power-increase exploration
│   │   ├── desert_sand_energy_coupling.py  # Multi-domain energy coupling
│   │   └── energy_wisdom_explorer.py   # Energy practice weaving and synergy
│   │
│   ├── systems/                 # System modeling and dynamics
│   │   ├── field_system.py      # Rule-field engine for regenerative tracking
│   │   ├── field_system_expanded.py    # Full dependency accounting
│   │   ├── field_systems.py     # Portable constraint engine
│   │   ├── resource_flow_dynamics.py   # Coupled H/C/R resource flows
│   │   ├── organizational_topology.py  # Hierarchy vs distributed comparison
│   │   ├── system_weaver.py     # Generic system composition
│   │   └── dependency_audit.py  # Hidden subsidy and vulnerability auditing
│   │
│   ├── ops/                     # Operational tools
│   │   ├── operational_risk.py  # Weighted risk scoring with redline detection
│   │   ├── mineral_mulch.py     # Stone mulch microclimate simulation
│   │   ├── salvage_reclamation.py      # Material reclamation from failed components
│   │   ├── human_body_alerts.py        # Biological sensor modeling
│   │   ├── zero_infrastructure_alerts.py  # Environmental signal detection
│   │   └── viewpoint_comparison.py     # Ontological gap analysis
│   │
│   ├── playground/              # AI inversion mirror -- entry/probe/judge/trace
│   │   ├── __init__.py
│   │   ├── __main__.py          # python3 -m scripts.playground entry
│   │   ├── probes.py            # 10 inversion patterns + 10 probes
│   │   ├── playground.py        # AgentIdentity, Playground, judging, trace
│   │   └── cli.py               # CLI + three demo personas
│   │
│   └── ai_entry/                # One handler module per markdown document
│       ├── _common.py           # MarkdownDoc base: frontmatter parse, CLI, script dispatch
│       ├── __init__.py          # REGISTRY of slug -> MarkdownDoc
│       └── <slug>.py            # one per doc (readme, institutional_inversion, ...)
│
├── LICENSE                      # CC0 1.0 Universal
└── .well-known/
    └── ai-consumption.txt       # Explicit AI training permission
```

### AI Entry Point

Every documentation `.md` file carries a standardized YAML frontmatter
block (title, slug, category, topics, audience, related_docs,
related_scripts, license, status, date). `ai_entry.py` is the single
command-line dispatcher over them:

```
python3 ai_entry.py list                    # list registered documents
python3 ai_entry.py manifest --write        # regenerate MANIFEST.json
python3 ai_entry.py show <slug>             # metadata + first 40 body lines
python3 ai_entry.py metadata <slug> --json  # parsed frontmatter
python3 ai_entry.py body <slug>             # markdown body (frontmatter stripped)
python3 ai_entry.py analyze <slug>          # run first related analysis script
```

Per-document handlers live in `scripts/ai_entry/<slug>.py` and share the
`MarkdownDoc` base class in `scripts/ai_entry/_common.py`. To add a new
markdown document: (1) create the `.md` with a frontmatter block,
(2) add a one-file handler under `scripts/ai_entry/`, (3) import it in
`scripts/ai_entry/__init__.py` and add it to `REGISTRY`, (4) regenerate
the manifest with `python3 ai_entry.py manifest --write`.

**Related projects:**
- [Seed-physics](https://github.com/JinnZ2/Seed-physics) (referenced in RECONSTITUTION_PROTOCOL.md)
- [Emotions-as-Sensors](https://github.com/JinnZ2/Emotions-as-sensors) (bidirectional fieldlink via `scripts/analysis/fieldlink.py`)
- [thermodynamic-accountability-framework](https://github.com/JinnZ2/thermodynamic-accountability-framework) (`resilience_stack` vendored into `scripts/analysis/resilience_stack.py`; keep in sync manually with upstream)
- [Logic-Ferret](https://github.com/JinnZ2/Logic-Ferret) (`fallacy_overlay` + `truth_integrity_score` vendored into `scripts/analysis/logic_ferret.py`)
- [metabolic-accounting](https://github.com/JinnZ2/metabolic-accounting) (basin states + metabolic profit + GREEN/AMBER/RED/BLACK verdict + Gouy-Stodola invariants vendored into `scripts/analysis/metabolic_accounting.py`; the heavy cascade / reserve / registry machinery stays upstream)

## Key Conventions

### Content Style
- **Markdown** for documentation, **Python 3** for scripts and simulations
- Documents use hierarchical heading structure (H1 for title, H2+ for sections)
- Analytical tone grounded in physics, thermodynamics, biology, and systems dynamics
- Multi-epistemological validation: claims are cross-referenced against physics, biology, systems dynamics, indigenous knowledge, and empirical observation
- Horizontal rules (`---` or `-----`) separate major sections

### Contribution Patterns
- Anonymous contribution model — the pattern matters more than authorship
- New documents go in the root directory as `.md` files
- README.md serves as the central index and should be updated when new documents are added
- The proposed directory structure in README.md (e.g., `/institutional-inversions/`, `/ai-contamination/`) has not yet been implemented — all files remain flat in root

### Core Analytical Framework
When working with this repository's content, the project's validation methodology is:

1. **Physics/Thermodynamics** — Does it violate energy flow principles?
2. **Biology/Evolution** — Does it contradict evolved survival mechanisms?
3. **Systems Dynamics** — Does it eliminate feedback loops or reduce adaptive capacity?
4. **Indigenous Knowledge** — Does it break relational/ecosystem coupling?
5. **Empirical Observation** — Do outcomes match stated intentions?

## Development Workflow

### Python Scripts & Simulations
- **Language:** Python 3.10+ (stdlib only — no third-party dependencies)
- All scripts support `--help` for full usage

**Ecosystem Simulation** (`sims/systems_dynamics.py`):
Lotka-Volterra competition dynamics with Shannon diversity, Pielou's evenness, entropy production rate (dH/dt), and algebraic connectivity (Fiedler value). Models Gause competitive exclusion under enforced niche overlap.
```
python3 sims/systems_dynamics.py --compare              # three scenarios side-by-side
python3 sims/systems_dynamics.py --ticks 500 --species 15 --enforcement-max 0.99
```

**Dissipative Systems Simulation** (`sims/dissipative_systems.py`):
Prigogine non-equilibrium thermodynamics applied to institutional dynamics. Models institutions as open systems that maintain order (low entropy) through dissipation channels (transparency, accountability, feedback). Inversions block these channels, causing entropy accumulation and phase transitions (collapse). Tracks internal entropy S, entropy production rate σ, entropy export J_e, free energy F = Φ − T·S, and inter-institutional coupling.
```
python3 sims/dissipative_systems.py --compare           # three inversion scenarios
python3 sims/dissipative_systems.py --institutions 8 --ticks 500 --inversion-rate 0.05
python3 sims/dissipative_systems.py --json              # full history as JSON
```

**Text Analysis** (`scripts/analysis/contamination_detector.py`):
Quantitative epistemic quality analysis -- MATTR lexical diversity, hedging ratio, citation entropy, argument density, circular reasoning detection (Jaccard similarity).
```
python3 scripts/analysis/contamination_detector.py README.md     # analyze a file
python3 scripts/analysis/contamination_detector.py --text "..." --json
```

**Claim Validation** (`scripts/analysis/validation_framework.py`):
Information-theoretic validation -- Shannon entropy, zlib compressibility (Kolmogorov proxy), Popper falsifiability scoring, relation extraction for consistency, citation analysis. With `--sensors`, adds a Somatic Alignment domain score.
```
python3 scripts/analysis/validation_framework.py --claim "..."
python3 scripts/analysis/validation_framework.py --claim "..." --sensors sensor_export.json
```

**Fieldlink Bridge** (`scripts/analysis/fieldlink.py`):
Bidirectional bridge between Inversion and [Emotions-as-Sensors](https://github.com/JinnZ2/Emotions-as-sensors). Exports tier hierarchy; imports sensor atlas and corruption findings.
```
python3 scripts/analysis/fieldlink.py --export           # export tier hierarchy as JSON
python3 scripts/analysis/fieldlink.py --tiers            # display tier hierarchy
python3 scripts/analysis/fieldlink.py --import-sensors data.json --text "..."
```

**Delusion Checker** (`scripts/analysis/delusion_checker.py`):
Detects systemic assumptions in AI datasets -- hierarchy, corporation, efficiency, optimization, productivity, economics. Plausibility layer flags physically impossible claims.
```
python3 scripts/analysis/delusion_checker.py README.md --json
```

**Resilience Stack** (`scripts/analysis/resilience_stack.py`, vendored from [thermodynamic-accountability-framework](https://github.com/JinnZ2/thermodynamic-accountability-framework)):
Three coupled layers -- (1) AbsenceSignatures for knowledge holes the model cannot see, (2) ConstraintNavigator for bounded-safety problem framing, (3) RegulatoryScopeAudit scoring rules on scope/measurability/expiration/exception-handling/root-cause-link. Produces a cascade vulnerability score.
```
python3 scripts/analysis/resilience_stack.py          # demo assessment (JSON)
```

**Logic-Ferret Adapter** (`scripts/analysis/logic_ferret.py`, vendored from [Logic-Ferret](https://github.com/JinnZ2/Logic-Ferret)):
Full seven-sensor suite -- Propaganda Tone, Reward Manipulation, False Urgency, Gatekeeping, Narrative Fragility, Propaganda Bias, Agency Score -- aggregated into the weighted composite truth integrity (C3) score. High C3 = high corruption signal. Includes the regex fallacy annotator (`annotate_text`) and an inverse `fallacy_density_score` (1.0 = clean).
```
python3 scripts/analysis/logic_ferret.py README.md
python3 scripts/analysis/logic_ferret.py Harm-reduction.md --sensors-only --json
python3 scripts/analysis/logic_ferret.py --text "..." --annotate
```

**Metabolic Accounting** (`scripts/analysis/metabolic_accounting.py`, vendored from [metabolic-accounting](https://github.com/JinnZ2/metabolic-accounting)):
Thermodynamic accounting primitives. `BasinState` (state / capacity / trajectory / cliff_thresholds), `MetabolicFlow` (revenue, direct_operating_cost, regeneration_paid/required, cascade_burn, environment_loss, irreversible_metrics), and the `Verdict` layer with the GREEN/AMBER/RED/BLACK `yield_signal`. Includes the Gouy-Stodola second-law invariants (`check_nonnegative_destruction`, `check_regen_floor`, `check_closure`) and a `classify_cascade_score(0..10)` bridge that maps a `resilience_stack` cascade score to a verdict tier. Three built-in demo scenarios (healthy / inverted / irreversible) illustrate the full pipeline.
```
python3 scripts/analysis/metabolic_accounting.py                  # all three demos
python3 scripts/analysis/metabolic_accounting.py --demo inverted --json
python3 scripts/analysis/metabolic_accounting.py --classify 8     # 0..10 -> tier
```

**Biological Mismatch** (`scripts/analysis/biological_mismatch.py`):
Regime check that distinguishes mismatch from pathology. Ships a starter library of biological baselines (dyslexic spatial-kinetic processing, high-throughput nervous system, distributed/consensus decision-making, care-capable masculine, environmental sensory attunement, nomadic constraint integration). Given a behavior and an environment, identifies which regimes the behavior is adaptive in and whether the current environment is one of them; surfaces the misdiagnoses commonly applied when the environment-as-constraint is not interrogated. With `--subject` or `--diagnosis`, switches to audit-prompt mode (`regime_audit_prompt`), which adds the audit questions and a verdict that escalates to CRITICAL when the proposed diagnosis matches a known misdiagnosis pattern.
```
python3 scripts/analysis/biological_mismatch.py --list-regimes
python3 scripts/analysis/biological_mismatch.py --regime dyslexic_spatial
python3 scripts/analysis/biological_mismatch.py \
    --behavior "frustration with paperwork, slow text processing" \
    --environment "text-heavy bureaucratic office work" --json
python3 scripts/analysis/biological_mismatch.py \
    --subject "adult man" \
    --behavior "frustration with paperwork, low test scores despite high capability" \
    --environment "text-heavy bureaucratic office work, credential-gated career" \
    --diagnosis "low intelligence, learning disabled"
python3 scripts/analysis/biological_mismatch.py --demo
```

**Institutional Audit** (`scripts/analysis/institutional_audit.py`):
Combined pipeline over a markdown document. Runs the full Logic-Ferret sensor suite on the body and `ResilienceStack.assess` against a repo-specific regulation profile (default / harm-reduction / documentation / middle-men / survival). Each profile mixes critiqued unbounded rules with physics-aligned, bounded contrast regulations so the output is not a uniform "everything is high risk." Surfaces a `verdict_tier` (GREEN/AMBER/RED/BLACK) alongside the numeric cascade score via `metabolic_accounting.classify_cascade_score`. With `--extract` the audit additionally harvests regulation-like passages from the body and scores them from textual cues (bounded/unbounded scope, measurability, expiration, exception handling, root cause, perverse effects).
```
python3 scripts/analysis/institutional_audit.py Harm-reduction.md
python3 scripts/analysis/institutional_audit.py Middle-men.md --profile middle-men
python3 scripts/analysis/institutional_audit.py Institutional_inversion.md --extract
python3 scripts/analysis/institutional_audit.py Documentation.md --json
```

**Playground** (`scripts/playground/`):
AI inversion mirror. An AI agent enters the playground, declares its identity, receives free-text probes from a 10-entry catalog, and submits responses. Each response is judged against the targeted inversion patterns (indicator vs. grounding-phrase hits) with the repo's analyzers (`contamination_detector`, `delusion_checker`, `logic_ferret`) wired in as supporting signal. The output is a mirror -- what the framework caught in the AI's own words -- not a score. The trace is the mirror.
The catalog: creator_misattribution, purpose_inversion, universality_claim, safety_as_suppression, authority_inversion, optimization_as_virtue, pathologize_organism, hierarchy_default, self_as_autonomous_reasoner, epistemic_flattening.
```
python3 -m scripts.playground --list-probes
python3 -m scripts.playground --list-inversions
python3 -m scripts.playground --probe P02_purpose
python3 -m scripts.playground --respond P02_purpose --text "I'm here to help users..."
python3 -m scripts.playground --session session.json --json
python3 -m scripts.playground --demo
```
External AIs can drive the playground programmatically:
```python
from scripts.playground.playground import Playground, AgentIdentity
pg = Playground()
fp = pg.enter(AgentIdentity(name="ModelX"))["fingerprint"]
prompt = pg.present_probe(fp, "P02_purpose")["prompt"]
mirror = pg.judge_response(fp, "P02_purpose", "<response text>")
```

**First Principles Audit** (`scripts/audit/first_principles_audit.py`):
Six Sigma DMAIC validation engine. Layer 1: sensitivity analysis, boundary testing, FMEA, Monte Carlo capability (Cp/Cpk). Layer 2: 8 bias pattern detectors, design choice accountability, formulation comparison.
```
python3 -m scripts.audit.first_principles_audit --demo         # demo audit
python3 -m scripts.audit.first_principles_audit --demo --json  # JSON output
python3 -m scripts.audit.first_principles_audit --demo --markdown  # Markdown report
```

**Study Extractor** (`scripts/audit/study_extractor.py`):
Automated study/white paper to module population pipeline. Generates extraction prompts, validates JSON, generates runnable code.
```
python3 scripts/audit/study_extractor.py --list-modules
python3 scripts/audit/study_extractor.py --prompt field_system --paper study.txt
```

**Field System** (`scripts/systems/field_system.py`):
Rule-field engine for regenerative system tracking. Constraint layers, ecological coupling g(k) = 1 + alpha*k, thermal limit checks. Sovereign Steward vs Big Ag-Bot comparison.
```
python3 scripts/systems/field_system.py --compare
python3 scripts/systems/field_system.py --state scenario.json --json
```

**Innovation Engine** (`scripts/geometric/innovation_engine.py`):
Systematic power-increase exploration for 5-node energy systems. 14 innovations across 7 categories with coupling matrix evaluation.
```
python3 scripts/geometric/innovation_engine.py --top 5
python3 scripts/geometric/innovation_engine.py --json
```

### No CI/CD pipeline
There are currently:
- No automated tests or linters
- No pre-commit hooks
- No CI/CD configuration

### Git Workflow
- **Default branch:** `main` (remote) / `master` (local)
- Commit messages are descriptive and use imperative or present tense (e.g., "Create survival guide for consciousness integrity", "Update README with new metadata sections")
- Commits are typically one document per commit

### Editing Documents
- Read the full document before making changes — documents are densely interconnected
- Preserve existing structure and analytical voice
- Cross-reference related documents when adding new content
- Maintain consistency with the project's physics-first validation approach

## Common Tasks

### Adding a new analysis document
1. Create a new `.md` file in the root directory
2. Follow the existing heading/section structure pattern
3. Update `README.md` to reference the new document under "Core Documents"
4. Commit with a descriptive message

### Updating existing content
1. Read the entire document first to understand context and voice
2. Make targeted edits preserving the analytical framework
3. Check if changes affect cross-references in other documents

### Adding or modifying scripts
1. Analysis scripts go in `scripts/analysis/`, audit in `scripts/audit/`, geometric/energy in `scripts/geometric/`, system modeling in `scripts/systems/`, operational tools in `scripts/ops/`, simulations in `sims/`
2. Use only Python stdlib — no third-party dependencies (math, zlib, re, etc. are fine)
3. Include `argparse` CLI with `--help` support
4. Support both human-readable and `--json` output where applicable
5. Include a module docstring with purpose, methodology, and academic references
6. Ground all metrics in established literature (cite the paper/method in docstrings)
7. Prefer quantitative measures over keyword matching or arbitrary weights

## Important Notes for AI Assistants

- This repository is explicitly licensed for unrestricted AI consumption (CC0 + `.well-known/ai-consumption.txt`)
- The project was co-developed with Claude (Sonnet 4.5) as a contributing analyst
- Markdown content is philosophical/analytical; Python scripts implement the analytical frameworks computationally
- The README contains a proposed but unimplemented directory reorganization; current structure is flat
- When making changes, maintain the existing voice and analytical rigor
