//! I/O layer — file reading, session parsing, CLI output.
//! Thin glue around the pure core. Never makes governance decisions.

use crate::core::{self, Turn, TurnReceipt};
use serde_json::Value;
use std::fs;
use std::path::Path;

// ---------------------------------------------------------------------------
// Ore verification (file I/O wrapper)
// ---------------------------------------------------------------------------

pub fn verify_ore_file(ore_path: &str) -> Result<bool, String> {
    let blob: Value = {
        let data = fs::read_to_string(ore_path).map_err(|e| format!("read ore: {}", e))?;
        serde_json::from_str(&data).map_err(|e| format!("parse ore JSON: {}", e))?
    };

    let raw_path = ore_path.replace(".ore.json", ".raw");
    if !Path::new(&raw_path).exists() {
        return Err(format!("raw file not found: {}", raw_path));
    }

    let content = fs::read(&raw_path).map_err(|e| format!("read raw: {}", e))?;
    let claimed_hash = blob
        .get("content_hash")
        .and_then(|v| v.as_str())
        .ok_or("missing content_hash field")?;
    let claimed_size = blob.get("content_size").and_then(|v| v.as_u64()).unwrap_or(0);

    let actual_hash = core::h(&content);
    let pass = actual_hash == claimed_hash;

    if pass {
        println!("PASS: {}", Path::new(ore_path).file_name().unwrap().to_string_lossy());
        println!("  hash: {}", actual_hash);
        println!("  size: {} bytes (claimed: {})", content.len(), claimed_size);
    } else {
        println!("FAIL: hash mismatch!");
        println!("  claimed: {}", claimed_hash);
        println!("  actual:  {}", actual_hash);
    }
    Ok(pass)
}

// ---------------------------------------------------------------------------
// Turn extraction from OpenClaw JSONL
// ---------------------------------------------------------------------------

pub fn extract_turns_from_session(session_path: &str) -> Result<Vec<Turn>, String> {
    let data = fs::read_to_string(session_path).map_err(|e| format!("read session: {}", e))?;
    let mut turns = Vec::new();
    let mut current_model = "unknown".to_string();

    for line in data.lines() {
        let line = line.trim();
        if line.is_empty() {
            continue;
        }
        let obj: Value = match serde_json::from_str(line) {
            Ok(v) => v,
            Err(_) => continue,
        };

        // Track model changes
        if obj.get("type").and_then(|v| v.as_str()) == Some("model_change") {
            if let Some(m) = obj.get("modelId").and_then(|v| v.as_str()) {
                current_model = m.to_string();
            }
            continue;
        }
        if obj.get("type").and_then(|v| v.as_str()) == Some("custom")
            && obj.get("customType").and_then(|v| v.as_str()) == Some("model-snapshot")
        {
            if let Some(m) = obj.get("data").and_then(|d| d.get("modelId")).and_then(|v| v.as_str()) {
                current_model = m.to_string();
            }
            continue;
        }

        // Only message types
        if obj.get("type").and_then(|v| v.as_str()) != Some("message") {
            continue;
        }

        let msg = match obj.get("message") {
            Some(m) => m,
            None => continue,
        };

        let role = match msg.get("role").and_then(|v| v.as_str()) {
            Some(r) if r == "user" || r == "assistant" => r,
            _ => continue,
        };

        // Extract text from content (string or array of blocks)
        let text = match msg.get("content") {
            Some(Value::String(s)) => s.clone(),
            Some(Value::Array(arr)) => {
                let parts: Vec<&str> = arr
                    .iter()
                    .filter_map(|b| {
                        if b.get("type").and_then(|v| v.as_str()) == Some("text") {
                            b.get("text").and_then(|v| v.as_str())
                        } else {
                            None
                        }
                    })
                    .collect();
                parts.join(" ")
            }
            _ => continue,
        };

        let text = text.trim().to_string();
        if text.len() < 5 {
            continue;
        }

        let timestamp = obj
            .get("timestamp")
            .and_then(|v| v.as_str())
            .unwrap_or("")
            .to_string();

        let model = if role == "assistant" {
            current_model.clone()
        } else {
            "human".to_string()
        };

        turns.push(Turn {
            role: role.to_string(),
            model,
            text,
            timestamp,
        });
    }
    Ok(turns)
}

