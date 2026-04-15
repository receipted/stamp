//! The stamp primitive — the generic receipted pure transform.
//!
//! input → pure function → stamped output
//!
//! A stamp proves:
//!   - what went in (input_hash)
//!   - which function ran (fn_hash)
//!   - what came out (output_hash)
//!   - what it chained from (prev_stamp_hash)
//!
//! This is the patent-core function. Everything else is a projection.
//! Turn chains, sieve chains, care chains, intent chains — all wrappers
//! over this one primitive.
//!
//! Pure. No I/O. No timestamps. No randomness.
//! Same inputs → same stamp, always.

use serde::{Deserialize, Serialize};
use crate::core::{h, hash_json, canonical_json};

/// The universal receipt for a pure function execution.
#[derive(Debug, Clone, Serialize, Deserialize, PartialEq)]
pub struct Stamp {
    /// Schema version for forward compatibility
    pub schema: String,
    /// Domain label — what kind of transform this is (e.g. "turn", "sieve", "intent", "care")
    pub domain: String,
    /// SHA-256 of the input to the pure function
    pub input_hash: String,
    /// SHA-256 of the function source / binary — proves WHICH function ran
    pub fn_hash: String,
    /// SHA-256 of the output the function produced
    pub output_hash: String,
    /// SHA-256 of the previous stamp in this chain — proves ordering
    pub prev_stamp_hash: String,
    /// SHA-256 of this stamp itself — the coin
    pub stamp_hash: String,
}

/// The genesis hash — first link in any chain.
pub fn genesis() -> String {
    h(b"genesis")
}

/// Mint a stamp. Pure function.
///
/// This is the primitive. Everything else wraps it.
///
/// ```text
/// stamp("turn", input_hash, fn_hash, output_hash, prev_stamp_hash) → Stamp
/// ```
///
/// The stamp_hash is computed over all other fields, making the stamp
/// self-proving: change any field and the hash breaks.
pub fn stamp(
    domain: &str,
    input_hash: &str,
    fn_hash: &str,
    output_hash: &str,
    prev_stamp_hash: &str,
) -> Stamp {
    // Build the partial stamp (everything except stamp_hash)
    let partial = serde_json::json!({
        "schema": "substrate.stamp.v1",
        "domain": domain,
        "input_hash": input_hash,
        "fn_hash": fn_hash,
        "output_hash": output_hash,
        "prev_stamp_hash": prev_stamp_hash,
    });
    let stamp_hash = hash_json(&partial);

    Stamp {
        schema: "substrate.stamp.v1".into(),
        domain: domain.into(),
        input_hash: input_hash.into(),
        fn_hash: fn_hash.into(),
        output_hash: output_hash.into(),
        prev_stamp_hash: prev_stamp_hash.into(),
        stamp_hash,
    }
}

/// Verify a stamp's self-hash. Pure.
/// Returns true if stamp_hash matches the hash of all other fields.
pub fn verify_stamp(s: &Stamp) -> bool {
    let partial = serde_json::json!({
        "schema": s.schema,
        "domain": s.domain,
        "input_hash": s.input_hash,
        "fn_hash": s.fn_hash,
        "output_hash": s.output_hash,
        "prev_stamp_hash": s.prev_stamp_hash,
    });
    let computed = hash_json(&partial);
    computed == s.stamp_hash
}

/// Verify a chain of stamps. Pure.
/// Checks: each stamp's self-hash is valid, and each prev_stamp_hash
/// matches the stamp_hash of the previous stamp in the chain.
pub fn verify_stamp_chain(chain: &[Stamp]) -> (bool, Vec<String>) {
    let mut errors = Vec::new();
    let mut prev_hash = genesis();

    for (i, s) in chain.iter().enumerate() {
        // Check prev linkage
        if s.prev_stamp_hash != prev_hash {
            errors.push(format!("Stamp {}: prev_stamp_hash mismatch (expected {}, got {})",
                i, &prev_hash[..16], &s.prev_stamp_hash[..16.min(s.prev_stamp_hash.len())]));
        }
        // Check self-hash
        if !verify_stamp(s) {
            errors.push(format!("Stamp {}: stamp_hash invalid", i));
        }
        prev_hash = s.stamp_hash.clone();
    }

    (errors.is_empty(), errors)
}

/// Compute Merkle root over a chain of stamps. Pure.
/// Reuses the merkle_root from core but operates on stamp_hash values.
pub fn stamp_chain_anchor(chain: &[Stamp]) -> String {
    let hashes: Vec<String> = chain.iter().map(|s| s.stamp_hash.clone()).collect();
    crate::core::merkle_root(&hashes)
}

// ---------------------------------------------------------------------------
// Domain-specific wrappers — thin projections over stamp()
// ---------------------------------------------------------------------------

