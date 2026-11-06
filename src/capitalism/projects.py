"""Shared research and software development project engine (design.md slice 4b)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .tables import RESEARCH_DURATIONS, RESEARCH_RULES, SOFTWARE_RULES

if TYPE_CHECKING:
    from .catalog import Product
    from .economy import Corporation, Economy


def product_duration_months(product: Product) -> int:
    """Map source-pending tech years to the seven-entry reference duration table."""
    if product.row.tech_year >= RESEARCH_RULES.max_technology:
        return 0
    bucket = min(
        len(RESEARCH_DURATIONS) - 1,
        (product.row.tech_year + RESEARCH_RULES.tech_year_divisor - 1)
        // RESEARCH_RULES.tech_year_divisor,
    )
    return RESEARCH_DURATIONS[bucket]


def project_duration_months(product: Product, software: bool) -> int:
    return SOFTWARE_RULES.software_project_months if software else product_duration_months(product)


class Project:
    """One job's active project; elapsed days remain valid while unfunded/paused."""

    __slots__ = ("completed", "elapsed_days", "funded", "paused", "product", "repeat", "started")

    def __init__(self, product: Product) -> None:
        self.product = product
        self.repeat = 0
        self.funded = True
        self.paused = False
        self.started = False
        self.completed = False
        self.elapsed_days = 0

    @property
    def active(self) -> bool:
        return self.funded and not self.paused

    @property
    def progress_months(self) -> float:
        return self.elapsed_days / RESEARCH_RULES.days_per_project_month

    def progress(self, days: int = 1) -> bool:
        if self.active:
            self.elapsed_days += days
        return False

    def duration(self, software: bool) -> int:
        return project_duration_months(self.product, software)

    def complete(self, software: bool) -> bool:
        months = self.duration(software)
        return self.started and self.elapsed_days >= months * RESEARCH_RULES.days_per_project_month


class ProjectEngine:
    """Advance project jobs and let them report completion data to their subclass."""

    @staticmethod
    def ready(corp: Corporation | None, product: Product, eco: Economy, software: bool) -> bool:
        if corp is None:
            return False
        if software:
            return True
        return all(corp.has_technology(p.requires_id) for p in eco.catalog.prerequisites(product))

    @staticmethod
    def work(job: object, eco: Economy) -> None:
        project: Project | None = job.project  # type: ignore[attr-defined]
        if project is None or job.product is None:  # type: ignore[attr-defined]
            return
        corp = job.firm.owner  # type: ignore[attr-defined]
        software = job.software_project  # type: ignore[attr-defined]
        if not ProjectEngine.ready(corp, project.product, eco, software):
            return  # prerequisites may be met later; elapsed days are retained
        if not project.started:
            if project.completed:
                return
            if project.product.row.tech_year >= RESEARCH_RULES.max_technology:
                return
            project.started = True
        project.progress()
        if not project.complete(software):
            return
        assert corp is not None
        product = project.product
        if software:
            job.complete_project(product, eco)  # type: ignore[attr-defined]
        else:
            corp.add_technology(product)
        project.started = False
        project.completed = True
        job.completed_count += 1  # type: ignore[attr-defined]
        if project.repeat and corp.technology_level(product) < RESEARCH_RULES.max_technology:
            project.product = product
            project.elapsed_days = 0
            project.completed = False
            project.started = True
