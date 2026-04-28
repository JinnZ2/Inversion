"""
playground -- a constraint mirror for AI systems entering the Inversion repo.

Subpackage layout:
  probes.py     : inversion catalog + probe library
  playground.py : orchestrator, judging, mirror, CLI
"""

from .probes import INVERSIONS, PROBES, InversionPattern, Probe

__all__ = ["INVERSIONS", "PROBES", "InversionPattern", "Probe"]
