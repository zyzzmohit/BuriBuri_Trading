import math
import feedparser
from datetime import datetime, timezone, timedelta

def compute_vitals(position: dict) -> dict:
    """
    Computes a Vitals Score (0-100) for a trading position to evaluate its efficiency.
    
    The score reflects a weighted combination of:
    1. Volatility-Adjusted Return (Risk efficiency)
    2. Capital Efficiency (Return on Capital Usage)
    3. Time Efficiency (Penalty for stagnation)

    Args:
        position (dict): A dictionary containing:
            - symbol (str): Ticker symbol
            - entry_price (float): Average entry price
            - current_price (float): Current market price
            - atr (float): Average True Range (volatility proxy)
            - days_held (int): Number of days the position has been open
            - capital_allocated (float): Total capital invested in this position

    Returns:
        dict: Evaluation results including:
            - symbol
            - vitals_score (float)
            - health (str): HEALTHY | WEAK | UNHEALTHY
            - suggested_action (str): HOLD / SCALE | HOLD / MONITOR | REDUCE / EXIT
            - drivers (dict): Breakdown of the component metrics
            - flags (list): Special condition flags (e.g., STAGNANT)
    """
    
    # ---------------------------------------------------------
    # 1. Extract and Validate Inputs
    # ---------------------------------------------------------
    symbol = position.get("symbol", "UNKNOWN")
    entry_price = float(position.get("entry_price", 0.0))
    current_price = float(position.get("current_price", 0.0))
    atr = float(position.get("atr", 0.0))
    days_held = int(position.get("days_held", 0))
    capital_allocated = float(position.get("capital_allocated", 0.0))

    # Safety checks to prevent division by zero or invalid logic
    if entry_price <= 0:
        return {
            "symbol": symbol,
            "vitals_score": 0.0,
            "health": "UNHEALTHY",
            "suggested_action": "REDUCE / EXIT (Data Error: Invalid Entry Price)",
            "drivers": {},
            "flags": ["DATA_ERROR"]
        }
    
    # ---------------------------------------------------------
    # 2. Compute Core Metrics
    # ---------------------------------------------------------
    
    # 1. Raw PnL Percentage
    pnl_pct = ((current_price - entry_price) / entry_price) * 100.0
    
    # 2. Volatility-Adjusted Return
    safe_atr = max(atr, 0.0001)
    vol_adj_return = pnl_pct / safe_atr

    # 3. Time Efficiency Penalty
    time_penalty = days_held / 10.0

    # 4. Capital Efficiency
    safe_capital = max(capital_allocated, 1.0)
    capital_efficiency = pnl_pct / (safe_capital / 100000.0)

    # ---------------------------------------------------------
    # 3. Calculate Efficiency Score (Internal Calculation)
    # ---------------------------------------------------------
    # Weights: 0.5 * Volatility + 0.3 * Capital - 0.2 * Time
    
    raw_efficiency = (
        (0.5 * vol_adj_return) +
        (0.3 * capital_efficiency) -
        (0.2 * time_penalty)
    )

    # Normalize to 0-100
    efficiency_score = 50.0 + (raw_efficiency * 10.0)
    efficiency_score = max(0.0, min(100.0, efficiency_score))
    
    # Round for output
    vitals_score = round(efficiency_score, 2)

    # ---------------------------------------------------------
    # 4. Derivative Flags
    # ---------------------------------------------------------
    # Stagnation: < 2% return but held > 20 days
    stagnant = pnl_pct < 2.0 and days_held > 20
    flags = []
    if stagnant:
        flags.append("STAGNANT")

    # ---------------------------------------------------------
    # 5. Determine Health Classification
    # ---------------------------------------------------------
    health = ""
    action = ""

    if vitals_score < 40:
        health = "UNHEALTHY"
        action = "REDUCE / EXIT"
    elif vitals_score < 60:
        health = "WEAK"
        action = "HOLD / MONITOR"
    else:
        health = "HEALTHY"
        action = "HOLD / SCALE"

    # ---------------------------------------------------------
    # 6. Return Final Output
    # ---------------------------------------------------------
    return {
        "symbol": symbol,
        "vitals_score": vitals_score,
        "health": health,
        "suggested_action": action,
        "drivers": {
            "pnl_pct": round(pnl_pct, 2),
            "vol_adj_return": round(vol_adj_return, 2),
            "time_penalty": round(time_penalty, 2),
            "capital_efficiency": round(capital_efficiency, 2)
        },
        "flags": flags
    }

def fetch_sector_news() -> list[dict]:
    """
    Fetches recent Technology sector news headlines using Google News RSS.
    
    Returns:
        list[dict]: A list of dictionaries with 'title' and 'published' keys.
                    Returns empty list on failure. 
                    Includes only headlines from the last 24 hours.
    """
    # Hardcoded URL for Technology Sector (India Region)
    rss_url = "https://news.google.com/rss/search?q=technology+sector&hl=en-IN&gl=IN&ceid=IN:en"
    
    try:
        # Parse RSS Feed
        feed = feedparser.parse(rss_url)
        
        # Check for parsing failure or empty feed
        if not feed.entries: 
            # feedparser might return empty entries on network error too (bozo bit might be set)
            # but we just want to safely return empty list.
            print("Error: Empty feed or parsing failure (check network).")
            return []

        headlines = []
        now_utc = datetime.now(timezone.utc)
        one_day_ago = now_utc - timedelta(hours=24)

        for entry in feed.entries:
            title = entry.get("title", "").strip()
            
            # Title Validation
            if not title:
                continue
            
            # Time Handling
            pub_date = None
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                try:
                    # published_parsed is a struct_time tuple in UTC
                    pub_date = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                except Exception:
                    pass
            
            # If date is missing or invalid, we skip it (Strict 24h rule)
            if not pub_date:
                continue

            # Time Filter (Last 24 hours)
            if pub_date < one_day_ago:
                continue
            
            # Add valid headline
            headlines.append({
                "title": title,
                "published": pub_date.isoformat()
            })
            
        return headlines

    except Exception as e:
        # Catch-all for any other runtime errors to ensure no crashes
        print(f"Error fetching news: {e}")
        return []

# ---------------------------------------------------------
# Usage Example
# ---------------------------------------------------------
if __name__ == "__main__":
    print("=== VITALS MONITOR: Position & News Validation ===")
    
    # 1. Test Position Logic
    print("\n[Test 1] Computing Vitals for a healthy position...")
    pos_example = {
        "symbol": "TEST_TICKER",
        "entry_price": 100.0,
        "current_price": 120.0,
        "atr": 2.5,
        "days_held": 5,
        "capital_allocated": 50000.0
    }
    result = compute_vitals(pos_example)
    print(f"Result: {result['health']} (Score: {result['vitals_score']})")

    # 2. Test News Fetching
    print("\n[Test 2] Fetching Technology Sector News (Last 24h)...")
    try:
        news = fetch_sector_news()
        print(f"Fetched {len(news)} headlines.")
        if news:
            print("Sample Headline:")
            print(f" - Title: {news[0]['title']}")
            print(f" - Published: {news[0]['published']}")
        else:
            print("No news found (or network error).")
    except Exception as e:
        print(f"CRITICAL FAILURE: {e}")