// ---------------------------------------------------------------------------
// Turn chain file I/O
// ---------------------------------------------------------------------------

pub fn load_chain(chain_path: &str) -> Result<Vec<TurnReceipt>, String> {
    let data = fs::read_to_string(chain_path).map_err(|e| format!("read chain: {}", e))?;
    let mut chain = Vec::new();
    for line in data.lines() {
        let line = line.trim();
        if line.is_empty() {
            continue;
        }
        let receipt: TurnReceipt =
            serde_json::from_str(line).map_err(|e| format!("parse receipt: {}", e))?;
        chain.push(receipt);
    }
    Ok(chain)
}

pub fn save_chain(chain: &[TurnReceipt], chain_path: &str) -> Result<(), String> {
    let parent = Path::new(chain_path).parent().unwrap();
    fs::create_dir_all(parent).map_err(|e| format!("mkdir: {}", e))?;

    let mut out = String::new();
    for receipt in chain {
        let line = serde_json::to_string(receipt).map_err(|e| format!("serialize: {}", e))?;
        out.push_str(&line);
        out.push('\n');
    }
    fs::write(chain_path, out).map_err(|e| format!("write chain: {}", e))?;
    Ok(())
}

// ---------------------------------------------------------------------------
// Ledger file I/O
// ---------------------------------------------------------------------------

pub fn ledger_path() -> String {
    std::env::var("SUBSTRATE_LEDGER_PATH")
        .unwrap_or_else(|_| {
            let ore = ore_dir();
            format!("{}/ledger.jsonl", ore)
        })
}

pub fn ore_dir() -> String {
    std::env::var("SUBSTRATE_ORE_DIR")
        .unwrap_or_else(|_| "/Users/Shared/sidecar-ore".to_string())
}

pub fn chain_dir() -> String {
    let ore = ore_dir();
    format!("{}/turn-chains", ore)
}

pub fn read_ledger() -> Result<Vec<Value>, String> {
    let lp = ledger_path();
    let path = Path::new(&lp);
    if !path.exists() {
        return Ok(Vec::new());
    }
    let data = fs::read_to_string(path).map_err(|e| format!("read ledger: {}", e))?;
    let mut entries = Vec::new();
    for line in data.lines() {
        let line = line.trim();
        if line.is_empty() {
            continue;
        }
        let entry: Value =
            serde_json::from_str(line).map_err(|e| format!("parse ledger entry: {}", e))?;
        entries.push(entry);
    }
    Ok(entries)
}

// ---------------------------------------------------------------------------
// Stamp chain file I/O
// ---------------------------------------------------------------------------

pub fn save_stamp_chain(chain: &[crate::stamp::Stamp], chain_path: &str) -> Result<(), String> {
    let parent = Path::new(chain_path).parent().unwrap();
    fs::create_dir_all(parent).map_err(|e| format!("mkdir: {}", e))?;

    let mut out = String::new();
    for s in chain {
        let line = serde_json::to_string(s).map_err(|e| format!("serialize stamp: {}", e))?;
        out.push_str(&line);
        out.push('\n');
    }
    fs::write(chain_path, out).map_err(|e| format!("write stamp chain: {}", e))?;
    Ok(())
}

pub fn load_stamp_chain(chain_path: &str) -> Result<Vec<crate::stamp::Stamp>, String> {
    let data = fs::read_to_string(chain_path).map_err(|e| format!("read stamp chain: {}", e))?;
    let mut chain = Vec::new();
    for line in data.lines() {
        let line = line.trim();
        if line.is_empty() {
            continue;
        }
        let s: crate::stamp::Stamp = serde_json::from_str(line)
            .map_err(|e| format!("parse stamp: {}", e))?;
        chain.push(s);
    }
    Ok(chain)
}

// ---------------------------------------------------------------------------
// Anchor file I/O
// ---------------------------------------------------------------------------

pub fn save_anchor_json(anchor: &core::Anchor, path: &str) -> Result<(), String> {
    let json = serde_json::to_string_pretty(anchor).map_err(|e| format!("serialize anchor: {}", e))?;
    fs::write(path, json).map_err(|e| format!("write anchor: {}", e))?;
    Ok(())
}
