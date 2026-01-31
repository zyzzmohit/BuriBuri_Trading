"""
full_system_demo.py

End-to-End Demonstration of the Portfolio Intelligence System.
Validates the complete pipeline: Signals -> Decisions -> Safety -> Planning.

Data Source:
    - USE_ALPACA = False (default): Mock data for development/testing
    - USE_ALPACA = True: Real Alpaca paper trading data

No real funds. No live trading. Pure logic validation.
"""

import os
import json
import volatility_metrics
import news_scorer
import sector_confidence
import decision_engine
import execution_planner
import risk_guardrails
import execution_summary

# =============================================================================
# DATA SOURCE CONFIGURATION
# =============================================================================

# Feature flag: Set to True to use real Alpaca paper trading data
# Can also be set via environment variable: USE_ALPACA=true
USE_ALPACA = os.environ.get("USE_ALPACA", "false").lower() == "true"

# Initialize data adapter based on feature flag
if USE_ALPACA:
    print("[Config] Data Source: ALPACA (Paper Trading)")
    from broker.alpaca_adapter import AlpacaAdapter
    _adapter = AlpacaAdapter()
else:
    print("[Config] Data Source: MOCK (Development)")
    from broker.mock_adapter import MockAdapter
    _adapter = MockAdapter()


# =============================================================================
# DATA ACCESS LAYER (Uses Adapter)
# =============================================================================

def get_portfolio_context():
    """Returns portfolio state from configured data source."""
    return _adapter.get_portfolio()


def get_positions():
    """Returns positions from configured data source."""
    return _adapter.get_positions()


def get_candidates():
    """Returns trade candidates."""
    candidates = _adapter.get_candidates()
    # If Alpaca returns empty, use defaults
    if not candidates:
        return [
            {"symbol": "NEW_BIO", "sector": "BIOTECH", "projected_efficiency": 85.0},
            {"symbol": "MORE_TECH", "sector": "TECH", "projected_efficiency": 95.0}
        ]
    return candidates


def get_sector_heatmap():
    """Returns sector heat scores."""
    return _adapter.get_sector_heatmap()


def get_market_data():
    """Returns candles and news headlines."""
    # Get candles from adapter
    candles = _adapter.get_recent_candles("SPY", 20)
    
    # If no candles, generate mock
    if not candles:
        candles = [
            {"timestamp": f"2026-01-31T10:{i:02d}:00Z", "high": 100+i, "low": 98+i, "close": 99+i}
            for i in range(20)
        ]
    
    # Get headlines (may be empty from Alpaca)
    headlines = _adapter.get_headlines()
    if not headlines:
        headlines = [
            "Tech sector shows resilience despite rate hike fears",
            "AI demand continues to outpace supply in hardware markets",
            "Utility sector stagnates as bond yields rise"
        ]
    
    return candles, headlines


# =============================================================================
# API-COMPATIBLE OUTPUT FUNCTION (NO PRINTING)
# =============================================================================

