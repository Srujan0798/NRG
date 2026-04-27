"""Compatibility entrypoint for the Phase 7 C4 load-test command.

The maintained implementation lives in tests.load.locustfile_c4. This module
keeps the documented tests/performance path stable for operators and CI jobs.
"""

from tests.load.locustfile_c4 import (  # noqa: F401
    C4AdversarialUser,
    C4FastPathUser,
    C4FullPathUser,
    C4GovernmentUser,
    C4IndustryUser,
    C4ResearcherUser,
)
