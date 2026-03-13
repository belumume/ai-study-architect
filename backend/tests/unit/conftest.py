"""Unit test conftest -- no database required.

Overrides the session-scoped autouse setup_database fixture from the parent
conftest so pure unit tests can run without a PostgreSQL connection.
"""

import pytest


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """No-op override: unit tests do not need a database."""
    yield
