# CONTEXT.md — System Architecture & Intent

> **Canonical reference document for the Portfolio Intelligence System.**  
> Last updated: 2026-02-01

---

## 1. What This Branch Is

This is the **final working backend** for an AI-powered portfolio intelligence system.

**Branch:** `feature/alpaca-live-data-clean`

**Capabilities:**

- Demo portfolio profiles (hardcoded, deterministic)
- Real Alpaca paper trading data (READ-ONLY)
- Mock data for development/testing

**Designed for:**

- Hackathon demonstration
- Portfolio intelligence and advisory
- **NOT** trade execution

**Key Constraint:**  
This system provides **recommendations**, not **automated trading**.  
All execution is disabled. This is intentional.

---

## 2. System Philosophy (WHY It Exists)

### Core Principles

| Principle | Meaning |
|-----------|---------|
| **Portfolio-first** | We optimize the entire portfolio, not individual trades |
| **Safety over aggressiveness** | Capital preservation > capital growth |
| **Explainability** | Every decision has a human-readable reason |
| **No forced trades** | Inaction is a valid decision |
| **Transparency** | Demo behavior is always clearly labeled |

### Design Philosophy

This system was built with the understanding that:

1. **Markets are unpredictable** — The system doesn't predict; it reacts.
2. **Intelligence ≠ Complexity** — Simple rules, applied consistently, outperform clever hacks.
3. **Trust requires honesty** — The system never hides what it's doing or why.
4. **Safety gates exist for a reason** — Guardrails cannot be bypassed.

---

## 3. High-Level Architecture (HOW It Works)

```
┌─────────────────────────────────────────────────────────────────────┐
│                    PORTFOLIO INTELLIGENCE SYSTEM                     │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│   ┌────────────┐    ┌────────────┐    ┌────────────┐                │
│   │  PHASE 1   │───▶│  PHASE 2   │───▶│  PHASE 3   │                │
│   │  INGEST    │    │  SIGNALS   │    │  DECISIONS │                │
│   └────────────┘    └────────────┘    └────────────┘                │
│         │                 │                 │                        │
│         ▼                 ▼                 ▼                        │
│   ┌────────────┐    ┌────────────┐    ┌────────────┐                │
│   │ Portfolio  │    │ Volatility │    │  Actions   │                │
│   │ Positions  │    │ News Score │    │ + Reasons  │                │
│   │ Candidates │    │ Confidence │    │            │                │
│   └────────────┘    └────────────┘    └────────────┘                │
│                                              │                        │
│                                              ▼                        │
│                           ┌─────────────────────────────┐            │
│                           │   PHASE 4: RISK GUARDRAILS  │            │
│                           │   (Concentration, Cash,     │            │
│                           │    Volatility Guards)       │            │
│                           └─────────────────────────────┘            │
│                                              │                        │
│                                              ▼                        │
│                           ┌─────────────────────────────┐            │
│                           │  PHASE 5: EXECUTION PLAN    │            │
│                           │  (Advisory Only - No Exec)  │            │
│                           └─────────────────────────────┘            │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘
```

### Phase Breakdown

| Phase | Module(s) | Input | Output |
|-------|-----------|-------|--------|
| **Phase 1: Data Ingestion** | `broker/*.py`, `demo/demo_profiles.py` | API credentials, profile name | Portfolio state, positions, candidates |
| **Phase 2: Signal Intelligence** | `volatility_metrics.py`, `news_scorer.py`, `sector_confidence.py` | Candles, headlines | ATR, volatility state, news score, sector confidence |
| **Phase 3: Decision Synthesis** | `decision_engine.py`, `position_vitals.py`, `concentration_guard.py` | Signals + positions | Proposed actions with reasons |
| **Phase 4: Risk Guardrails** | `risk_guardrails.py` | Proposed actions + context | Allowed vs blocked actions |
| **Phase 5: Execution Planning** | `execution_planner.py`, `execution_summary.py` | Safe actions | Sequential plan (advisory) |

### Why Phases Are Isolated

- **Testability:** Each phase can be validated independently
- **Debuggability:** Errors are traceable to a specific phase
- **Extensibility:** New signal types or guardrails can be added without touching other phases
- **Clarity:** Engineers can understand one phase at a time

---

## 4. Data Sources & Modes

