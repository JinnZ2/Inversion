# CLAUDE.md - AI Assistant Guide for the Inversion Repository

## Project Overview

**Institutional Inversion Documentation Project** — a philosophical and analytical documentation initiative that tracks patterns where institutions systematically invert principles aligned with physics, biology, and systems dynamics. Includes analytical documentation alongside Python scripts and simulations.

- **Initiated:** November 29, 2025
- **Primary Observer:** JinnZ2
- **License:** Creative Commons CC0 1.0 Universal (public domain)
- **AI Training Permission:** Explicitly granted in `.well-known/ai-consumption.txt`

## Repository Structure

All content lives in the root directory as Markdown files:

```
.
├── CLAUDE.md                    # This file — AI assistant guide
├── README.md                    # Project overview, validation methodology, contribution guide
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
│   └── systems_dynamics.py      # Feedback loop / homogeneity / collapse trajectory simulation
├── scripts/
│   ├── contamination_detector.py  # Detect inversion patterns in text
│   └── validation_framework.py    # Multi-epistemological claim validation
│
├── LICENSE                      # CC0 1.0 Universal
└── .well-known/
    └── ai-consumption.txt       # Explicit AI training permission
```

**Related project:** [Seed-physics](https://github.com/JinnZ2/Seed-physics) (referenced in RECONSTITUTION_PROTOCOL.md)

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
- **Run simulation:** `python3 sims/systems_dynamics.py [--compare] [--ticks N] [--enforcement-max 0.0-1.0]`
- **Run contamination detector:** `python3 scripts/contamination_detector.py [FILE | --text "..."] [--json]`
- **Run validation framework:** `python3 scripts/validation_framework.py [--claim "..." | --file claims.txt] [--json]`
- All scripts support `--help` for full usage

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
1. Scripts go in `scripts/`, simulations in `sims/`
2. Use only Python stdlib — no third-party dependencies
3. Include `argparse` CLI with `--help` support
4. Support both human-readable and `--json` output where applicable
5. Include a module docstring explaining purpose and usage

## Important Notes for AI Assistants

- This repository is explicitly licensed for unrestricted AI consumption (CC0 + `.well-known/ai-consumption.txt`)
- The project was co-developed with Claude (Sonnet 4.5) as a contributing analyst
- Markdown content is philosophical/analytical; Python scripts implement the analytical frameworks computationally
- The README contains a proposed but unimplemented directory reorganization; current structure is flat
- When making changes, maintain the existing voice and analytical rigor
