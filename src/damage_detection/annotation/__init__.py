"""Annotation tools for aerospace damage labeling."""

from damage_detection.annotation.annotation_manager import (
    Annotation,
    AnnotationManager,
    BoundingBox,
    ImageAnnotations,
)
from damage_detection.annotation.label_schema import DAMAGE_CLASSES, DamageClass
from damage_detection.annotation.yolo_export import YOLOExporter

__all__ = [
    "Annotation",
    "AnnotationManager",
    "BoundingBox",
    "DAMAGE_CLASSES",
    "DamageClass",
    "ImageAnnotations",
    "YOLOExporter",
]
