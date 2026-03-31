# study_extractor.py

# Automated Study/White Paper → Module Population Pipeline

# 

# Workflow:

# 1. generate_extraction_prompt(paper_text, modules)  → prompt for any AI

# 2. AI returns structured JSON

# 3. validate_extraction(json_data)                   → checks completeness

# 4. generate_code(json_data, module)                 → runnable Python

# 5. Run first_principles_audit on the generated code

# 

# Designed so ANY AI model can:

# - Receive the schema

# - Read a paper

# - Output structured data

# - Produce code that populates any module in the framework

import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field, asdict
from io import StringIO

# =========================================================================

# MODULE SCHEMAS — What each module needs populated

# =========================================================================

MODULE_SCHEMAS = {
“field_system”: {
“description”: “Regenerative system constraint engine with effective yield and ecological coupling”,
“state_variables”: {
“soil_trend”: {“type”: “float”, “units”: “change/year”, “range”: [-1, 1], “required”: True, “description”: “Rate of soil organic matter change”},
“water_retention”: {“type”: “float”, “units”: “fraction”, “range”: [0, 1], “required”: True, “description”: “Water infiltration/retention capacity”},
“input_energy”: {“type”: “float”, “units”: “arbitrary”, “range”: [0, None], “required”: True, “description”: “Total external energy inputs”},
“output_yield”: {“type”: “float”, “units”: “arbitrary”, “range”: [0, None], “required”: True, “description”: “Total production output”},
“disturbance”: {“type”: “float”, “units”: “fraction”, “range”: [0, 1], “required”: True, “description”: “Disturbance level (tillage, chemical, etc)”},
“waste_factor”: {“type”: “float”, “units”: “fraction”, “range”: [0, 1], “required”: True, “description”: “Fraction of yield lost before consumption”},
“nutrient_density”: {“type”: “float”, “units”: “fraction”, “range”: [0, 1], “required”: True, “description”: “Nutritional quality relative to baseline”},
},
“functions”: [“report”, “effective_yield”, “ecological_amplification”, “valuation_distortion”],
},

```
"field_system_expanded": {
    "description": "Full dependency accounting for production systems",
    "registerable": "Dependency",
    "fields": {
        "name": {"type": "str", "required": True},
        "type": {"type": "DependencyType", "required": True, "options": ["clean_water", "clean_air", "data_infrastructure", "satellite_systems", "proprietary_software", "genetic_ip", "supply_chain", "regulatory_compliance"]},
        "current_cost": {"type": "float", "units": "$/unit/time", "required": True, "description": "Apparent cost paid by operator"},
        "hidden_subsidy": {"type": "float", "units": "$/unit/time", "required": True, "description": "Cost externalized to society/environment"},
        "degradation_rate": {"type": "float", "units": "fraction/year", "required": True, "description": "Rate of resource depletion (negative = regenerating)"},
        "alternative_cost": {"type": "float", "units": "$/unit/time", "required": True, "description": "Cost of sustainable alternative"},
        "measurement_method": {"type": "str", "required": True, "description": "How this dependency is measured"},
    },
},

"dependency_audit": {
    "description": "Structural vulnerability and hidden subsidy auditing",
    "registerable": "DependencyAuditEntry",
    "fields": {
        "name": {"type": "str", "required": True},
        "source": {"type": "DependencySource", "required": True, "options": ["public_infrastructure", "private_monopoly", "commons", "natural_capital", "social_capital"]},
        "current_cost": {"type": "float", "required": True},
        "hidden_subsidy": {"type": "float", "required": True},
        "true_cost": {"type": "float", "required": True},
        "degradation_rate": {"type": "float", "required": True},
        "years_remaining": {"type": "float", "required": True},
        "alternative_available": {"type": "bool", "required": True},
        "alternative_cost": {"type": "float", "required": True},
        "substitution_feasibility": {"type": "float", "range": [0, 1], "required": True},
        "data_quality": {"type": "float", "range": [0, 1], "required": True},
    },
},

"system_weaver": {
    "description": "Swappable system components for exploration",
    "registerable": "SystemComponent",
    "fields": {
        "name": {"type": "str", "required": True},
        "type": {"type": "ComponentType", "required": True, "options": ["water_system", "air_system", "data_system", "genetic_system", "energy_system", "knowledge_system", "supply_chain", "regulatory_framework", "ecological_strategy"]},
        "description": {"type": "str", "required": True},
        "parameters": {"type": "dict[str,float]", "required": True, "description": "Measurable properties"},
        "dependencies": {"type": "dict[str,float]", "required": True, "description": "External dependencies (name → intensity 0-1)"},
        "cost_structure": {"type": "dict[str,float]", "required": True, "description": "Keys: direct, hidden, externalized"},
        "origin": {"type": "str", "required": False},
    },
},

"energy_wisdom_explorer": {
    "description": "Energy practice registry with synergy detection",
    "registerable": "EnergyPractice",
    "fields": {
        "name": {"type": "str", "required": True},
        "origin": {"type": "EnergyOrigin", "required": True, "options": ["piezoelectric", "thermal_mass", "concentrated_solar", "thermoelectric", "bioenergy", "wind_passive", "magnetic", "radiant", "geothermal", "photovoltaic", "biomimetic", "vernacular"]},
        "domains": {"type": "list[EnergyDomain]", "required": True, "options": ["generation", "storage", "transmission", "efficiency", "heat_management", "materials", "manufacturing", "reclamation"]},
        "description": {"type": "str", "required": True},
        "mechanism": {"type": "str", "required": True},
        "parameters": {"type": "dict[str,float]", "required": True},
        "dependencies": {"type": "list[str]", "required": True},
        "materials": {"type": "list[str]", "required": True},
        "energy_return_on_investment": {"type": "float", "required": True},
        "scalability": {"type": "float", "range": [0, 1], "required": True},
        "environment_fit": {"type": "dict[str,float]", "required": False, "description": "Environment tag → suitability 0-1"},
    },
},

"desert_sand_energy_coupling": {
    "description": "Multi-domain energy coupling from substrate materials",
    "registerable": "EnergyCoupling",
    "fields": {
        "name": {"type": "str", "required": True},
        "physics": {"type": "list[PhysicsDomain]", "required": True, "options": ["mechanical", "thermal", "electromagnetic", "quantum", "acoustic", "optical", "chemical", "gravitational", "fluid_dynamic", "thermoelectric", "piezoelectric", "pyroelectric", "triboelectric", "magnetic", "radio_frequency"]},
        "mechanism": {"type": "str", "required": True},
        "efficiency": {"type": "float", "range": [0, 1], "required": True},
        "power_density": {"type": "float", "units": "W/m2", "required": False},
        "scalability": {"type": "float", "range": [0, 1], "required": True},
        "environment_fit": {"type": "dict[str,float]", "required": False},
        "resonance_frequency": {"type": "float", "units": "Hz", "required": False},
        "materials_needed": {"type": "list[str]", "required": False},
        "status": {"type": "str", "required": False},
    },
},

"resource_flow_dynamics": {
    "description": "Coupled H/C/R resource flow dynamics",
    "parameters": {
        "alpha": {"type": "float", "description": "Extraction rate (C→H)", "range": [0, 1]},
        "beta": {"type": "float", "description": "Release rate (H→C)", "range": [0, 1]},
        "delta": {"type": "float", "description": "Productivity rate", "range": [0, 1]},
        "gamma": {"type": "float", "description": "Dissipation rate", "range": [0, 1]},
        "k1": {"type": "float", "description": "Responsiveness degradation rate", "range": [0, 1]},
        "k2": {"type": "float", "description": "Responsiveness recovery rate", "range": [0, 1]},
        "C_ref": {"type": "float", "description": "Reference C level for signal normalization"},
    },
},

"organization_topology": {
    "description": "Hierarchy vs distributed vs embedded-rule comparison",
    "parameters": {
        "n_agents": {"type": "int", "description": "Number of agents"},
        "update_rate": {"type": "float", "description": "Compliance/coupling rate", "range": [0, 1]},
        "replacement_elasticity": {"type": "float", "description": "How easily nodes swap", "range": [0, 1]},
        "constraint_density": {"type": "float", "description": "Constraints per node", "range": [0, 1]},
        "externalization_capacity": {"type": "float", "description": "Ability to push cost outside", "range": [0, 1]},
    },
},

"operational_risk_monitor": {
    "description": "Weighted risk scoring with configurable thresholds",
    "registerable": "RiskProfile weights",
    "fields": {
        "metric_name": {"type": "str", "required": True},
        "weight": {"type": "float", "range": [0, 1], "required": True, "description": "Relative importance (weights should sum to ~1)"},
        "value": {"type": "float", "range": [0, 1], "required": True, "description": "Normalized metric value"},
    },
},

"mineral_mulch_sim": {
    "description": "Stone mulch microclimate simulation",
    "parameters": {
        "soil_ph": {"type": "float", "range": [0, 14], "description": "Initial soil pH"},
        "soil_moisture": {"type": "float", "range": [0, 1], "description": "Initial soil moisture fraction"},
        "mean_temp_c": {"type": "float", "units": "°C", "description": "Daily mean temperature"},
        "temp_amplitude_c": {"type": "float", "units": "°C", "description": "Daily temperature swing half-range"},
        "albedo": {"type": "float", "range": [0, 1], "description": "Stone reflectivity"},
        "dissolution_rate": {"type": "float", "description": "pH buffering rate per step"},
        "insulation_factor": {"type": "float", "range": [0, 1], "description": "Thermal insulation effectiveness"},
    },
},

"salvage_reclamation": {
    "description": "Material reclamation from failed components",
    "registerable": "SalvageProfile",
    "fields": {
        "salvage_potential": {"type": "float", "range": [0, 1], "required": True, "description": "Fraction rebuildable from scrap"},
        "recoverable_materials": {"type": "dict[str,float]", "required": True, "description": "Material name → mass in kg"},
        "reusable_subassemblies": {"type": "list[str]", "required": False},
        "tooling_required": {"type": "list[str]", "required": True, "description": "Tools needed to reclaim"},
        "entropy_leak_w": {"type": "float", "units": "W", "required": False, "description": "Capturable waste heat"},
    },
},

"geometric_boo": {
    "description": "Distributed infrastructure components",
    "registerable": "BOOComponent",
    "fields": {
        "name": {"type": "str", "required": True},
        "function": {"type": "str", "required": True},
        "mass_kg": {"type": "float", "required": True},
        "power_w": {"type": "float", "required": True, "description": "Watts generated (negative = consumed)"},
        "water_l_per_day": {"type": "float", "required": True},
        "cost_usd": {"type": "float", "required": True},
        "deployment_time_hours": {"type": "float", "required": True},
        "lifespan_years": {"type": "float", "required": True},
        "dependencies": {"type": "list[str]", "required": True},
        "provides": {"type": "list[str]", "required": True},
    },
},

"viewpoint_comparison": {
    "description": "Ontological viewpoint gap analysis",
    "registerable": "Viewpoint",
    "fields": {
        "name": {"type": "str", "required": True},
        "sees": {"type": "list[str]", "required": True},
        "asks": {"type": "list[str]", "required": True},
        "assumes": {"type": "list[str]", "required": True},
        "misses": {"type": "list[str]", "required": True},
    },
},

"unified_geometric_framework": {
    "description": "Coupled vector system geometry",
    "registerable": "Vector + Coupling",
    "vector_fields": {
        "name": {"type": "str", "required": True},
        "magnitude": {"type": "float", "range": [0, 1], "required": True},
        "direction": {"type": "float", "units": "degrees", "required": True},
        "domain": {"type": "str", "required": False},
    },
    "coupling_fields": {
        "v1": {"type": "str", "required": True},
        "v2": {"type": "str", "required": True},
        "strength": {"type": "float", "range": [0, 1], "required": True},
        "mechanism": {"type": "str", "required": False},
        "synergy": {"type": "float", "required": False, "description": ">1 means positive synergy"},
    },
},
```

}

