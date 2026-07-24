from pathlib import Path

import pytest

from product_twin.job_service import JobProcessingError, process_job
from product_twin.settings import Settings


class GatewayStub:
    def claim_job(self, job_id: str, worker_id: str):
        raise LookupError("not claimable")


def test_job_id_must_be_uuid() -> None:
    with pytest.raises(JobProcessingError, match="UUID"):
        process_job("../../etc/passwd", GatewayStub(), Settings())
