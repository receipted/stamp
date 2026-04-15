//! Pure functions — no I/O, no timestamps, no randomness.
//! Same inputs → same outputs, always.
//! These are the functions that will run inside the ZK circuit.

use serde::{Deserialize, Serialize};
use sha2::{Digest, Sha256};

// ---------------------------------------------------------------------------
// Hashing
// ---------------------------------------------------------------------------

/// SHA-256 of raw bytes, returned as hex string.
pub fn h(data: &[u8]) -> String {
    let mut hasher = Sha256::new();
    hasher.update(data);
    hex::encode(hasher.finalize())
}

/// Canonical JSON hash: serialize with sorted keys, compact separators,
/// then SHA-256. This is the contract — byte-identical to Python's
/// `hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(',',':')).encode()).hexdigest()`
pub fn hash_json(value: &serde_json::Value) -> String {
    let canonical = canonical_json(value);
    h(canonical.as_bytes())
}

/// Produce canonical JSON: sorted keys, no whitespace.
/// Equivalent to Python's `json.dumps(obj, sort_keys=True, separators=(',',':'))`
pub fn canonical_json(value: &serde_json::Value) -> String {
    match value {
        serde_json::Value::Object(map) => {
            let mut keys: Vec<&String> = map.keys().collect();
            keys.sort();
            let pairs: Vec<String> = keys
                .iter()
                .map(|k| {
                    let v = canonical_json(&map[*k]);
                    format!("\"{}\":{}", escape_json_string(k), v)
                })
                .collect();
            format!("{{{}}}", pairs.join(","))
        }
        serde_json::Value::Array(arr) => {
            let items: Vec<String> = arr.iter().map(canonical_json).collect();
            format!("[{}]", items.join(","))
        }
        serde_json::Value::String(s) => format!("\"{}\"", escape_json_string(s)),
        serde_json::Value::Number(n) => n.to_string(),
        serde_json::Value::Bool(b) => b.to_string(),
        serde_json::Value::Null => "null".to_string(),
    }
}

fn escape_json_string(s: &str) -> String {
    let mut out = String::with_capacity(s.len());
    for c in s.chars() {
        match c {
            '"' => out.push_str("\\\""),
            '\\' => out.push_str("\\\\"),
            '\n' => out.push_str("\\n"),
            '\r' => out.push_str("\\r"),
            '\t' => out.push_str("\\t"),
            c if (c as u32) < 0x20 => {
                out.push_str(&format!("\\u{:04x}", c as u32));
            }
            c => out.push(c),
        }
    }
    out
}

// ---------------------------------------------------------------------------
// Turn receipts
// ---------------------------------------------------------------------------

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TurnReceipt {
    pub schema: String,
    pub turn_index: usize,
    pub role: String,
    pub model: String,
    pub text_hash: String,
    pub text_length: usize,
    pub timestamp: String,
    pub prev_receipt_hash: String,
    pub receipt_hash: String,
}

/// Hash a single turn's content. Pure.
pub fn hash_turn(role: &str, model: &str, text: &str, timestamp: &str) -> String {
    let obj = serde_json::json!({
        "role": role,
        "model": model,
        "text": text,
        "timestamp": timestamp,
    });
    hash_json(&obj)
}

/// Build a turn receipt. Pure.
pub fn make_turn_receipt(
    turn_index: usize,
    role: &str,
    model: &str,
    text: &str,
    timestamp: &str,
    prev_receipt_hash: &str,
) -> TurnReceipt {
    let text_hash = hash_turn(role, model, text, timestamp);
    let text_length = text.len();

    // Build the receipt without receipt_hash first
    let partial = serde_json::json!({
        "schema": "sidecar.turn.v1",
        "turn_index": turn_index,
        "role": role,
        "model": model,
        "text_hash": text_hash,
        "text_length": text_length,
        "timestamp": timestamp,
        "prev_receipt_hash": prev_receipt_hash,
    });
    let receipt_hash = hash_json(&partial);

    TurnReceipt {
        schema: "sidecar.turn.v1".into(),
        turn_index,
        role: role.into(),
        model: model.into(),
        text_hash,
        text_length,
        timestamp: timestamp.into(),
        prev_receipt_hash: prev_receipt_hash.into(),
        receipt_hash,
    }
}

// ---------------------------------------------------------------------------
// Chain building
// ---------------------------------------------------------------------------

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Turn {
    pub role: String,
    pub model: String,
    pub text: String,
    pub timestamp: String,
}

