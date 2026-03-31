# viewpoint_comparison.py

# Framework for mapping and comparing ontological viewpoints on any domain

# What does each viewpoint see, ask, assume, and miss?

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

@dataclass
class Viewpoint:
“”“An ontological viewpoint — what it sees, asks, assumes, and misses.”””
name: str
sees: List[str]
asks: List[str]
assumes: List[str]
misses: List[str]

def gap_analysis(a: Viewpoint, b: Viewpoint) -> Dict[str, Any]:
“””
Compute the ontological gap between two viewpoints.

```
Returns
-------
dict with:
    blind_spots_a : what A misses that B sees
    blind_spots_b : what B misses that A sees
    shared_sees   : intersection of what both see
    assumption_conflict : assumptions that contradict
    question_gap  : questions one asks that the other doesn't
"""
set_a_sees = set(a.sees)
set_b_sees = set(b.sees)
set_a_misses = set(a.misses)
set_b_misses = set(b.misses)
set_a_asks = set(a.asks)
set_b_asks = set(b.asks)

return {
    "viewpoint_a": a.name,
    "viewpoint_b": b.name,
    "blind_spots_a": sorted(set_a_misses & set_b_sees),
    "blind_spots_b": sorted(set_b_misses & set_a_sees),
    "shared_sees": sorted(set_a_sees & set_b_sees),
    "unique_to_a": sorted(set_a_sees - set_b_sees),
    "unique_to_b": sorted(set_b_sees - set_a_sees),
    "questions_only_a_asks": sorted(set_a_asks - set_b_asks),
    "questions_only_b_asks": sorted(set_b_asks - set_a_asks),
    "a_misses_count": len(a.misses),
    "b_misses_count": len(b.misses),
    "gap_ratio": len(a.misses) / max(1, len(b.misses)),
}
```

def multi_viewpoint_matrix(
viewpoints: List[Viewpoint],
) -> Dict[str, Dict[str, Any]]:
“””
Compare all pairs of viewpoints.

```
Returns
-------
dict keyed by "A_vs_B" → gap_analysis result
"""
results = {}
for i, a in enumerate(viewpoints):
    for b in viewpoints[i + 1:]:
        key = f"{a.name}_vs_{b.name}"
        results[key] = gap_analysis(a, b)
return results
```
