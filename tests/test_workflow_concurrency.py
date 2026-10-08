import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi import HTTPException
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.main import submission_decision, submit_department
from app.models import Submission, SubmissionEvent, Notification
import app.program_service as service


@pytest.mark.postgres
@pytest.mark.parametrize('operation,second_operation', [
    ('submit', 'submit'), ('approve', 'approve'), ('return', 'return'),
    ('approve', 'return'), ('return', 'approve'), ('submit', 'approve'), ('approve', 'submit'),
])
def test_concurrent_transition_applied_once(db, sample, monkeypatch, operation, second_operation):
    assert db.get_bind().dialect.name == 'postgresql'
    submission = db.scalar(select(Submission))
    submission.status = 'draft' if operation == 'submit' else 'submitted'
    submission.revision = 0 if operation == 'submit' else 1
    db.commit()
    sid = submission.id
    user = sample['user'] if operation == 'submit' else sample['strategy']
    first_read = threading.Event()
    second_read = threading.Event()
    original = service.validate_department if operation != 'return' else service.department_snapshot
    entered = [0]
    guard = threading.Lock()
    def held_read(*args):
        result = original(*args)
        with guard:
            entered[0] += 1
            first = entered[0] == 1
        if first:
            first_read.set()
            second_read.wait(timeout=1)
        else:
            second_read.set()
        return result
    monkeypatch.setattr(service, 'validate_department' if operation != 'return' else 'department_snapshot', held_read)
    class Request:
        def __init__(self, decision): self.decision = decision
        async def json(self): return {'decision': self.decision, 'note': 'Düzeltin.'}
    def call(decision):
        with Session(db.get_bind(), expire_on_commit=False) as session:
            try:
                if decision == 'submit': return submit_department(1, session, sample['user'])
                return asyncio.run(submission_decision(sid, Request(decision), session, sample['strategy']))
            except HTTPException as error:
                session.rollback()
                return {'status': error.status_code}
    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(call, operation)
        assert first_read.wait(timeout=5)
        second = pool.submit(call, second_operation)
        results = [first.result(timeout=10), second.result(timeout=10)]
    assert sum(result.get('ok') is True for result in results) == 1
    assert sum(result.get('status') == 409 for result in results) == 1
    db.expire_all()
    assert db.scalar(select(func.count()).select_from(SubmissionEvent)) == 1
    assert db.scalar(select(func.count()).select_from(Notification)) == 1
    assert db.get(Submission, sid).revision == 1