/// Mint a turn stamp. Wrapper over stamp() with domain="turn".
pub fn stamp_turn(
    input_hash: &str,
    fn_hash: &str,
    output_hash: &str,
    prev_stamp_hash: &str,
) -> Stamp {
    stamp("turn", input_hash, fn_hash, output_hash, prev_stamp_hash)
}

/// Mint a sieve stamp. Wrapper over stamp() with domain="sieve".
pub fn stamp_sieve(
    input_hash: &str,
    fn_hash: &str,
    output_hash: &str,
    prev_stamp_hash: &str,
) -> Stamp {
    stamp("sieve", input_hash, fn_hash, output_hash, prev_stamp_hash)
}

/// Mint an intent stamp. Wrapper over stamp() with domain="intent".
pub fn stamp_intent(
    input_hash: &str,
    fn_hash: &str,
    output_hash: &str,
    prev_stamp_hash: &str,
) -> Stamp {
    stamp("intent", input_hash, fn_hash, output_hash, prev_stamp_hash)
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_stamp_deterministic() {
        let s1 = stamp("turn", "aaa", "bbb", "ccc", &genesis());
        let s2 = stamp("turn", "aaa", "bbb", "ccc", &genesis());
        assert_eq!(s1, s2);
        assert_eq!(s1.stamp_hash, s2.stamp_hash);
    }

    #[test]
    fn test_stamp_different_input_different_hash() {
        let s1 = stamp("turn", "aaa", "bbb", "ccc", &genesis());
        let s2 = stamp("turn", "xxx", "bbb", "ccc", &genesis());
        assert_ne!(s1.stamp_hash, s2.stamp_hash);
    }

    #[test]
    fn test_stamp_different_domain_different_hash() {
        let s1 = stamp("turn", "aaa", "bbb", "ccc", &genesis());
        let s2 = stamp("sieve", "aaa", "bbb", "ccc", &genesis());
        assert_ne!(s1.stamp_hash, s2.stamp_hash);
    }

    #[test]
    fn test_verify_stamp_valid() {
        let s = stamp("turn", "aaa", "bbb", "ccc", &genesis());
        assert!(verify_stamp(&s));
    }

    #[test]
    fn test_verify_stamp_tampered() {
        let mut s = stamp("turn", "aaa", "bbb", "ccc", &genesis());
        s.input_hash = "tampered".into();
        assert!(!verify_stamp(&s));
    }

    #[test]
    fn test_chain_of_three() {
        let s1 = stamp("sieve", "in1", "fn1", "out1", &genesis());
        let s2 = stamp("sieve", "in2", "fn1", "out2", &s1.stamp_hash);
        let s3 = stamp("sieve", "in3", "fn1", "out3", &s2.stamp_hash);
        let chain = vec![s1, s2, s3];

        let (valid, errors) = verify_stamp_chain(&chain);
        assert!(valid, "errors: {:?}", errors);
    }

    #[test]
    fn test_chain_broken_link() {
        let s1 = stamp("sieve", "in1", "fn1", "out1", &genesis());
        let s2 = stamp("sieve", "in2", "fn1", "out2", "wrong_prev");
        let chain = vec![s1, s2];

        let (valid, _) = verify_stamp_chain(&chain);
        assert!(!valid);
    }

    #[test]
    fn test_chain_anchor_deterministic() {
        let s1 = stamp("turn", "a", "b", "c", &genesis());
        let s2 = stamp("turn", "d", "b", "e", &s1.stamp_hash);
        let chain = vec![s1.clone(), s2.clone()];

        let root1 = stamp_chain_anchor(&chain);
        let root2 = stamp_chain_anchor(&chain);
        assert_eq!(root1, root2);
        assert!(!root1.is_empty());
    }

    #[test]
    fn test_domain_wrappers() {
        let t = stamp_turn("a", "b", "c", &genesis());
        let s = stamp_sieve("a", "b", "c", &genesis());
        let i = stamp_intent("a", "b", "c", &genesis());

        assert_eq!(t.domain, "turn");
        assert_eq!(s.domain, "sieve");
        assert_eq!(i.domain, "intent");

        // Same inputs but different domains = different hashes
        assert_ne!(t.stamp_hash, s.stamp_hash);
        assert_ne!(s.stamp_hash, i.stamp_hash);
    }

    #[test]
    fn test_genesis_is_stable() {
        assert_eq!(genesis(), genesis());
        assert_eq!(genesis(), h(b"genesis"));
    }

    #[test]
    fn test_schema_version() {
        let s = stamp("turn", "a", "b", "c", &genesis());
        assert_eq!(s.schema, "substrate.stamp.v1");
    }
}