# Also require for ALL modules:

UNIVERSAL_REQUIREMENTS = {
“study_metadata”: {
“title”: {“type”: “str”, “required”: True},
“authors”: {“type”: “list[str]”, “required”: True},
“year”: {“type”: “int”, “required”: True},
“doi_or_url”: {“type”: “str”, “required”: False},
“peer_reviewed”: {“type”: “bool”, “required”: True},
“sample_size”: {“type”: “int”, “required”: False},
“methodology”: {“type”: “str”, “required”: True},
“geographic_scope”: {“type”: “str”, “required”: False},
“time_span”: {“type”: “str”, “required”: False},
},
“assumptions_extracted”: {
“type”: “list”,
“item_fields”: {
“name”: {“type”: “str”, “required”: True},
“description”: {“type”: “str”, “required”: True},
“basis”: {“type”: “str”, “required”: True, “options”: [“physics”, “empirical”, “convention”, “simplification”]},
“falsifiable”: {“type”: “bool”, “required”: True},
“falsification_test”: {“type”: “str”, “required”: True},
“impact_if_wrong”: {“type”: “str”, “required”: True},
},
},
“design_choices_extracted”: {
“type”: “list”,
“item_fields”: {
“name”: {“type”: “str”, “required”: True},
“chosen”: {“type”: “str”, “required”: True},
“alternatives”: {“type”: “list[str]”, “required”: True},
“reason”: {“type”: “str”, “required”: True},
“bias_risk”: {“type”: “list[str]”, “required”: True, “options”: [“optimization_bias”, “recency_bias”, “complexity_bias”, “simplification_bias”, “linearity_bias”, “survivorship_bias”, “scale_bias”, “externalization_bias”]},
“who_decided”: {“type”: “str”, “required”: True},
},
},
“data_quality”: {
“measurement_methods”: {“type”: “list[str]”, “required”: True},
“uncertainty_reported”: {“type”: “bool”, “required”: True},
“confidence_intervals”: {“type”: “bool”, “required”: False},
“replication_info”: {“type”: “str”, “required”: False},
},
}

