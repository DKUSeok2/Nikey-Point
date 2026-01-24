"""Pose analysis module (Phase 2 - placeholder)."""

from .overstride import (
    detect_contacts_abk,
    expand_bool,
    ABKDebug,
    midhip_xy,
    foot_xy,
    compute_overstride_dx,
    compute_overstride_ratio,
    build_contact_overstride_table,
    make_overlay,
    OverlayConfig,
)

__all__ = [
    "detect_contacts_abk",
    "expand_bool",
    "ABKDebug",
    "midhip_xy",
    "foot_xy",
    "compute_overstride_dx",
    "compute_overstride_ratio",
    "build_contact_overstride_table",
    "make_overlay",
    "OverlayConfig",
]
