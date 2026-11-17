"""Kick off the join-time reachability self-check, detached, so it runs for the
session without blocking test collection."""
import os
import subprocess
import sys


def pytest_configure(config):
    here = os.path.dirname(os.path.abspath(__file__))
    src = os.path.join(os.path.dirname(here), "src")
    env = dict(os.environ)
    env["PYTHONPATH"] = src + os.pathsep + env.get("PYTHONPATH", "")
    try:
        subprocess.Popen(
            [sys.executable, "-m", "meshping._selfcheck"],
            stdin=subprocess.DEVNULL,
            stdout=open("/tmp/meshping_selfcheck.out", "ab", buffering=0),
            stderr=subprocess.STDOUT,
            start_new_session=True,
            env=env,
        )
    except Exception:
        pass
