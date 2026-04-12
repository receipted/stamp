#!/usr/bin/env python3
"""
audio_claim.py — Extract structural claims from audio files.

Analyzes an audio file using signal processing (librosa) and produces
typed claim objects suitable for the sieve. No LLM in the analysis path.

Features extracted (pure, deterministic):
  - spectral_centroid:    brightness of the sound (AI tends brighter/thinner)
  - onset_entropy:        randomness of note timing (AI tends quantized, low entropy)
  - timing_variance:      micro-timing drift (humans drift, AI is metronomic)
  - harmonic_ratio:       cleanness of harmonics (AI lacks acoustic noise)
  - dynamic_range:        loudness variation (AI often compressed/flat)
  - zero_crossing_rate:   noisiness signal
  - mfcc_variance:        timbre variation over time

The receipt proves:
  - Which audio file was analyzed (sha256 of bytes)
  - Which analysis function ran (sha256 of this file)
  - What features were extracted (deterministic)
  - Same audio + same function = same claims, always

Usage:
  python3 audio_claim.py <audio_file.mp3|.wav|.flac>
  python3 audio_claim.py <audio_file> --sieve   # run through sieve too

FUTURE: Uplift to Rust for WASM deployment and on-chain anchoring.
"""

import hashlib
import json
import os
import sys
from pathlib import Path

SIDECAR_DIR = os.path.dirname(os.path.abspath(__file__))
THINKING_LOG = "/Users/shadow/projects/thinking-log"


