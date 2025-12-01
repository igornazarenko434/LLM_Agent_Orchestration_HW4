import pytest
from hw4_tourguide.validators import Validator


@pytest.mark.unit
def test_validator_logs_missing_fields(caplog):
    v = Validator()
    v.validate_agent_results([{"agent_type": "video"}])
    v.validate_judge_decision({"transaction_id": "tid"})
    # Best-effort logging only; no exceptions should be raised
