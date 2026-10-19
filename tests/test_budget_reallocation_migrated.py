"""Run core HTTP acceptance against the real migrated schema and database guards."""
import pytest
from tests.test_authorization_foundation import foundation_db
from tests.test_released_permissions import actors, http
from tests.test_budget_reallocation import budget
from tests import test_budget_reallocation as acceptance

pytestmark=pytest.mark.postgres


@pytest.fixture
def db(foundation_db):
    return foundation_db


def test_migrated_apply_and_reversal(db,sample,budget,http):
    acceptance.test_exact_amounts_protected_lines_rounding_history_and_reverse(db,sample,budget,http)


def test_migrated_delegation(db,actors,budget,http):
    acceptance.test_staff_denied_delegation_grant_and_revocation(db,actors,budget,http)