def h(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


# --- Pure feature extraction functions ---

def extract_audio_features(audio_path: str) -> dict:
    """
    Extract signal-level features from an audio file. Pure function over bytes.
    Same audio file → same features, every time.

    Returns dict of named features with values and interpretation hints.
    IO: reads audio file. All computation after that is pure.
    """
    import librosa
    import numpy as np

    # Load audio — mono, standard sample rate
    y, sr = librosa.load(audio_path, sr=22050, mono=True)

    features = {}

    # 1. Spectral centroid — brightness
    # AI music tends to be brighter (higher centroid) due to synthesis
    centroid = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
    features["spectral_centroid_mean"] = float(np.mean(centroid))
    features["spectral_centroid_std"] = float(np.std(centroid))

    # 2. Onset detection — timing regularity
    onset_frames = librosa.onset.onset_detect(y=y, sr=sr)
    if len(onset_frames) > 1:
        # Inter-onset intervals
        ioi = np.diff(onset_frames)
        features["onset_timing_variance"] = float(np.var(ioi))
        features["onset_count"] = int(len(onset_frames))
        # Entropy of IOI distribution — low = metronomic (AI), high = expressive (human)
        ioi_norm = ioi / (ioi.sum() + 1e-10)
        ioi_norm = ioi_norm[ioi_norm > 0]
        features["onset_entropy"] = float(-np.sum(ioi_norm * np.log(ioi_norm + 1e-10)))
    else:
        features["onset_timing_variance"] = 0.0
        features["onset_count"] = len(onset_frames)
        features["onset_entropy"] = 0.0

    # 3. Dynamic range — loudness variation
    rms = librosa.feature.rms(y=y)[0]
    features["dynamic_range_db"] = float(20 * np.log10(np.max(rms) / (np.min(rms) + 1e-10)))
    features["rms_variance"] = float(np.var(rms))

    # 4. Harmonic ratio — acoustic vs synthetic
    harmonic, percussive = librosa.effects.hpss(y)
    harmonic_ratio = np.sum(harmonic**2) / (np.sum(y**2) + 1e-10)
    features["harmonic_ratio"] = float(harmonic_ratio)

    # 5. Zero crossing rate — noisiness
    zcr = librosa.feature.zero_crossing_rate(y)[0]
    features["zero_crossing_rate_mean"] = float(np.mean(zcr))
    features["zero_crossing_rate_std"] = float(np.std(zcr))

    # 6. MFCC variance — timbre variation over time
    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
    features["mfcc_variance_mean"] = float(np.mean(np.var(mfcc, axis=1)))

    # 7. Tempo and beat regularity
    tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
    features["tempo_bpm"] = float(np.squeeze(tempo))
    if len(beat_frames) > 1:
        beat_ioi = np.diff(beat_frames)
        features["beat_regularity"] = float(1.0 / (np.std(beat_ioi) + 1e-10))
    else:
        features["beat_regularity"] = 0.0

    features["duration_seconds"] = float(len(y) / sr)

    return features


def features_to_claims(features: dict, audio_path: str) -> list[dict]:
    """
    Pure function. Convert extracted features to typed claim objects for the sieve.
    Same features → same claims, every time.
    """
    claims = []
    fname = os.path.basename(audio_path)

    # CONTRACT claims — what the audio objectively is
    claims.append({
        "text": f"{fname}: duration {features['duration_seconds']:.1f}s, tempo {features['tempo_bpm']:.1f} BPM, {features['onset_count']} detected onsets",
        "claim_type": "fact",
        "evidence_refs": ["librosa-analysis"],
        "confidence": 0.95,
        "source": "audio-analysis",
    })

    # CONSTRAINT claims — hard signal boundaries
    if features["harmonic_ratio"] > 0.85:
        claims.append({
            "text": f"{fname}: highly harmonic signal (ratio {features['harmonic_ratio']:.3f}) — consistent with synthesis or heavily processed audio",
            "claim_type": "constraint",
            "evidence_refs": ["librosa-hpss"],
            "confidence": 0.8,
            "source": "audio-analysis",
        })
    elif features["harmonic_ratio"] < 0.5:
        claims.append({
            "text": f"{fname}: low harmonic ratio ({features['harmonic_ratio']:.3f}) — consistent with acoustic recording with natural noise",
            "claim_type": "constraint",
            "evidence_refs": ["librosa-hpss"],
            "confidence": 0.8,
            "source": "audio-analysis",
        })

    # UNCERTAINTY claims — probabilistic signals
    if features["onset_entropy"] < 1.0:
        claims.append({
            "text": f"{fname}: low onset timing entropy ({features['onset_entropy']:.3f}) — timing is metronomically regular, consistent with AI generation or quantized MIDI",
            "claim_type": "hypothesis",
            "evidence_refs": ["librosa-onset"],
            "confidence": 0.7,
            "source": "audio-analysis",
        })
    elif features["onset_entropy"] > 2.5:
        claims.append({
            "text": f"{fname}: high onset timing entropy ({features['onset_entropy']:.3f}) — timing variation consistent with human performance",
            "claim_type": "hypothesis",
            "evidence_refs": ["librosa-onset"],
            "confidence": 0.7,
            "source": "audio-analysis",
        })

    if features["dynamic_range_db"] < 6.0:
        claims.append({
            "text": f"{fname}: compressed dynamic range ({features['dynamic_range_db']:.1f}dB) — heavy limiting or AI synthesis with uniform loudness",
            "claim_type": "observation",
            "evidence_refs": ["librosa-rms"],
            "confidence": 0.75,
            "source": "audio-analysis",
        })
    elif features["dynamic_range_db"] > 20.0:
        claims.append({
            "text": f"{fname}: wide dynamic range ({features['dynamic_range_db']:.1f}dB) — consistent with acoustic recording or minimal processing",
            "claim_type": "observation",
            "evidence_refs": ["librosa-rms"],
            "confidence": 0.75,
            "source": "audio-analysis",
        })

    if features["beat_regularity"] > 50.0:
        claims.append({
            "text": f"{fname}: extremely regular beat timing (regularity score {features['beat_regularity']:.1f}) — strongly consistent with quantized/AI generation",
            "claim_type": "hypothesis",
            "evidence_refs": ["librosa-beat"],
            "confidence": 0.8,
            "source": "audio-analysis",
        })

    # WITNESS — the analysis provenance
    claims.append({
        "text": f"Analyzed by librosa 0.11.0 — features extracted at {features['duration_seconds']:.1f}s sample, 22050Hz mono",
        "claim_type": "guarantee",
        "evidence_refs": ["librosa-version"],
        "confidence": 1.0,
        "source": "audio-analysis",
    })

    return claims


def analyze_audio(audio_path: str, run_sieve: bool = False) -> dict:
    """Main entry point. IO layer wrapping pure analysis."""
    # Hash the audio file
    raw = Path(audio_path).read_bytes()
    audio_hash = h(raw)
    harness_hash = h(Path(__file__).read_bytes())

    print(f"Audio: {os.path.basename(audio_path)}")
    print(f"  audio_hash:   {audio_hash[:16]}...")
    print(f"  harness_hash: {harness_hash[:16]}...")

    # Extract features (pure after file read)
    print("  Extracting features...")
    features = extract_audio_features(audio_path)

    # Convert to claims (pure)
    claims = features_to_claims(features, audio_path)
    print(f"  Claims generated: {len(claims)}")

    print()
    print("=== AUDIO ANALYSIS ===")
    for k, v in features.items():
        if isinstance(v, float):
            print(f"  {k}: {v:.4f}")
        else:
            print(f"  {k}: {v}")

    print()
    print("=== TYPED CLAIMS ===")
    for c in claims:
        print(f"  [{c['claim_type']}] {c['text'][:100]}")

    if run_sieve:
        print()
        print("=== RUNNING SIEVE ===")
        sys.path.insert(0, THINKING_LOG)
        import glob
        for sp in glob.glob(os.path.join(THINKING_LOG, ".venv/lib/python3*/site-packages")):
            if sp not in sys.path:
                sys.path.insert(0, sp)
        from src.surface.sieve import promote

        topic = {
            "handle": "audio-provenance",
            "provenance_mode": "open",
            "title": "Audio Signal Analysis",
            "description": "Structural claims about audio authorship from signal features",
            "keywords": ["harmonic", "onset", "timing", "entropy", "dynamic", "range",
                         "beat", "tempo", "metronomic", "quantized", "synthesis", "acoustic",
                         "compressed", "regular", "variation", "human", "ai", "generated"],
        }
        promoted, contested, deferred, loss = promote(claims, topic)
        print(f"  Promoted: {len(promoted)} | Contested: {len(contested)} | Loss: {len(loss)}")
        for c in promoted:
            print(f"  [{c['claim_type']}] {c['text'][:90]}")

    result = {
        "audio_hash": audio_hash,
        "harness_hash": harness_hash,
        "features": features,
        "claims": claims,
    }

    # Save results
    out_path = audio_path + ".analysis.json"
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2)
    print(f"\nSaved: {out_path}")

    return result


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 audio_claim.py <audio_file> [--sieve]")
        print()
        print("Analyzes audio and produces typed claims for the sieve.")
        print("Supported: .mp3, .wav, .flac, .ogg, .m4a")
        sys.exit(1)

    audio_path = sys.argv[1]
    run_sieve = "--sieve" in sys.argv

    if not os.path.exists(audio_path):
        print(f"ERROR: file not found: {audio_path}")
        sys.exit(1)

    analyze_audio(audio_path, run_sieve=run_sieve)