/// Build a receipt chain from a list of turns. Pure.
/// Same turns → same chain, every time.
pub fn build_chain(turns: &[Turn]) -> Vec<TurnReceipt> {
    let mut chain = Vec::with_capacity(turns.len());
    let mut prev_hash = h(b"genesis");

    for (i, turn) in turns.iter().enumerate() {
        let receipt = make_turn_receipt(
            i,
            &turn.role,
            &turn.model,
            &turn.text,
            &turn.timestamp,
            &prev_hash,
        );
        prev_hash = receipt.receipt_hash.clone();
        chain.push(receipt);
    }
    chain
}

/// Verify every link in a chain. Pure.
/// Returns (all_valid, list_of_errors).
pub fn verify_chain(chain: &[TurnReceipt]) -> (bool, Vec<String>) {
    let mut errors = Vec::new();
    let mut prev_hash = h(b"genesis");

    for (i, receipt) in chain.iter().enumerate() {
        // Check prev_receipt_hash
        if receipt.prev_receipt_hash != prev_hash {
            errors.push(format!("Turn {}: prev_hash mismatch", i));
        }

        // Recompute receipt_hash
        let partial = serde_json::json!({
            "schema": receipt.schema,
            "turn_index": receipt.turn_index,
            "role": receipt.role,
            "model": receipt.model,
            "text_hash": receipt.text_hash,
            "text_length": receipt.text_length,
            "timestamp": receipt.timestamp,
            "prev_receipt_hash": receipt.prev_receipt_hash,
        });
        let computed = hash_json(&partial);
        if computed != receipt.receipt_hash {
            errors.push(format!("Turn {}: receipt_hash invalid", i));
        }

        prev_hash = receipt.receipt_hash.clone();
    }

    (errors.is_empty(), errors)
}

// ---------------------------------------------------------------------------
// Merkle tree
// ---------------------------------------------------------------------------

/// Compute Merkle root over a list of hex hashes. Pure.
/// Same hashes → same root, always.
pub fn merkle_root(hashes: &[String]) -> String {
    if hashes.is_empty() {
        return h(b"empty");
    }

    let mut layer: Vec<Vec<u8>> = hashes
        .iter()
        .map(|h| hex::decode(h).expect("invalid hex in merkle_root"))
        .collect();

    while layer.len() > 1 {
        // Pad odd count by duplicating last
        if layer.len() % 2 == 1 {
            layer.push(layer.last().unwrap().clone());
        }
        layer = layer
            .chunks(2)
            .map(|pair| {
                let mut hasher = Sha256::new();
                hasher.update(&pair[0]);
                hasher.update(&pair[1]);
                hasher.finalize().to_vec()
            })
            .collect();
    }

    hex::encode(&layer[0])
}

// ---------------------------------------------------------------------------
// Stamp-based turn chain — the new way
// ---------------------------------------------------------------------------

/// Hash of the core.rs source, computed at build time via include_str!.
/// This is the real fn_hash: proves WHICH version of the transform code ran.
pub fn core_source_hash() -> String {
    h(include_str!("core.rs").as_bytes())
}

/// Hash of the stamp.rs source.
pub fn stamp_source_hash() -> String {
    h(include_str!("stamp.rs").as_bytes())
}

/// Build a stamped turn chain. Each turn becomes a stamp with domain="turn".
/// fn_hash = hash of core.rs source — proves which function version ran.
pub fn build_stamped_turn_chain(turns: &[Turn]) -> Vec<crate::stamp::Stamp> {
    use crate::stamp;

    let fn_hash = core_source_hash();
    let mut chain = Vec::with_capacity(turns.len());
    let mut prev = stamp::genesis();

    for turn in turns {
        let input_hash = hash_turn(&turn.role, &turn.model, &turn.text, &turn.timestamp);
        let output_hash = input_hash.clone();
        let s = stamp::stamp("turn", &input_hash, &fn_hash, &output_hash, &prev);
        prev = s.stamp_hash.clone();
        chain.push(s);
    }
    chain
}

// ---------------------------------------------------------------------------
// Anchors
// ---------------------------------------------------------------------------

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Anchor {
    pub schema: String,
    pub merkle_root: String,
    pub turn_count: usize,
    pub receipt_count: usize,
    pub first_turn_hash: String,
    pub last_turn_hash: String,
}

/// Compute anchor from a legacy turn chain. Pure.
pub fn compute_anchor(chain: &[TurnReceipt]) -> Anchor {
    let receipt_hashes: Vec<String> = chain.iter().map(|r| r.receipt_hash.clone()).collect();
    let root = merkle_root(&receipt_hashes);
    Anchor {
        schema: "sidecar.anchor.v1".into(),
        merkle_root: root,
        turn_count: chain.len(),
        receipt_count: receipt_hashes.len(),
        first_turn_hash: chain.first().map(|r| r.receipt_hash.clone()).unwrap_or_default(),
        last_turn_hash: chain.last().map(|r| r.receipt_hash.clone()).unwrap_or_default(),
    }
}