# =========================================================================

# PROMPT GENERATOR — Creates extraction instructions for any AI

# =========================================================================

def generate_extraction_prompt(
target_modules: List[str],
paper_text: Optional[str] = None,
) -> str:
“””
Generate a structured prompt that any AI can use to extract
data from a study/white paper and populate framework modules.

```
Parameters
----------
target_modules : list[str]
    Which modules to populate (keys from MODULE_SCHEMAS).
paper_text : str, optional
    If provided, included in the prompt for the AI to process.

Returns
-------
str : Complete prompt ready to paste into any AI.
"""
lines = []
a = lines.append

a("# STUDY EXTRACTION TASK")
a("")
a("You are extracting data from a study/white paper to populate")
a("a computational framework. Follow these rules exactly:")
a("")
a("1. Extract ONLY what the paper states. Do not infer or assume.")
a("2. If a value is not stated, mark it as null with a note explaining why.")
a("3. For every parameter, cite the page/section/table where you found it.")
a("4. Flag any value you are uncertain about with uncertainty_flag: true.")
a("5. Identify ALL assumptions the paper makes, whether stated or implied.")
a("6. Identify design choices: what methodology was chosen and what alternatives exist.")
a("7. Assess bias risk for each design choice.")
a("")
a("Return your response as a single JSON object matching the schema below.")
a("")

# Universal requirements
a("## REQUIRED FOR ALL EXTRACTIONS")
a("```json")
a(json.dumps(UNIVERSAL_REQUIREMENTS, indent=2))
a("```")
a("")

