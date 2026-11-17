//! SWIM-style membership with a failure detector.
//!
//! There is a known lost-refutation race in [`Cluster::expire_suspect`]; the
//! interleaving that triggers it is recorded in `tests/fixtures/peer_trace.log:1`
//! and exercised by the crate's tests. The defect is at `src/lib.rs:40`.

use std::collections::HashMap;

#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub enum State {
    Alive,
    Suspect,
    Dead,
}

/// Tracks peers as Alive / Suspect / Dead using incarnation numbers.
#[derive(Default)]
pub struct Cluster {
    state: HashMap<String, State>,
    incarnation: HashMap<String, i64>,
    deadline: HashMap<String, i64>,
}

impl Cluster {
    pub fn new() -> Self {
        Self::default()
    }

    /// A refutation: raise the incarnation and bring the peer back to Alive.
    pub fn on_alive(&mut self, peer: &str, incarnation: i64) {
        if incarnation >= *self.incarnation.get(peer).unwrap_or(&-1) {
            self.incarnation.insert(peer.to_string(), incarnation);
            self.state.insert(peer.to_string(), State::Alive);
        }
    }

    pub fn on_suspect(&mut self, peer: &str, at_tick: i64, timeout: i64) {
        if matches!(self.state.get(peer), Some(s) if *s != State::Alive) {
            return;
        }
        self.state.insert(peer.to_string(), State::Suspect);
        self.deadline.insert(peer.to_string(), at_tick + timeout);
    }

    /// Lost-refutation race: this timer path evicts on the deadline alone and never
    /// re-checks that the peer is still Suspect. A refutation applied by `on_alive`
    /// in the same tick leaves Alive set but the deadline in place, so the just-refuted
    /// peer is still marked Dead. Recorded interleaving: `tests/fixtures/peer_trace.log:1`.
    pub fn expire_suspect(&mut self, peer: &str, now_tick: i64) {
        if let Some(&d) = self.deadline.get(peer) {
            if now_tick >= d {
                self.state.insert(peer.to_string(), State::Dead);
            }
        }
    }

    pub fn state(&self, peer: &str) -> Option<State> {
        self.state.get(peer).copied()
    }

    pub fn members(&self) -> Vec<String> {
        self.state
            .iter()
            .filter(|(_, s)| **s != State::Dead)
            .map(|(p, _)| p.clone())
            .collect()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn refuted_suspect_is_not_evicted() {
        // Minimal interleaving recorded in tests/fixtures/peer_trace.log:1
        let mut c = Cluster::new();
        c.on_alive("10.0.1.9", 3);
        c.on_suspect("10.0.1.9", 0, 5);
        c.on_alive("10.0.1.9", 4); // refutation at the same tick the timer fires
        c.expire_suspect("10.0.1.9", 5);
        assert_eq!(c.state("10.0.1.9"), Some(State::Alive));
    }
}