// ---------------------------------------------------------------------------
// Ledger entries
// ---------------------------------------------------------------------------

/// Hash a ledger entry using canonical JSON. Pure.
pub fn hash_entry(entry: &serde_json::Value) -> String {
    hash_json(entry)
}

/// Compute Merkle root over ledger entries. Pure.
pub fn ledger_anchor(entries: &[serde_json::Value]) -> String {
    let hashes: Vec<String> = entries.iter().map(|e| hash_entry(e)).collect();
    merkle_root(&hashes)
}

/// Verify a ledger chain. Pure.
pub fn verify_ledger(entries: &[serde_json::Value]) -> (bool, Vec<String>) {
    let mut errors = Vec::new();
    let mut prev_hash = h(b"genesis");

    for (i, entry) in entries.iter().enumerate() {
        let claimed_prev = entry
            .get("prev_entry_hash")
            .and_then(|v| v.as_str())
            .unwrap_or("");
        if claimed_prev != prev_hash {
            errors.push(format!("Entry {}: prev_hash mismatch", i));
        }
        prev_hash = hash_entry(entry);
    }

    (errors.is_empty(), errors)
}

/// Build a stamped ledger chain from raw entries.
/// fn_hash = hash of core.rs source — proves which function version ran.
pub fn build_stamped_ledger(entries: &[serde_json::Value]) -> Vec<crate::stamp::Stamp> {
    use crate::stamp;

    let fn_hash = core_source_hash();
    let mut chain = Vec::with_capacity(entries.len());
    let mut prev = stamp::genesis();

    for entry in entries {
        let input_hash = hash_entry(entry);
        let output_hash = input_hash.clone();
        let s = stamp::stamp("ledger", &input_hash, &fn_hash, &output_hash, &prev);
        prev = s.stamp_hash.clone();
        chain.push(s);
    }
    chain
}

// ---------------------------------------------------------------------------
// Ore verification
// ---------------------------------------------------------------------------

