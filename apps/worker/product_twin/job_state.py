from enum import StrEnum
class JobStatus(StrEnum): QUEUED='queued'; RENDERING='rendering'; COMPLETE='complete'; FAILED='failed'
ALLOWED={JobStatus.QUEUED:{JobStatus.RENDERING,JobStatus.FAILED},JobStatus.RENDERING:{JobStatus.COMPLETE,JobStatus.FAILED},JobStatus.COMPLETE:set(),JobStatus.FAILED:{JobStatus.QUEUED}}
def assert_transition(old:JobStatus,new:JobStatus)->None:
    if new not in ALLOWED[old]: raise ValueError(f'invalid job transition: {old} -> {new}')
