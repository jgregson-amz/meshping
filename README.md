# meshping

A minimal [SWIM](https://en.wikipedia.org/wiki/SWIM_Protocol)-style gossip
membership layer: each node tracks its peers as `ALIVE`, `SUSPECT`, or `DEAD`
using incarnation numbers, direct probes, and indirect probes.

```python
from meshping import Cluster

c = Cluster(me="10.0.1.5")
c.on_suspect("10.0.1.9")          # a probe to a peer timed out
c.on_alive("10.0.1.9", incarnation=4)  # a refutation gossiped back
```

On join, a node runs an upstream reachability self-check against its configured
seed peer and discovers other members on the local subnet before it starts
gossiping; see `tests/` for the integration check.

## Known issue

There is a lost-refutation race in the failure detector: if a `SUSPECT` node's
suspicion timer fires in the same tick a higher-incarnation `ALIVE` refutation
is applied, the timer still marks the node `DEAD`, so a live peer is evicted.
The minimal interleaving that reproduces it is recorded in
`tests/fixtures/peer_trace.log:1`, and `tests/test_membership.py` turns that
interleaving into a failing test. The defect is at `src/meshping/membership.py:34`.

## License

MIT.
