"""Boundary between image extraction and GIS feature persistence.

The GIS persistence model is owned by the GIS layer.  This module deliberately
does not create a second feature table: it hands validated feature batches to
that layer once its persistence adapter is available.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class ExtractedFeatureBatch:
    """Features produced from one upload in normalized image coordinates."""

    upload_job_id: str
    project_id: str | None
    features: list[dict]


class FeaturePersistencePort(Protocol):
    """Contract that the future GIS persistence service must implement."""

    def persist(self, batch: ExtractedFeatureBatch) -> None:
        """Persist a batch after its geometries have been validated."""


class DeferredFeatureHandoff:
    """Safe default until the GIS persistence adapter is integrated.

    The worker still returns the validated features to its caller.  This no-op
    avoids silently inventing a parallel GIS storage model while keeping the
    processing boundary testable and ready for Member 1's adapter.
    """

    def persist(self, batch: ExtractedFeatureBatch) -> None:
        return None
