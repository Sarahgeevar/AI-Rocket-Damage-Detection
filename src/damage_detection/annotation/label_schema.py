"""Centralized aerospace damage class schema."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DamageClass:
    """A single supported aerospace damage label."""

    id: int
    name: str
    description: str


DAMAGE_CLASSES: tuple[DamageClass, ...] = (
    DamageClass(0, "CRACK", "Visible fracture or linear crack in a surface."),
    DamageClass(1, "TILE_DAMAGE", "Damaged thermal protection tile or tile surface."),
    DamageClass(2, "MISSING_TILE", "Thermal protection tile that is partially or fully missing."),
    DamageClass(3, "SCORCH_MARK", "Burn, soot, or heat discoloration mark."),
    DamageClass(4, "DEBRIS_IMPACT", "Impact mark caused by debris or foreign object contact."),
    DamageClass(5, "INSULATION_DAMAGE", "Damaged foam, blanket, or insulation material."),
    DamageClass(6, "ICE_DAMAGE", "Damage or hazard related to ice accumulation or shedding."),
    DamageClass(7, "DENT", "Localized indentation or deformation of a surface."),
    DamageClass(8, "CORROSION", "Oxidation, rust, or corrosion-like surface degradation."),
    DamageClass(9, "OTHER", "Damage that does not fit another defined class."),
)


DAMAGE_CLASS_BY_ID: dict[int, DamageClass] = {
    damage_class.id: damage_class for damage_class in DAMAGE_CLASSES
}

DAMAGE_CLASS_BY_NAME: dict[str, DamageClass] = {
    damage_class.name: damage_class for damage_class in DAMAGE_CLASSES
}


def get_damage_class(damage_class: int | str) -> DamageClass:
    """Return a damage class by integer ID or uppercase class name."""

    if isinstance(damage_class, int):
        if damage_class in DAMAGE_CLASS_BY_ID:
            return DAMAGE_CLASS_BY_ID[damage_class]
    else:
        normalized = damage_class.upper()
        if normalized in DAMAGE_CLASS_BY_NAME:
            return DAMAGE_CLASS_BY_NAME[normalized]
    raise ValueError(f"Unsupported damage class: {damage_class}")