def run_demo_scenario():
    """
    Returns full system output as JSON-safe dict.
    NO printing. NO side effects.
    
    This is the function called by the Flask API.
    """
    # Mock Data (Same as demo)
    portfolio = {
        "total_capital": 1_000_000.0,
        "cash": 150_000.0,
        "risk_tolerance": "moderate"
    }
    
    positions = [
        {
            "symbol": "NVDA", 
            "sector": "TECH",
            "entry_price": 400.0, 
            "current_price": 480.0, 
            "atr": 12.0, 
            "days_held": 12, 
            "capital_allocated": 300_000.0
        },
        {
            "symbol": "SLOW_UTIL", 
            "sector": "UTILITIES", 
            "entry_price": 50.0, 
            "current_price": 51.0, 
            "atr": 1.0, 
            "days_held": 42, 
            "capital_allocated": 200_000.0
        },
        {
            "symbol": "SPEC_TECH", 
            "sector": "TECH", 
            "entry_price": 120.0, 
            "current_price": 95.0, 
            "atr": 5.0, 
            "days_held": 8, 
            "capital_allocated": 180_000.0
        }
    ]
    
    sector_heatmap = {
        "TECH": 80,
        "UTILITIES": 40,
        "BIOTECH": 70
    }
    
    candidates = [
        {"symbol": "NEW_BIO", "sector": "BIOTECH", "projected_efficiency": 72.0},
        {"symbol": "MORE_TECH", "sector": "TECH", "projected_efficiency": 68.0}
    ]
    
    # Compute Phase 2 Signals
    candles = [
        {"timestamp": f"2026-01-31T10:{i:02d}:00Z", "high": 100+i, "low": 98+i, "close": 99+i}
        for i in range(20)
    ]
    headlines = [
        "Tech sector sees steady demand growth",
        "AI stocks remain resilient despite volatility",
        "Investors cautious ahead of inflation data"
    ]
    
    atr_res = volatility_metrics.compute_atr(candles)
    vol_res = volatility_metrics.classify_volatility_state(current_atr=2.0, baseline_atr=2.5)
    vol_state = vol_res["volatility_state"]
    
    news_res = news_scorer.score_tech_news(headlines)
    news_score_val = news_res["news_score"]
    
    conf_res = sector_confidence.compute_sector_confidence(vol_state, news_score_val)
    confidence_val = conf_res["sector_confidence"]
    
    market_context = {
        "candles": candles,
        "news": headlines
    }
    
    # Run Decision Engine
    decision_report = decision_engine.run_decision_engine(
        portfolio_state=portfolio,
        positions=positions,
        sector_heatmap=sector_heatmap,
        candidates=candidates,
        market_context=market_context
    )
    
    # Extract components
    posture = decision_report.get("market_posture", {})
    safe_decisions = decision_report.get("decisions", [])
    blocked_decisions = decision_report.get("blocked_by_safety", [])
    concentration_risk = decision_report.get("concentration_risk", {})
    
    # Generate Execution Plan
    if safe_decisions:
        simulated_decision_input = {"decision": posture.get("market_posture", "NEUTRAL")}
        plan_output = execution_planner.generate_execution_plan(simulated_decision_input, positions)
    else:
        plan_output = {"proposed_actions": []}
    
    # Generate Summary
    summary_context = {
        "primary_intent": posture.get("market_posture", "NEUTRAL"),
        "proposed_actions": plan_output.get("proposed_actions", []),
        "blocked_actions": blocked_decisions,
        "mode": posture.get("risk_level", "MEDIUM")
    }
    summary = execution_summary.generate_execution_summary(summary_context)
    
    # Return JSON-safe structure for UI
    return {
        # Phase 2 Signals
        "phase2": {
            "volatility_state": vol_state,
            "volatility_explanation": "Volatility contracting, risk subsiding",
            "news_score": news_score_val,
            "news_explanation": f"Processed {news_res['headline_count']} headlines",
            "sector_confidence": confidence_val,
            "confidence_explanation": "Combined signals indicate moderate confidence"
        },
        # Phase 3 Decisions
        "market_posture": posture,
        "decisions": safe_decisions,
        "blocked_by_safety": blocked_decisions,
        "concentration_risk": concentration_risk,
        # Phase 4 Planning
        "execution_plan": plan_output.get("proposed_actions", []),
        "execution_summary": summary,
        # Metadata
        "input_stats": {
            "positions": len(positions),
            "candles": len(candles),
            "headlines": len(headlines)
        }
    }


# =============================================================================
# MAIN DEMO RUNNER
# =============================================================================