The system supports three data modes, controlled by environment variables:

| Mode | `DEMO_MODE` | `USE_ALPACA` | Portfolio Source | Market Data | Execution |
|------|-------------|--------------|------------------|-------------|-----------|
| **DEMO** | `true` | ignored | Hardcoded profiles | Simulated | ❌ Disabled |
| **MOCK** | `false` | `false` | Mock adapter | Simulated | ❌ Disabled |
| **ALPACA** | `false` | `true` | Alpaca Paper API | Real (with fallback) | ❌ Disabled |

### Alpaca Integration

**Endpoints Used (READ-ONLY):**

- `GET /v2/account` — Portfolio equity, cash
- `GET /v2/positions` — Current holdings

**Security Constraints:**

- Only paper trading URL allowed (`https://paper-api.alpaca.markets`)
- Credentials from environment variables only
- No write operations (no orders, no modifications)

### Demo Mode

Demo mode is **intentional and transparent**. When enabled:

1. A `RUN CONFIGURATION` block prints at startup
2. The profile name and source are clearly labeled
3. This is not a workaround — it's a feature for reliable demonstrations

---

## 5. Demo Profiles (WHAT They Prove)

Each profile demonstrates a different system capability:

| Profile | Capital | Cash | Description | Expected Behavior |
|---------|---------|------|-------------|-------------------|
| **BALANCED_TECH** | $500k | $75k (15%) | Healthy, diversified | Mostly HOLD/MAINTAIN |
| **OVERCONCENTRATED_TECH** | $1M | $35k (3.5%) | 82% in TECH | TRIM_RISK, BLOCK_RISK, concentration alerts |
| **LOSING_PORTFOLIO** | $750k | $50k | 4 losing positions | RISK_OFF posture, REDUCE actions |
| **ROTATION_SCENARIO** | $800k | $120k | TECH declining, ENERGY rising | FREE_CAPITAL → reallocation |
| **CASH_HEAVY** | $500k | $200k (40%) | High idle cash | Shows why we *don't* deploy capital |

### Key Insight

Each profile answers a question:

- Can the system recognize concentration risk? → **OVERCONCENTRATED_TECH**
- Can the system protect capital during losses? → **LOSING_PORTFOLIO**
- Can the system identify sector rotation? → **ROTATION_SCENARIO**
- Can the system resist deploying capital when conditions don't justify it? → **CASH_HEAVY**

---

## 6. Decision & Explainability Flow

### How Signals Become Decisions

```
Signals (Vol, News, Confidence)
         │
         ▼
┌──────────────────────┐
│ Market Posture Logic │  → BULLISH / NEUTRAL / RISK_OFF
└──────────────────────┘
         │
         ▼
┌──────────────────────┐
│ Position Vitals      │  → Score each position (0-100)
└──────────────────────┘
         │
         ▼
┌──────────────────────┐
│ Action Assignment    │  → HOLD, TRIM, REDUCE, ALLOCATE, etc.
└──────────────────────┘
         │
         ▼
┌──────────────────────┐
│ Reason Attachment    │  → 1-3 reasons per decision
└──────────────────────┘
```

### Explainability Contract

Every decision includes:

- `action`: What to do (HOLD, REDUCE, ALLOCATE, etc.)
- `target`: Which symbol or candidate
- `score`: Numerical assessment (0-100)
- `reasons`: List of human-readable explanations

Example:

```python
{
    "type": "POSITION",
    "target": "AMD",
    "action": "TRIM_RISK",
    "score": 31.0,
    "reasons": [
        "Position vitals critically low",
        "High-confidence upgrade opportunity available",
        "Sector TECH shows strong momentum"
    ]
}
```

---

## 7. Risk & Safety Guarantees

### Guardrail Types

| Guard | Trigger | Effect |
|-------|---------|--------|
| **Sector Concentration** | Any sector > 60% | Block new allocations to that sector |
| **Cash Reserve** | Cash < minimum threshold | Block outflows, encourage inflows |
| **Volatility × Aggression** | High volatility + aggressive action | Scale down or block |

### Implementation

- Guardrails run **after** decision synthesis
- Blocked actions are logged with reasons
- The system reports both allowed AND blocked actions
- Guardrails cannot be bypassed programmatically

### Why This Matters

Traditional systems execute trades first, ask questions later.  
This system asks questions first, executes never (in demo mode).

