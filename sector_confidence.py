def compute_sector_confidence(volatility_state: str, news_score: float) -> dict:
    """
    Combines volatility regime and news sentiment into a single Sector Confidence Score (0-100).
    
    Formula:
        Base Confidence = News Score
        
        Volatility Adjustments:
        - EXPANDING:   -20 penalty (High uncertainty reduces confidence in news signal)
        - STABLE:      No change (Baseline confidence)
        - CONTRACTING: +10 bonus (Calm markets increase confidence in trend)
        
        Final Score = Clamped(Base + Volatility Adjustment, 0, 100)
    
    Args:
        volatility_state (str): 'EXPANDING' | 'STABLE' | 'CONTRACTING'
        news_score (float): 0-100 (where 50 is neutral)
        
    Returns:
        dict: {"sector_confidence": int}
    """
    
    # 1. Base Score
    base_score = float(news_score)
    
    # 2. Volatility Adjustment
    vol_adj = 0.0
    
    if volatility_state == "EXPANDING":
        vol_adj = -20.0
    elif volatility_state == "CONTRACTING":
        vol_adj = 10.0
    elif volatility_state == "STABLE":
        vol_adj = 0.0
    else:
        # Unknown state -> treat as expanding risk for safety
        vol_adj = -10.0
        
    # 3. Combine
    raw_confidence = base_score + vol_adj
    
    # 4. Clamp & Round
    final_confidence = int(max(0, min(100, raw_confidence)))
    
    return {
        "sector_confidence": final_confidence
    }

# ---------------------------------------------------------
# Usage Example
# ---------------------------------------------------------
if __name__ == "__main__":
    print("=== SECTOR CONFIDENCE COMPONENT TEST ===")
    
    test_cases = [
        ("EXPANDING", 80),   # High News, but Volatile -> Should be penalized
        ("STABLE", 50),      # Neutral News, Stable -> Neutral
        ("CONTRACTING", 40), # Weak News, but Calm -> Slightly boosted
        ("EXPANDING", 20),   # Bad News + Volatility -> Crushed
        ("UNKNOWN", 50)      # Edge case
    ]
    
    for vol, news in test_cases:
        res = compute_sector_confidence(vol, news)
        print(f"Vol={vol:<12} | News={news:<3} -> Confidence={res['sector_confidence']}")