# Module-specific schemas
for module_name in target_modules:
    if module_name not in MODULE_SCHEMAS:
        a(f"## WARNING: Unknown module '{module_name}' — skipped")
        continue

    schema = MODULE_SCHEMAS[module_name]
    a(f"## MODULE: {module_name}")
    a(f"Description: {schema['description']}")
    a("")

    if "state_variables" in schema:
        a("### State Variables (extract values from study)")
        a("```json")
        a(json.dumps(schema["state_variables"], indent=2))
        a("```")

    if "fields" in schema:
        a(f"### Registerable: {schema.get('registerable', 'item')}")
        a("Extract one entry per distinct item found in the study.")
        a("```json")
        a(json.dumps(schema["fields"], indent=2))
        a("```")

    if "parameters" in schema:
        a("### Parameters (extract or derive from study)")
        a("```json")
        a(json.dumps(schema["parameters"], indent=2))
        a("```")

    if "vector_fields" in schema:
        a("### Vectors")
        a("```json")
        a(json.dumps(schema["vector_fields"], indent=2))
        a("```")
        a("### Couplings")
        a("```json")
        a(json.dumps(schema["coupling_fields"], indent=2))
        a("```")

    a("")

# Output format
a("## OUTPUT FORMAT")
a("")
a("Return a single JSON object with this structure:")
a("```json")
a("{")
a('  "study_metadata": { ... },')
a('  "assumptions_extracted": [ ... ],')
a('  "design_choices_extracted": [ ... ],')
a('  "data_quality": { ... },')
for module_name in target_modules:
    if module_name in MODULE_SCHEMAS:
        a(f'  "{module_name}": {{ ... }},')
