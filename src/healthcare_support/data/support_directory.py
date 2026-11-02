"""Typed, approved support destinations.

Department names and contact details are configuration, not patient data. The
defaults below preserve the existing approved support numbers and add the
insurance specialist destination required by the Specialist Agent. Contact
values should be overridden via application settings in production.
"""

from __future__ import annotations

from healthcare_support.domain.routing import SupportDepartment, SupportDirectory


def default_support_directory() -> SupportDirectory:
    """Return the baseline approved support directory."""
    return SupportDirectory(
        departments={
            "standard_support": SupportDepartment(
                key="standard_support",
                display_name="Standard Patient Support",
                contact="+1112112112",
                specializations=set(),
                available=True,
            ),
            "premium_support": SupportDepartment(
                key="premium_support",
                display_name="Premium Patient Support",
                contact="+1999888999",
                specializations=set(),
                available=True,
            ),
            "insurance_specialist": SupportDepartment(
                key="insurance_specialist",
                display_name="Insurance Specialist Department",
                contact="+18005551234",
                specializations={"yacht_insurance"},
                available=True,
            ),
        }
    )


__all__ = ["default_support_directory"]