/// Verify an ore blob: recompute SHA-256 of raw content, compare to claimed hash. Pure.
pub fn verify_ore(raw_content: &[u8], claimed_hash: &str) -> bool {
    let actual = h(raw_content);
    actual == claimed_hash
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_h_empty() {
        let result = h(b"");
        assert_eq!(
            result,
            "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        );
    }

    #[test]
    fn test_h_genesis() {
        let result = h(b"genesis");
        // Must match Python: hashlib.sha256(b"genesis").hexdigest()
        assert_eq!(
            result,
            "aeebad4a796fcc2e15dc4c6061b45ed9b373f26adfc798ca7d2d8cc58182718e"
        );
    }

    #[test]
    fn test_canonical_json_sorted_keys() {
        let obj = serde_json::json!({"b": 2, "a": 1});
        let result = canonical_json(&obj);
        assert_eq!(result, r#"{"a":1,"b":2}"#);
    }

    #[test]
    fn test_canonical_json_nested() {
        let obj = serde_json::json!({"z": {"b": 2, "a": 1}, "a": [3, 1]});
        let result = canonical_json(&obj);
        assert_eq!(result, r#"{"a":[3,1],"z":{"a":1,"b":2}}"#);
    }

    #[test]
    fn test_hash_turn_deterministic() {
        let h1 = hash_turn("user", "human", "hello", "2026-01-01T00:00:00Z");
        let h2 = hash_turn("user", "human", "hello", "2026-01-01T00:00:00Z");
        assert_eq!(h1, h2);
    }

    #[test]
    fn test_build_chain_genesis() {
        let turns = vec![Turn {
            role: "user".into(),
            model: "human".into(),
            text: "hello".into(),
            timestamp: "2026-01-01T00:00:00Z".into(),
        }];
        let chain = build_chain(&turns);
        assert_eq!(chain.len(), 1);
        assert_eq!(chain[0].prev_receipt_hash, h(b"genesis"));
    }

    #[test]
    fn test_verify_chain_valid() {
        let turns = vec![
            Turn { role: "user".into(), model: "human".into(), text: "hello".into(), timestamp: "t1".into() },
            Turn { role: "assistant".into(), model: "claude".into(), text: "hi there".into(), timestamp: "t2".into() },
        ];
        let chain = build_chain(&turns);
        let (valid, errors) = verify_chain(&chain);
        assert!(valid, "errors: {:?}", errors);
    }

    #[test]
    fn test_verify_chain_tampered() {
        let turns = vec![
            Turn { role: "user".into(), model: "human".into(), text: "hello".into(), timestamp: "t1".into() },
            Turn { role: "assistant".into(), model: "claude".into(), text: "hi".into(), timestamp: "t2".into() },
        ];
        let mut chain = build_chain(&turns);
        chain[1].text_hash = "deadbeef".into();
        let (valid, _) = verify_chain(&chain);
        assert!(!valid);
    }

    #[test]
    fn test_merkle_root_single() {
        let hashes = vec![h(b"one")];
        let root = merkle_root(&hashes);
        assert_eq!(root, h(b"one"));
    }

    #[test]
    fn test_merkle_root_two() {
        let h1 = h(b"one");
        let h2 = h(b"two");
        let root = merkle_root(&vec![h1.clone(), h2.clone()]);
        // Manual: SHA256(decode(h1) || decode(h2))
        let mut hasher = Sha256::new();
        hasher.update(hex::decode(&h1).unwrap());
        hasher.update(hex::decode(&h2).unwrap());
        let expected = hex::encode(hasher.finalize());
        assert_eq!(root, expected);
    }

    #[test]
    fn test_merkle_root_empty() {
        let root = merkle_root(&[]);
        assert_eq!(root, h(b"empty"));
    }

    #[test]
    fn test_merkle_root_odd_pads() {
        // 3 hashes: [a, b, c] → layer1: [H(a||b), H(c||c)] → root: H(H(a||b) || H(c||c))
        let hashes = vec![h(b"a"), h(b"b"), h(b"c")];
        let root = merkle_root(&hashes);
        assert!(!root.is_empty());
        // Verify determinism
        assert_eq!(root, merkle_root(&hashes));
    }

    #[test]
    fn test_verify_ore() {
        let content = b"hello world";
        let hash = h(content);
        assert!(verify_ore(content, &hash));
        assert!(!verify_ore(b"tampered", &hash));
    }

    #[test]
    fn test_ledger_verify_valid() {
        let genesis = h(b"genesis");
        let e1 = serde_json::json!({"prev_entry_hash": genesis, "data": "first"});
        let h1 = hash_entry(&e1);
        let e2 = serde_json::json!({"prev_entry_hash": h1, "data": "second"});
        let (valid, errors) = verify_ledger(&[e1, e2]);
        assert!(valid, "errors: {:?}", errors);
    }

    #[test]
    fn test_ledger_verify_broken() {
        let e1 = serde_json::json!({"prev_entry_hash": h(b"genesis"), "data": "first"});
        let e2 = serde_json::json!({"prev_entry_hash": "wrong", "data": "second"});
        let (valid, _) = verify_ledger(&[e1, e2]);
        assert!(!valid);
    }

    #[test]
    fn test_stamped_turn_chain() {
        let turns = vec![
            Turn { role: "user".into(), model: "human".into(), text: "hello".into(), timestamp: "t1".into() },
            Turn { role: "assistant".into(), model: "claude".into(), text: "hi".into(), timestamp: "t2".into() },
        ];
        let chain = build_stamped_turn_chain(&turns);
        assert_eq!(chain.len(), 2);
        assert_eq!(chain[0].domain, "turn");
        assert_eq!(chain[1].domain, "turn");
        // Verify the stamp chain
        let (valid, errors) = crate::stamp::verify_stamp_chain(&chain);
        assert!(valid, "errors: {:?}", errors);
    }

    #[test]
    fn test_stamped_turn_chain_deterministic() {
        let turns = vec![
            Turn { role: "user".into(), model: "human".into(), text: "test".into(), timestamp: "t1".into() },
        ];
        let c1 = build_stamped_turn_chain(&turns);
        let c2 = build_stamped_turn_chain(&turns);
        assert_eq!(c1[0].stamp_hash, c2[0].stamp_hash);
    }

    #[test]
    fn test_stamped_ledger() {
        let genesis = h(b"genesis");
        let e1 = serde_json::json!({"prev_entry_hash": genesis, "data": "first"});
        let h1 = hash_entry(&e1);
        let e2 = serde_json::json!({"prev_entry_hash": h1, "data": "second"});
        let chain = build_stamped_ledger(&[e1, e2]);
        assert_eq!(chain.len(), 2);
        assert_eq!(chain[0].domain, "ledger");
        let (valid, errors) = crate::stamp::verify_stamp_chain(&chain);
        assert!(valid, "errors: {:?}", errors);
    }
}
