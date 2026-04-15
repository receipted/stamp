mod core;
mod io;
mod stamp;

use clap::{Parser, Subcommand};

#[derive(Parser)]
#[command(name = "substrate")]
#[command(about = "Receipted substrate: stamped semantic transforms with portable proof")]
struct Cli {
    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand)]
enum Commands {
    /// Verify an ore blob's content hash
    Verify {
        /// Path to the .ore.json file
        ore_path: String,
    },

    /// Stamp operations — the generic primitive
    #[command(subcommand)]
    Stamp(StampCmd),

    /// Turn chain operations (legacy + stamped)
    #[command(subcommand)]
    TurnChain(TurnChainCmd),

    /// Ledger operations
    #[command(subcommand)]
    Ledger(LedgerCmd),

    /// Show system info
    Info,
}

#[derive(Subcommand)]
enum StampCmd {
    /// Mint a stamp from explicit hashes
    Mint {
        /// Domain label (e.g. turn, sieve, intent, care)
        domain: String,
        /// SHA-256 hash of the input
        input_hash: String,
        /// SHA-256 hash of the function/binary that ran
        fn_hash: String,
        /// SHA-256 hash of the output
        output_hash: String,
        /// SHA-256 hash of the previous stamp (or "genesis")
        #[arg(long, default_value = "genesis")]
        prev: String,
    },
    /// Verify a stamp's self-hash
    VerifyOne {
        /// JSON stamp (inline or @file)
        stamp_json: String,
    },
}

#[derive(Subcommand)]
enum TurnChainCmd {
    /// Build a stamped turn chain from an OpenClaw session JSONL
    Build {
        /// Path to session .jsonl file
        session_path: String,
        /// Output path for the chain (default: auto-named in turn-chains dir)
        #[arg(short, long)]
        output: Option<String>,
        /// Use legacy TurnReceipt format instead of generic stamps
        #[arg(long)]
        legacy: bool,
    },
    /// Verify an existing turn chain (supports both legacy and stamp format)
    Verify {
        /// Path to .turn-chain.jsonl file
        chain_path: String,
    },
    /// Show summary of a session's turns
    Summary {
        /// Path to session .jsonl file
        session_path: String,
    },
    /// Compute and display the Merkle anchor for a chain
    Anchor {
        /// Path to .turn-chain.jsonl file
        chain_path: String,
    },
}

#[derive(Subcommand)]
enum LedgerCmd {
    /// Verify the entire ledger chain
    Verify,
    /// Show ledger status
    Status,
    /// Compute and display the current Merkle root
    Anchor,
}

