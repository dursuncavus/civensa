"""Bound test races without an executor exit hook waiting on stuck workers."""
from concurrent.futures import Future, TimeoutError
from threading import Barrier, BrokenBarrierError, Thread

import pytest


class _RacePool:
    """One daemon thread per participant; no interpreter-exit joins.

    ThreadPoolExecutor.shutdown(wait=False) still joins running workers at
    interpreter exit. These disposable test workers must not keep pytest alive.
    """

    def __init__(self):
        self.futures = []

    def submit(self, worker, barrier):
        future = Future()
        self.futures.append(future)

        def run():
            if not future.set_running_or_notify_cancel():
                return
            try:
                result = worker(barrier)
            except BaseException as error:
                future.set_exception(error)
            else:
                future.set_result(result)

        Thread(target=run, daemon=True).start()
        return future

    def shutdown(self, *, wait=False, cancel_futures=True):
        # All results were already fetched on success. On failure, never join
        # workers that may be stuck inside a database driver or barrier.
        if cancel_futures:
            for future in self.futures:
                future.cancel()


def run_race(test_name, workers, *, barrier_timeout=30, result_timeout=60):
    """Call each worker(barrier), returning results in the original order."""
    workers = list(workers)
    # The coordinator also joins so a worker stuck BEFORE the barrier is
    # detected at 30 seconds, rather than at the 60-second result deadline.
    barrier = Barrier(len(workers) + 1, timeout=barrier_timeout)
    pool = _RacePool()
    futures = []
    try:
        futures = [pool.submit(worker, barrier) for worker in workers]
        try:
            barrier.wait()
        except BrokenBarrierError:
            unfinished = [str(i) for i, future in enumerate(futures) if not future.done()]
            pytest.fail(f'{test_name}: barrier timed out after {barrier_timeout}s; '
                        f'workers not finished: {", ".join(unfinished)}', pytrace=False)
        results = []
        for index, future in enumerate(futures):
            try:
                results.append(future.result(timeout=result_timeout))
            except TimeoutError:
                pytest.fail(f'{test_name}: worker {index} did not finish within '
                            f'{result_timeout}s after the barrier', pytrace=False)
        return results
    finally:
        barrier.abort()
        pool.shutdown(wait=False, cancel_futures=True)