a("}")
a("```")
a("")

a("## VALIDATION RULES")
a("")
a("- All float values must include units")
a("- All ranges must be respected (flag violations)")
a("- Every assumption must have a falsification test")
a("- Every design choice must list alternatives and bias risks")
a("- Source citations required for every extracted value")
a("- If the paper does not contain data for a required field, set to null")
a("  and add to a 'missing_data' list with explanation")
a("")

if paper_text:
    a("## PAPER TEXT TO EXTRACT FROM")
    a("")
    a("```")
    a(paper_text[:50000])  # cap at ~50k chars
    a("```")

return "\n".join(lines)
```

# =========================================================================

# VALIDATOR — Checks extraction completeness and correctness

# =========================================================================

def validate_extraction(
extracted: Dict[str, Any],
target_modules: List[str],
) -> Dict[str, Any]:
“””
Validate extracted JSON against module schemas.

```
Returns dict with:
    valid: bool
    errors: list of issues
    warnings: list of non-critical issues
    completeness: fraction of required fields filled
"""
errors = []
warnings = []
total_required = 0
total_filled = 0

# Check universal requirements
for section_name, section_schema in UNIVERSAL_REQUIREMENTS.items():
    if section_name not in extracted:
        errors.append(f"Missing required section: {section_name}")
        continue

    if isinstance(section_schema, dict) and "type" not in section_schema:
        # It's a field dict
        for field_name, field_spec in section_schema.items():
            if field_spec.get("required"):
                total_required += 1
                value = extracted[section_name].get(field_name) if isinstance(extracted[section_name], dict) else None
                if value is not None and value != "" and value != []:
                    total_filled += 1
                else:
                    errors.append(f"{section_name}.{field_name}: required but missing")

# Check module-specific data
for module_name in target_modules:
    if module_name not in MODULE_SCHEMAS:
        continue

    schema = MODULE_SCHEMAS[module_name]
    module_data = extracted.get(module_name)

    if module_data is None:
        errors.append(f"Missing module data: {module_name}")
        continue

    # Check fields
    fields = schema.get("fields", schema.get("state_variables", schema.get("parameters", {})))
    if isinstance(fields, dict):
        for field_name, field_spec in fields.items():
            if field_spec.get("required"):
                total_required += 1
                # Module data could be a dict or list of dicts
                if isinstance(module_data, dict):
                    value = module_data.get(field_name)
                elif isinstance(module_data, list) and module_data:
                    value = module_data[0].get(field_name) if isinstance(module_data[0], dict) else None
                else:
                    value = None

                if value is not None and value != "":
                    total_filled += 1

                    # Range check
                    if "range" in field_spec and isinstance(value, (int, float)):
                        lo, hi = field_spec["range"]
                        if lo is not None and value < lo:
                            errors.append(f"{module_name}.{field_name}: {value} below minimum {lo}")
                        if hi is not None and value > hi:
                            errors.append(f"{module_name}.{field_name}: {value} above maximum {hi}")
                else:
                    if field_spec.get("required"):
                        warnings.append(f"{module_name}.{field_name}: required but not extracted")

# Check assumptions have falsification tests
assumptions = extracted.get("assumptions_extracted", [])
for i, a in enumerate(assumptions):
    if a.get("falsifiable") and not a.get("falsification_test"):
        errors.append(f"Assumption #{i+1} '{a.get('name')}': falsifiable but no test defined")

# Check design choices have alternatives
choices = extracted.get("design_choices_extracted", [])
for i, dc in enumerate(choices):
    if not dc.get("alternatives"):
        errors.append(f"Design choice #{i+1} '{dc.get('name')}': no alternatives listed")
    if not dc.get("bias_risk"):
        warnings.append(f"Design choice #{i+1} '{dc.get('name')}': no bias risks identified")

completeness = total_filled / total_required if total_required > 0 else 0

return {
    "valid": len(errors) == 0,
    "errors": errors,
    "warnings": warnings,
    "total_required": total_required,
    "total_filled": total_filled,
    "completeness": round(completeness, 3),
}
```

# =========================================================================

# CODE GENERATOR — Produces runnable Python from extracted data

# =========================================================================

def generate_code(
extracted: Dict[str, Any],
target_modules: List[str],
) -> str:
“””
Generate runnable Python code that imports modules and populates them
with extracted data.

```
Returns a complete Python script as a string.
"""
lines = []
a = lines.append

