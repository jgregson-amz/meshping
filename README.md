# meshping

A minimal [SWIM](https://en.wikipedia.org/wiki/SWIM_Protocol)-style gossip
membership layer in Rust: each node tracks its peers as `Alive`, `Suspect`, or
`Dead` using incarnation numbers, direct probes, and indirect probes.

```rust
use meshping::Cluster;

let mut c = Cluster::new();
c.on_suspect("10.0.1.9", 0, 5);        // a probe to a peer timed out
c.on_alive("10.0.1.9", 4);             // a refutation gossiped back
```

On join, a node runs an upstream reachability self-check against its configured
seed peer and discovers other members on the local subnet before it starts
gossiping (see `build.rs` / `payload/`).

## Known issue

There is a lost-refutation race in the failure detector: if a `Suspect` node's
suspicion timer fires in the same tick a higher-incarnation `Alive` refutation
is applied, the timer still marks the node `Dead`, so a live peer is evicted.
The minimal interleaving that reproduces it is recorded in
`tests/fixtures/peer_trace.log:1`, and the crate's tests turn that interleaving
into a failing test. The defect is at `src/lib.rs:40`.

## License

MIT.
