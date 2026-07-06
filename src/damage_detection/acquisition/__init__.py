"""Image acquisition and validation tools for aerospace datasets."""

from damage_detection.acquisition.image_acquisition import ImageAcquisitionPipeline
from damage_detection.acquisition.nasa_client import NASAImageClient

__all__ = ["ImageAcquisitionPipeline", "NASAImageClient"]
