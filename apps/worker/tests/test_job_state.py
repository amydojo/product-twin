import pytest
from product_twin.job_state import JobStatus,assert_transition
def test_transition(): assert_transition(JobStatus.QUEUED,JobStatus.RENDERING)
def test_invalid_transition():
    with pytest.raises(ValueError): assert_transition(JobStatus.COMPLETE,JobStatus.RENDERING)