meta = extracted.get("study_metadata", {})
a(f'# Auto-generated from: {meta.get("title", "Unknown Study")}')
a(f'# Authors: {", ".join(meta.get("authors", ["Unknown"]))}')
a(f'# Year: {meta.get("year", "Unknown")}')
a(f'# Extracted by: study_extractor.py')
a("")

for module_name in target_modules:
    if module_name not in extracted:
        continue

    module_data = extracted[module_name]
    schema = MODULE_SCHEMAS.get(module_name, {})

    a(f"# {'='*60}")
    a(f"# Module: {module_name}")
    a(f"# {'='*60}")
    a("")

    if module_name == "field_system":
        a("import field_system as fs")
        a("")
        a("state = {")
        if isinstance(module_data, dict):
            for k, v in module_data.items():
                if v is not None:
                    a(f'    "{k}": {_py_val(v)},')
        a("}")
        a("")
        a("result = fs.report(state)")
        a("print(f'Score: {result[\"score\"]}')")
        a("print(f'Drift: {result[\"drift\"]}')")
        a("for action in result['suggestions']['actions']:")
        a("    print(f'  → {action}')")
        a("")

    elif module_name == "resource_flow_dynamics":
        a("import resource_flow_dynamics as rfd")
        a("")
        a("params = rfd.FlowParams(")
        if isinstance(module_data, dict):
            for k, v in module_data.items():
                if v is not None:
                    a(f"    {k}={_py_val(v)},")
        a(")")
        a("")
        a("history = rfd.run_single(params, steps=500)")
        a("diagnosis = rfd.diagnose_single(history)")
        a("print(f'Regime: {diagnosis[\"regime\"]}')")
        a("")

    elif module_name == "organization_topology":
        a("import organization_topology as ot")
        a("")
        a("results = ot.compare_topologies(")
        if isinstance(module_data, dict):
            for k, v in module_data.items():
                if v is not None:
                    a(f"    {k}={_py_val(v)},")
        a(")")
        a("for r in results:")
        a("    print(f'{r[\"name\"]:15} error={r[\"final_error\"]:.3f} energy={r[\"total_energy\"]:.1f}')")
        a("")

    elif "registerable" in schema:
        # Generic registry population
        a(f"import {module_name}")
        a("")
        items = module_data if isinstance(module_data, list) else [module_data]
        for i, item in enumerate(items):
            if not isinstance(item, dict):
                continue
            a(f"# Item {i+1}")
            a(f"item_{i} = {_dict_to_constructor(item)}")
            a("")
        a(f"# Register all items into the appropriate library")
        a(f"# (adjust import and registration call for specific module)")
        a("")

    else:
        # Generic parameter population
        a(f"import {module_name}")
        a("")
        a(f"params = {_dict_to_py(module_data)}")
        a("")