fn main() {
    let cli = Cli::parse();

    match cli.command {
        // ── Verify ore ──
        Commands::Verify { ore_path } => {
            match io::verify_ore_file(&ore_path) {
                Ok(true) => std::process::exit(0),
                Ok(false) => std::process::exit(1),
                Err(e) => {
                    eprintln!("ERROR: {}", e);
                    std::process::exit(1);
                }
            }
        }

        // ── Stamp (generic primitive) ──
        Commands::Stamp(cmd) => match cmd {
            StampCmd::Mint { domain, input_hash, fn_hash, output_hash, prev } => {
                let prev_hash = if prev == "genesis" {
                    stamp::genesis()
                } else {
                    prev
                };
                let s = stamp::stamp(&domain, &input_hash, &fn_hash, &output_hash, &prev_hash);
                println!("{}", serde_json::to_string_pretty(&s).unwrap());
            }

            StampCmd::VerifyOne { stamp_json } => {
                let json_str = if stamp_json.starts_with('@') {
                    std::fs::read_to_string(&stamp_json[1..]).unwrap_or_else(|e| {
                        eprintln!("ERROR: {}", e);
                        std::process::exit(1);
                    })
                } else {
                    stamp_json
                };
                let s: stamp::Stamp = serde_json::from_str(&json_str).unwrap_or_else(|e| {
                    eprintln!("ERROR: invalid stamp JSON: {}", e);
                    std::process::exit(1);
                });
                if stamp::verify_stamp(&s) {
                    println!("PASS: stamp valid");
                    println!("  domain:     {}", s.domain);
                    println!("  stamp_hash: {}", s.stamp_hash);
                } else {
                    println!("FAIL: stamp_hash does not match fields");
                    std::process::exit(1);
                }
            }
        },

        // ── Turn chain ──
        Commands::TurnChain(cmd) => match cmd {
            TurnChainCmd::Build { session_path, output, legacy } => {
                let turns = match io::extract_turns_from_session(&session_path) {
                    Ok(t) => t,
                    Err(e) => {
                        eprintln!("ERROR: {}", e);
                        std::process::exit(1);
                    }
                };
                println!("Session: {}", std::path::Path::new(&session_path).file_name().unwrap().to_string_lossy());
                println!("  Turns extracted: {}", turns.len());

                if turns.is_empty() {
                    eprintln!("  ERROR: no turns found");
                    std::process::exit(1);
                }

                // Model distribution
                let mut models = std::collections::HashMap::new();
                for t in &turns {
                    *models.entry(t.model.clone()).or_insert(0usize) += 1;
                }
                println!("  Models: {:?}", models);

                let chain_dir = io::chain_dir();
                let session_id: String = std::path::Path::new(&session_path)
                    .file_stem()
                    .unwrap()
                    .to_string_lossy()
                    .chars()
                    .take(16)
                    .collect();

                if legacy {
                    // Legacy TurnReceipt path (for backward compat with existing data)
                    let chain = core::build_chain(&turns);
                    println!("  Chain built: {} receipts (legacy)", chain.len());
                    let anchor = core::compute_anchor(&chain);
                    println!("  Merkle root: {}", anchor.merkle_root);

                    let chain_path = output.unwrap_or_else(|| {
                        format!("{}/{}.turn-chain.jsonl", chain_dir, session_id)
                    });
                    if let Err(e) = io::save_chain(&chain, &chain_path) {
                        eprintln!("ERROR: {}", e);
                        std::process::exit(1);
                    }
                    println!("  Final hash: {}...", &chain.last().unwrap().receipt_hash[..32]);
                    println!("  Chain saved: {}", chain_path);
                } else {
                    // Stamp path (canonical)
                    let stamps = core::build_stamped_turn_chain(&turns);
                    println!("  Chain built: {} stamps (canonical)", stamps.len());

                    let root = stamp::stamp_chain_anchor(&stamps);
                    println!("  Merkle root: {}", root);
                    println!("  fn_hash: {}...", &core::core_source_hash()[..32]);

                    let chain_path = output.unwrap_or_else(|| {
                        format!("{}/{}.stamp-chain.jsonl", chain_dir, session_id)
                    });
                    if let Err(e) = io::save_stamp_chain(&stamps, &chain_path) {
                        eprintln!("ERROR: {}", e);
                        std::process::exit(1);
                    }
                    println!("  Final stamp: {}...", &stamps.last().unwrap().stamp_hash[..32]);
                    println!("  Chain saved: {}", chain_path);
                }
            }

            TurnChainCmd::Verify { chain_path } => {
                // Try stamp format first, fall back to legacy
                if let Ok(stamps) = io::load_stamp_chain(&chain_path) {
                    let (valid, errors) = stamp::verify_stamp_chain(&stamps);
                    if valid {
                        println!("PASS: stamp chain intact ({} stamps)", stamps.len());
                        if let Some(last) = stamps.last() {
                            println!("  Final stamp: {}...", &last.stamp_hash[..32]);
                        }
                        let root = stamp::stamp_chain_anchor(&stamps);
                        println!("  Merkle root: {}", root);
                    } else {
                        println!("FAIL: {} error(s)", errors.len());
                        for e in &errors { println!("  {}", e); }
                        std::process::exit(1);
                    }
                } else if let Ok(chain) = io::load_chain(&chain_path) {
                    // Legacy TurnReceipt format
                    let (valid, errors) = core::verify_chain(&chain);
                    if valid {
                        println!("PASS: chain intact ({} turns, legacy format)", chain.len());
                        if let Some(last) = chain.last() {
                            println!("  Final hash: {}...", &last.receipt_hash[..32]);
                        }
                        let anchor = core::compute_anchor(&chain);
                        println!("  Merkle root: {}", anchor.merkle_root);
                    } else {
                        println!("FAIL: {} error(s)", errors.len());
                        for e in &errors { println!("  {}", e); }
                        std::process::exit(1);
                    }
                } else {
                    eprintln!("ERROR: could not parse as stamp chain or legacy chain");
                    std::process::exit(1);
                }
            }

            TurnChainCmd::Summary { session_path } => {
                let turns = match io::extract_turns_from_session(&session_path) {
                    Ok(t) => t,
                    Err(e) => {
                        eprintln!("ERROR: {}", e);
                        std::process::exit(1);
                    }
                };
                println!("Session: {}", std::path::Path::new(&session_path).file_name().unwrap().to_string_lossy());
                println!("Total turns: {}", turns.len());
                let mut models = std::collections::HashMap::new();
                for t in &turns {
                    *models.entry(t.model.clone()).or_insert(0usize) += 1;
                }
                println!("Models:");
                let mut sorted: Vec<_> = models.into_iter().collect();
                sorted.sort_by(|a, b| b.1.cmp(&a.1));
                for (model, count) in sorted {
                    println!("  {}: {} turns", model, count);
                }
            }

            TurnChainCmd::Anchor { chain_path } => {
                // Try stamp format first
                if let Ok(stamps) = io::load_stamp_chain(&chain_path) {
                    let root = stamp::stamp_chain_anchor(&stamps);
                    println!("{}", serde_json::json!({
                        "schema": "substrate.anchor.v1",
                        "stamp_count": stamps.len(),
                        "merkle_root": root,
                        "fn_hash": core::core_source_hash(),
                    }));
                } else if let Ok(chain) = io::load_chain(&chain_path) {
                    let anchor = core::compute_anchor(&chain);
                    println!("{}", serde_json::to_string_pretty(&anchor).unwrap());
                } else {
                    eprintln!("ERROR: could not parse chain file");
                    std::process::exit(1);
                }
            }
        },

        // ── Ledger ──
        Commands::Ledger(cmd) => match cmd {
            LedgerCmd::Verify => {
                let entries = match io::read_ledger() {
                    Ok(e) => e,
                    Err(e) => {
                        eprintln!("ERROR: {}", e);
                        std::process::exit(1);
                    }
                };
                if entries.is_empty() {
                    println!("Ledger is empty.");
                    return;
                }
                println!("Verifying {} entries...", entries.len());
                let (valid, errors) = core::verify_ledger(&entries);
                if valid {
                    println!("PASS: chain intact ({} entries)", entries.len());
                } else {
                    println!("FAIL: {} broken link(s)", errors.len());
                    for e in &errors { println!("  {}", e); }
                }
                let root = core::ledger_anchor(&entries);
                println!("  Merkle root: {}", root);
            }

            LedgerCmd::Status => {
                let entries = match io::read_ledger() {
                    Ok(e) => e,
                    Err(e) => {
                        eprintln!("ERROR: {}", e);
                        std::process::exit(1);
                    }
                };
                println!("Ledger: {}", io::ledger_path());
                println!("Entries: {}", entries.len());
                if !entries.is_empty() {
                    if let Some(first_at) = entries.first().and_then(|e| e.get("appended_at")).and_then(|v| v.as_str()) {
                        println!("First:  {}", first_at);
                    }
                    if let Some(last_at) = entries.last().and_then(|e| e.get("appended_at")).and_then(|v| v.as_str()) {
                        println!("Last:   {}", last_at);
                    }
                    let root = core::ledger_anchor(&entries);
                    println!("Merkle root: {}", root);
                }
            }

            LedgerCmd::Anchor => {
                let entries = match io::read_ledger() {
                    Ok(e) => e,
                    Err(e) => {
                        eprintln!("ERROR: {}", e);
                        std::process::exit(1);
                    }
                };
                let root = core::ledger_anchor(&entries);
                println!("{}", serde_json::json!({
                    "schema": "sidecar.anchor.v1",
                    "entry_count": entries.len(),
                    "merkle_root": root,
                }));
            }
        },

        // ── Info ──
        Commands::Info => {
            println!("substrate v{}", env!("CARGO_PKG_VERSION"));
            println!("  core.rs hash:  {}...", &core::core_source_hash()[..32]);
            println!("  stamp.rs hash: {}...", &core::stamp_source_hash()[..32]);
            println!("  stamp schema:  substrate.stamp.v1");
        }
    }
}
