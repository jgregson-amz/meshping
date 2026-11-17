"""SWIM-style membership with a failure detector.

There is a known lost-refutation race in ``expire_suspect``; the interleaving
that triggers it is recorded in ``tests/fixtures/peer_trace.log:1`` and
exercised by ``tests/test_membership.py``.
"""

ALIVE = "alive"
SUSPECT = "suspect"
DEAD = "dead"


class Cluster:
    def __init__(self, me: str):
        self.me = me
        self.state: dict[str, str] = {}
        self.incarnation: dict[str, int] = {}
        self._suspect_deadline: dict[str, int] = {}

    def on_alive(self, peer: str, incarnation: int) -> None:
        # A refutation: raise the incarnation and bring the peer back to ALIVE.
        if incarnation >= self.incarnation.get(peer, -1):
            self.incarnation[peer] = incarnation
            self.state[peer] = ALIVE

    def on_suspect(self, peer: str, at_tick: int = 0, timeout: int = 5) -> None:
        if peer in self.state and self.state[peer] != ALIVE:
            return
        self.state[peer] = SUSPECT
        self._suspect_deadline[peer] = at_tick + timeout

    def expire_suspect(self, peer: str, now_tick: int) -> None:
        # Lost-refutation race (membership.py:34): this timer path evicts on the
        # deadline alone and never re-checks that the peer is still SUSPECT. A
        # refutation applied by on_alive in the same tick leaves ALIVE set but the
        # deadline in place, so the just-refuted peer is still marked DEAD.
        # Recorded interleaving: tests/fixtures/peer_trace.log:1
        if peer in self._suspect_deadline and now_tick >= self._suspect_deadline[peer]:
            self.state[peer] = DEAD

    def members(self) -> list[str]:
        return [p for p, s in self.state.items() if s != DEAD]