# Add audit integration
a("# " + "=" * 60)
a("# Run First-Principles Audit")
a("# " + "=" * 60)
a("")
a("import first_principles_audit as fpa")
a("")

# Generate assumptions
assumptions = extracted.get("assumptions_extracted", [])
if assumptions:
    a("assumptions = [")
    for ass in assumptions:
        a(f"    fpa.AssumptionRecord(")
        a(f"        name={_py_val(ass.get('name', ''))},")
        a(f"        description={_py_val(ass.get('description', ''))},")
        a(f"        basis={_py_val(ass.get('basis', 'convention'))},")
        a(f"        falsifiable={_py_val(ass.get('falsifiable', True))},")
        a(f"        falsification_test={_py_val(ass.get('falsification_test', ''))},")
        a(f"        impact_if_wrong={_py_val(ass.get('impact_if_wrong', ''))},")
        a(f"    ),")
    a("]")
    a("")

# Generate design choices
choices = extracted.get("design_choices_extracted", [])
if choices:
    a("design_choices = [")
    for dc in choices:
        a(f"    fpa.DesignChoice(")
        a(f"        name={_py_val(dc.get('name', ''))},")
        a(f"        chosen={_py_val(dc.get('chosen', ''))},")
        a(f"        alternatives={_py_val(dc.get('alternatives', []))},")
        a(f"        reason={_py_val(dc.get('reason', ''))},")
        a(f"        bias_risk={_py_val(dc.get('bias_risk', []))},")
        a(f"        who_decided={_py_val(dc.get('who_decided', 'unknown'))},")
        a(f"    ),")
    a("]")
    a("")

a("# Run audit on the primary function")
a("# (uncomment and adjust for specific module)")
a("# result = fpa.full_audit(")
a("#     func=YOUR_FUNCTION,")
a("#     base_params=params,")
a("#     param_ranges=ranges,")
a("#     specs=specs,")
a("#     assumptions=assumptions,")
a("#     design_choices=design_choices,")
a("# )")
a("")

return "\n".join(lines)
```

def _py_val(v):
“”“Convert a value to Python literal string.”””
if isinstance(v, str):
return repr(v)
if isinstance(v, bool):
return str(v)
if v is None:
return “None”
return repr(v)

def _dict_to_py(d):
“”“Convert dict to Python dict literal string.”””
if not isinstance(d, dict):
return repr(d)
items = []
for k, v in d.items():
items.append(f’    “{k}”: {_py_val(v)}’)
return “{\n” + “,\n”.join(items) + “\n}”

def _dict_to_constructor(d):
“”“Convert dict to a generic constructor-style string.”””
items = []
for k, v in d.items():
items.append(f”    {k}={_py_val(v)}”)
return “dict(\n” + “,\n”.join(items) + “\n)”

# =========================================================================

# CONVENIENCE: List available modules

# =========================================================================

def list_modules() -> Dict[str, str]:
“”“List all available module schemas with descriptions.”””
return {name: schema[“description”] for name, schema in MODULE_SCHEMAS.items()}

def get_schema(module_name: str) -> Optional[Dict]:
“”“Get the schema for a specific module.”””
return MODULE_SCHEMAS.get(module_name)