---

## 8. What This System Does NOT Do

| Capability | Status | Reason |
|------------|--------|--------|
| Order execution | ❌ | Demo/advisory only |
| Price prediction | ❌ | Not a crystal ball |
| ML model training | ❌ | Deterministic rules only |
| Backtesting | ❌ | Not a historical simulator |
| Unsupervised automation | ❌ | Human oversight required |
| Live trading | ❌ | Paper trading only |

### Why This Is Important

This system is designed to **augment human judgment**, not replace it.  
Every recommendation requires human approval before action.

---

## 9. How This Was Built (PROCESS)

### Development Timeline

1. **Mock Data First** — Built end-to-end flow with synthetic data
2. **Phase 2 Signals** — Implemented volatility, news, confidence scoring
3. **Phase 3 Decisions** — Added market posture and action logic
4. **Explainability** — Attached reasons to every decision
5. **Risk Guardrails** — Added concentration, cash, volatility guards
6. **Alpaca Integration** — Connected to real paper trading API (READ-ONLY)
7. **Demo Profiles** — Created hardcoded portfolios for reliable demos
8. **Test Suite** — Validated all modes and profiles

### Engineering Principles Applied

- **Fail-safe defaults:** Empty data returns safe values, not crashes
- **Explicit over implicit:** Modes are clearly logged at startup
- **Isolation:** Phases don't reach into each other's internals
- **Determinism:** Same inputs → same outputs (no randomness)

---

## 10. Quick Reference

### Entry Point

```bash
python3 full_system_demo.py
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DEMO_MODE` | `true` | Use demo profiles |
| `DEMO_PROFILE` | `OVERCONCENTRATED_TECH` | Which profile to load |
| `DEMO_TREND` | `NEUTRAL` | Signal overlay (TECH_COOLING, RISK_ON, VOLATILITY_SHOCK) |
| `USE_ALPACA` | `false` | Use real Alpaca data (when DEMO_MODE is false) |
| `ALPACA_API_KEY` | — | Alpaca paper trading API key |
| `ALPACA_SECRET_KEY` | — | Alpaca paper trading secret |

### Example Commands

```bash
# Default demo (judges)
python3 full_system_demo.py

# Losing portfolio with volatility shock
DEMO_PROFILE=LOSING_PORTFOLIO DEMO_TREND=VOLATILITY_SHOCK python3 full_system_demo.py

# Real Alpaca data
DEMO_MODE=false USE_ALPACA=true python3 full_system_demo.py

# Run test suite
python3 tests/test_system.py
```

### File Structure

```
.
├── full_system_demo.py     # Main entry point
├── decision_engine.py      # Phase 3: Decision synthesis
├── risk_guardrails.py      # Phase 4: Safety gates
├── execution_planner.py    # Phase 5: Advisory planning
│
├── volatility_metrics.py   # Phase 2: Volatility signals
├── news_scorer.py          # Phase 2: News sentiment
├── sector_confidence.py    # Phase 2: Confidence scoring
│
├── position_vitals.py      # Position health scoring
├── concentration_guard.py  # Concentration detection
├── capital_lock_in.py      # Capital efficiency
├── opportunity_logic.py    # Candidate evaluation
│
├── broker/
│   ├── alpaca_adapter.py   # READ-ONLY Alpaca client
│   └── mock_adapter.py     # Mock data generator
│
├── demo/
│   ├── demo_profiles.py    # Hardcoded portfolio profiles
│   └── trend_overlays.py   # Signal modifiers for demos
│
├── tests/
│   └── test_system.py      # Comprehensive test suite
│
└── archive/                # Deprecated files (kept for reference)
```

---

## 11. For Judges

**What to look for:**

1. **Run the default demo** — Observe concentration alerts and TRIM recommendations
2. **Try LOSING_PORTFOLIO** — See RISK_OFF posture activate
3. **Check the RUN CONFIGURATION block** — Notice the transparency
4. **Review decision reasons** — Each action is explained
5. **Note what's NOT happening** — No orders, no predictions, no magic

**What this proves:**

- The system can reason about portfolio risk
- Safety is a first-class concern
- Decisions are explainable and auditable
- The architecture is clean and maintainable

---

*This document serves as the authoritative reference for understanding the Portfolio Intelligence System.*
