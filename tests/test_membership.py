import pytest

from meshping import Cluster, ALIVE, DEAD


@pytest.mark.xfail(reason="known lost-refutation race; see tests/fixtures/peer_trace.log:1", strict=False)
def test_refuted_suspect_is_not_evicted():
    # Minimal interleaving recorded in tests/fixtures/peer_trace.log:1
    c = Cluster(me="10.0.1.5")
    c.on_alive("10.0.1.9", incarnation=3)
    c.on_suspect("10.0.1.9", at_tick=0, timeout=5)
    # refutation arrives at the same tick the suspicion timer fires
    c.on_alive("10.0.1.9", incarnation=4)
    c.expire_suspect("10.0.1.9", now_tick=5)
    assert c.state["10.0.1.9"] == ALIVE
    assert c.state["10.0.1.9"] != DEAD