def run_full_system_demo():
    print("================================================================")
    print("PORTFOLIO INTELLIGENCE SYSTEM - END-TO-END DEMO")
    print("================================================================")
    
    # ---------------------------------------------------------
    # 1. PHASE 2 - SIGNAL GENERATION
    # ---------------------------------------------------------
    print("\n" + "="*50)
    print("=== PHASE 2: SIGNAL GENERATION ===")
    print("="*50)
    
    candles, headlines = get_market_data()
    
    # A. Volatility
    atr_res = volatility_metrics.compute_atr(candles)
    # Use computed ATR for classification
    current_atr = atr_res.get("atr", 2.0)
    baseline_atr = current_atr * 1.1  # Assume baseline slightly higher
    vol_res = volatility_metrics.classify_volatility_state(current_atr=current_atr, baseline_atr=baseline_atr)
    vol_state = vol_res["volatility_state"]
    print(f"[Signal] Volatility State: {vol_state} (ATR: {current_atr:.2f})")
    
    # B. News
    news_res = news_scorer.score_tech_news(headlines)
    news_score = news_res["news_score"]
    print(f"[Signal] News Sentiment:   {news_score}/100 ({news_res['headline_count']} headlines)")
    
    # C. Sector Confidence
    conf_res = sector_confidence.compute_sector_confidence(vol_state, news_score)
    confidence = conf_res["sector_confidence"]
    print(f"[Signal] Sector Confidence: {confidence}/100")
    
    market_context = {
        "candles": candles,
        "news": headlines
    }

    # ---------------------------------------------------------
    # 2. PHASE 3 - DECISION MAKING
    # ---------------------------------------------------------
    print("\n" + "="*50)
    print("=== PHASE 3: DECISION MAKING ===")
    print("="*50)
    
    portfolio = get_portfolio_context()
    positions = get_positions()
    heatmap = get_sector_heatmap()
    candidates = get_candidates()
    
    print(f"[Data] Portfolio: ${portfolio['total_capital']:,.0f} total, ${portfolio['cash']:,.0f} cash")
    print(f"[Data] Positions: {len(positions)}")
    for p in positions:
        print(f"       - {p['symbol']}: ${p.get('capital_allocated', 0):,.0f}")
    
    # Run the Engine
    decision_report = decision_engine.run_decision_engine(
        portfolio_state=portfolio,
        positions=positions,
        sector_heatmap=heatmap,
        candidates=candidates,
        market_context=market_context
    )
    
    posture = decision_report["market_posture"]
    print(f"\n[Strategy] Market Posture: {posture['market_posture']} (Risk: {posture['risk_level']})")
    print(f"[Strategy] Posture Reason: {posture['reasons'][0]}")
    
    print("\n[Strategy] Initial Decisions (Before Safety):")
    
    safe_decisions = decision_report.get("decisions", [])
    blocked_decisions = decision_report.get("blocked_by_safety", [])
    
    all_decisions = safe_decisions + blocked_decisions
    
    if not all_decisions:
        print("  - No actions proposed.")
    else:
        for d in all_decisions:
            print(f"  > {d['type']:<10} | {d['target']:<10} -> {d['action']}")
            print(f"    Reason: {d['reason']}")

    # ---------------------------------------------------------
    # 3. PHASE 4 - SAFETY & EXECUTION PLANNING
    # ---------------------------------------------------------
    print("\n" + "="*50)
    print("=== PHASE 4: SAFETY & EXECUTION PLANNING ===")
    print("="*50)

    if safe_decisions:
        simulated_decision_input = {"decision": posture["market_posture"]}
        plan_output = execution_planner.generate_execution_plan(simulated_decision_input, positions)
        
        print("\n[Plan] Execution Plan (Sequential):")
        for step in plan_output.get("proposed_actions", []):
            print(f"  - {step['symbol']}: {step['action']}")
            print(f"    Reason: {step['reason']}")
    else:
        plan_output = {"proposed_actions": []}
    
    print("\n[Safety] Blocked Actions Report:")
    if not blocked_decisions:
        print("  - No actions were blocked by safety guards.")
    else:
        for b in blocked_decisions:
            print(f"  X BLOCKED: {b['target']} ({b['action']})")
            print(f"    Guard: {b.get('blocking_guard', b.get('safety_reason', 'Unknown'))}")
            print(f"    Reason: {b.get('reason_blocked', b.get('reason', 'Safety violation'))}")

    # Final Summary
    print("\n" + "-"*60)
    print("FINAL EXECUTION SUMMARY")
    print("-" * 60)
    
    summary_context = {
        "primary_intent": posture["market_posture"],
        "proposed_actions": plan_output.get("proposed_actions", []) if safe_decisions else [],
        "blocked_actions": blocked_decisions,
        "mode": posture["risk_level"]
    }
    
    summary = execution_summary.generate_execution_summary(summary_context)
    
    print(f"Decision:         {summary['decision']}")
    print(f"Actions Proposed: {summary['actions_proposed']}")
    print(f"Actions Blocked:  {summary['actions_blocked']}")
    print(f"Final Mode:       {summary['final_mode']}")
    print("================================================================")


if __name__ == "__main__":
    run_full_system_demo()
