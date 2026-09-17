import streamlit as st
import pandas as pd
import yfinance as yf
import time
from supabase import create_client
import streamlit.components.v1 as components
from streamlit_autorefresh import st_autorefresh
import json
import feedparser
import google.generativeai as genai

# 1. Page Configuration
st.set_page_config(
    page_title="Stock Portfolio Terminal",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 2. Auto-refresh every 15 seconds (Price polling & idle watchdog)
st_autorefresh(interval=15000, key="datarefresh")

# 3. Google Material You (Material 3) Design System
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&family=Google+Sans:wght@400;500;700&display=swap');
  
  :root {
    --md-sys-color-background: #111318;
    --md-sys-color-surface: #111318;
    --md-sys-color-surface-container-low: #191c20;
    --md-sys-color-surface-container: #1d2024;
    --md-sys-color-surface-container-high: #282a2f;
    --md-sys-color-surface-container-highest: #33353a;
    --md-sys-color-primary: #a8c7fa;
    --md-sys-color-on-primary: #062e6f;
    --md-sys-color-primary-container: #234785;
    --md-sys-color-on-primary-container: #d3e3fd;
    --md-sys-color-secondary-container: #384656;
    --md-sys-color-on-secondary-container: #dbe4f6;
    --md-sys-color-outline: #8c9199;
    --md-sys-color-outline-variant: #43474e;
    --md-sys-color-on-surface: #e2e2e9;
    --md-sys-color-on-surface-variant: #c3c7cf;
  }

  html, body, [class*="css"] {
    font-family: 'Google Sans', 'Roboto', -apple-system, sans-serif;
  }

  .stApp {
    background-color: var(--md-sys-color-background);
    color: var(--md-sys-color-on-surface);
  }

  /* ============================================================
     HERO & WORKSPACE SELECTOR (STRICT MIDLINE CENTERING)
     ============================================================ */

  .hero-header {
    text-align: center;
    margin-top: 1rem;
    margin-bottom: 1.25rem;
  }

  .hero-title {
    font-size: 1.85rem;
    font-weight: 700;
    color: var(--md-sys-color-on-surface);
    letter-spacing: -0.02em;
    margin: 0;
  }

  div[data-testid="stRadio"] > label,
  div[data-testid="stRadio"] [data-testid="stWidgetLabel"] {
    display: none !important;
  }

  div[data-testid="stElementContainer"]:has(> div[data-testid="stRadio"]) {
    display: flex !important;
    justify-content: center !important;
    align-items: center !important;
    width: 100% !important;
    margin: 0 auto !important;
  }

  div[data-testid="stRadio"],
  div.stRadio {
    width: 100% !important;
    display: flex !important;
    flex-direction: column !important;
    align-items: center !important;
    justify-content: center !important;
    text-align: center !important;
    margin: 0 auto 1.5rem auto !important;
  }

  div[data-testid="stRadio"] > div[role="radiogroup"],
  div.stRadio > div[role="radiogroup"] {
    display: inline-flex !important;
    flex-direction: row !important;
    flex-wrap: wrap !important;
    justify-content: center !important;
    align-items: center !important;
    align-self: center !important;
    margin: 0 auto !important;
    gap: 4px !important;
    background-color: var(--md-sys-color-surface-container-low) !important;
    border: 1px solid var(--md-sys-color-outline-variant) !important;
    border-radius: 28px !important;
    padding: 4px !important;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.25) !important;
  }

  div[data-testid="stRadio"] div[role="radiogroup"] label {
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    background: transparent !important;
    border: none !important;
    border-radius: 24px !important;
    padding: 8px 22px !important;
    margin: 0 !important;
    cursor: pointer !important;
    transition: background-color 0.2s ease, color 0.2s ease !important;
    min-height: 38px !important;
  }

  div[data-testid="stRadio"] div[role="radiogroup"] input[type="radio"] {
    display: none !important;
  }

  div[data-testid="stRadio"] div[role="radiogroup"] div[aria-hidden="true"] {
    display: none !important;
  }

  div[data-testid="stRadio"] div[role="radiogroup"] label div,
  div[data-testid="stRadio"] div[role="radiogroup"] label p,
  div[data-testid="stRadio"] div[role="radiogroup"] label span {
    font-size: 0.88rem !important;
    font-weight: 500 !important;
    color: var(--md-sys-color-on-surface-variant) !important;
  }

  div[data-testid="stRadio"] div[role="radiogroup"] label:hover {
    background-color: rgba(255, 255, 255, 0.05) !important;
  }

  div[data-testid="stRadio"] div[role="radiogroup"] label:hover span,
  div[data-testid="stRadio"] div[role="radiogroup"] label:hover p {
    color: #ffffff !important;
  }

  div[data-testid="stRadio"] div[role="radiogroup"] label:has(input:checked) {
    background-color: var(--md-sys-color-secondary-container) !important;
  }

  div[data-testid="stRadio"] div[role="radiogroup"] label:has(input:checked) div,
  div[data-testid="stRadio"] div[role="radiogroup"] label:has(input:checked) p,
  div[data-testid="stRadio"] div[role="radiogroup"] label:has(input:checked) span {
    color: var(--md-sys-color-on-secondary-container) !important;
    font-weight: 600 !important;
  }

  /* ============================================================
     SCOPED CONTROLS: AVG/FIFO (LEFT) & TOGGLE/LOCK (RIGHT)
     ============================================================ */

  div[data-testid="stColumn"] div[data-testid="stElementContainer"]:has(div[data-testid="stRadio"]) {
    display: flex !important;
    justify-content: flex-start !important;
    align-items: flex-start !important;
    margin: 0 !important;
    width: 100% !important;
  }

  div[data-testid="stColumn"] div[data-testid="stRadio"],
  div[data-testid="stColumn"] div.stRadio {
    align-items: flex-start !important;
    justify-content: flex-start !important;
    text-align: left !important;
    margin: 0 !important;
  }

  div[data-testid="stColumn"] div[data-testid="stRadio"] > div[role="radiogroup"],
  div[data-testid="stColumn"] div.stRadio > div[role="radiogroup"] {
    justify-content: flex-start !important;
    align-self: flex-start !important;
    margin: 0 !important;
  }

  div[data-testid="stColumn"] div[data-testid="stToggle"],
  div[data-testid="stColumn"] div.stToggle {
    display: flex !important;
    justify-content: flex-end !important;
    align-items: center !important;
    margin-left: auto !important;
    width: 100% !important;
  }

  div[data-testid="stColumn"] div[data-testid="stToggle"] label,
  div[data-testid="stColumn"] div.stToggle label {
    margin-left: auto !important;
    justify-content: flex-end !important;
  }

  div[data-testid="stColumn"] div.stButton {
    display: flex !important;
    justify-content: flex-end !important;
    width: 100% !important;
  }

  /* ============================================================
     MATERIAL YOU SURFACES & CARDS
     ============================================================ */

  .m3-banner-centered {
    background-color: var(--md-sys-color-surface-container);
    border: 1px solid var(--md-sys-color-outline-variant);
    border-radius: 24px;
    padding: 1.25rem 1.5rem;
    margin: 0 auto 1.5rem auto;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    text-align: center;
    gap: 8px;
    max-width: 680px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2);
  }

  .m3-title {
    font-size: 1.4rem;
    font-weight: 700;
    color: var(--md-sys-color-on-surface);
    letter-spacing: -0.01em;
  }

  .m3-subtitle {
    font-size: 0.75rem;
    font-weight: 600;
    color: var(--md-sys-color-primary);
    text-transform: uppercase;
    letter-spacing: 0.08em;
  }

  .m3-kpi-card {
    background-color: var(--md-sys-color-surface-container);
    border-radius: 20px;
    padding: 1.25rem 1.5rem;
    margin-bottom: 1rem;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.3);
  }

  .m3-kpi-title {
    font-size: 0.8rem;
    font-weight: 500;
    color: var(--md-sys-color-on-surface-variant);
    text-transform: uppercase;
    letter-spacing: 0.04em;
  }

  .m3-kpi-value {
    font-size: 1.75rem;
    font-weight: 700;
    color: var(--md-sys-color-on-surface);
    margin-top: 0.35rem;
  }

  .m3-stock-card {
    background-color: var(--md-sys-color-surface-container-low);
    border: 1px solid var(--md-sys-color-outline-variant);
    border-radius: 18px;
    padding: 1.25rem;
    margin-bottom: 0.85rem;
    transition: background-color 0.2s ease, border-color 0.2s ease;
  }

  .m3-stock-card:hover {
    background-color: var(--md-sys-color-surface-container);
    border-color: var(--md-sys-color-primary);
  }

  .m3-chip {
    background-color: var(--md-sys-color-surface-container-high);
    color: var(--md-sys-color-on-surface-variant);
    border: 1px solid var(--md-sys-color-outline-variant);
    border-radius: 8px;
    padding: 4px 12px;
    font-size: 0.8rem;
    font-weight: 500;
    display: inline-flex;
    align-items: center;
    margin-right: 0.5rem;
    margin-bottom: 0.4rem;
  }

  .m3-sub-chip {
    background-color: var(--md-sys-color-surface-container-highest);
    color: var(--md-sys-color-on-surface);
    border-radius: 8px;
    padding: 3px 8px;
    font-size: 0.75rem;
    font-weight: 500;
    display: inline-flex;
    align-items: center;
    gap: 4px;
    margin-right: 4px;
    margin-top: 4px;
  }

  .badge-tonal-green {
    background-color: #1a3826;
    color: #a8f5ba;
    padding: 4px 10px;
    border-radius: 8px;
    font-weight: 600;
    font-size: 0.78rem;
  }

  .badge-tonal-red {
    background-color: #441816;
    color: #f2b8b5;
    padding: 4px 10px;
    border-radius: 8px;
    font-weight: 600;
    font-size: 0.78rem;
  }

  .badge-entity {
    background-color: var(--md-sys-color-primary-container);
    color: var(--md-sys-color-on-primary-container);
    padding: 5px 14px;
    border-radius: 12px;
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.04em;
  }

  div[data-testid="stExpander"] {
    background-color: var(--md-sys-color-surface-container-low) !important;
    border: 1px solid var(--md-sys-color-outline-variant) !important;
    border-radius: 16px !important;
    margin-bottom: 1rem;
  }

  div.stButton > button {
    background-color: var(--md-sys-color-primary) !important;
    color: var(--md-sys-color-on-primary) !important;
    border: none !important;
    border-radius: 20px !important;
    font-weight: 600 !important;
    font-size: 0.875rem !important;
    padding: 0.55rem 1.5rem !important;
    box-shadow: none !important;
    transition: opacity 0.2s ease !important;
  }

  div.stButton > button:hover {
    opacity: 0.9 !important;
  }

  button[data-baseweb="tab"] {
    background: transparent !important;
    border-radius: 12px !important;
    color: var(--md-sys-color-on-surface-variant) !important;
    font-weight: 600 !important;
  }

  button[aria-selected="true"] {
    color: var(--md-sys-color-primary) !important;
    background-color: var(--md-sys-color-surface-container-high) !important;
  }

  .m3-auth-card {
    background-color: var(--md-sys-color-surface-container);
    border: 1px solid var(--md-sys-color-outline-variant);
    border-radius: 28px;
    padding: 2.5rem 2rem;
    max-width: 440px;
    margin: 1rem auto 1.5rem auto;
    text-align: center;
  }
</style>
""", unsafe_allow_html=True)

# 4. Database Connection
@st.cache_resource
def init_supabase():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_supabase()

# Configure Gemini AI Engine
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

def run_ai_broker_team(market, holdings, live_prices):
    """Orchestrates analyst.md, economist.md, stockanalyst.md, and analystqa.md with Search Grounding."""
    if not holdings:
        return "No active holdings to analyze. Please log a transaction first."
    
    # 1. Gather recent news headlines for active holdings
    news_brief = {}
    for ticker in list(holdings.keys())[:5]:
        sym = f"{ticker}.JK" if market == "IDX" else ticker
        try:
            feed_items = yf.Ticker(sym).news
            news_brief[ticker] = [n.get("title", "") for n in (feed_items or [])[:2]]
        except Exception:
            news_brief[ticker] = []

    # 2. Compile portfolio state
    summary = []
    for t, h in holdings.items():
        curr_p = live_prices.get(t, h["avg_cost"])
        pnl = ((curr_p - h["avg_cost"]) / h["avg_cost"]) * 100
        summary.append(f"- {t}: Avg Cost {h['avg_cost']:,.2f}, Live {curr_p:,.2f}, Unrealized Return {pnl:+.2f}%")

    portfolio_str = "\n".join(summary)
    news_str = json.dumps(news_brief)

    # 3. Master Orchestration Prompt
    prompt = f"""
    You are analyst.md orchestrating your virtual research team for the {market} market.
    
    Current Portfolio Status:
    {portfolio_str}

    Recent Stock News Headlines:
    {news_str}

    Conduct your team briefing step-by-step:
    1. **economist.md**: Use Google Search to evaluate current real-time macroeconomic context for {market} (Bank Indonesia BI-Rate decisions, USD/IDR currency trends, Federal Reserve FOMC policy, and inflation prints). Highlight upcoming sectors with expansion potential.
    2. **stockanalyst.md**: Audit fundamentals (assign a Safety Net rating) and technical momentum (Bullish/Bearish bias) for these positions.
    3. **analystqa.md**: Play devil's advocate. Cross-examine both macro and single-stock assumptions, point out valuation traps, and stress-test downside risks.
    4. **analyst.md**: Deliver clear, actionable takeaways, profit targets, and stop-loss rules for the portfolio owner.
    """

    try:
        # Grounded search execution
        model = genai.GenerativeModel(
            model_name="gemini-3.8-flash",
            tools=[{"google_search": {}}]
        )
        response = model.generate_content(prompt)
        return response.text
    except Exception:
        # Fallback to standard execution if SDK version differs
        try:
            model = genai.GenerativeModel("gemini-3.8-flash")
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"⚠️ Unable to generate AI analysis: {str(e)}"

# 5. Master Constants
MERAKI_TRADERS = ["Abin", "Fery", "Osi", "Eisha"]
MERAKI_BROKERS_IDX = ["Stockbit", "SimInvest", "Mirae", "growin'", "Ajaib"]
MERAKI_BROKERS_US = ["Ajaib", "Pluang", "Interactive Brokers", "Other"]

PASSWORDS = {
    "pers": "Janardana2001Abin!",
    "meraki": "Upin7Ipin!"
}
INACTIVITY_TIMEOUT = 600

# 6. Cached Sector Lookup (24h Cache)
@st.cache_data(ttl=86400)
def fetch_stock_sector(symbol):
    try:
        t = yf.Ticker(symbol)
        sec = t.info.get("sector") or t.info.get("industry")
        if sec:
            return sec.strip()
    except Exception:
        pass
    return "Diversified / Other"

# 7. Real-Time Price Fetcher
def fetch_realtime_price(symbol):
    try:
        t = yf.Ticker(symbol)
        fast = getattr(t, "fast_info", None)
        if fast is not None:
            try:
                p = fast.last_price
                if p is not None and not pd.isna(p) and p > 0:
                    return float(p)
            except Exception:
                pass
            try:
                p = fast["lastPrice"]
                if p is not None and not pd.isna(p) and p > 0:
                    return float(p)
            except Exception:
                pass
        
        intraday = t.history(period="1d", interval="1m")
        if not intraday.empty:
            return float(intraday["Close"].iloc[-1])
            
        daily = t.history(period="5d")
        if not daily.empty:
            return float(daily["Close"].iloc[-1])
    except Exception:
        pass
    return None

# 8. Multi-Trader & Multi-Broker Accounting Engine
def compute_holdings(transactions, method="AVG", is_corporate=False):
    if not transactions:
        return {}
    
    df_tx = pd.DataFrame(transactions).sort_values("transaction_date")
    holdings = {}
    
    for ticker, group in df_tx.groupby("ticker"):
        total_shares = 0.0
        total_cost = 0.0
        sub_accounts = {}
        buy_lots = []
        
        for _, row in group.iterrows():
            shares = float(row["shares"])
            price = float(row["price_per_share"])
            trader = row.get("trader") or "Unassigned"
            broker = row.get("broker") or "Unassigned"
            sub_key = (trader, broker)

            if sub_key not in sub_accounts:
                sub_accounts[sub_key] = 0.0

            if row["type"] == "BUY":
                total_cost += (shares * price)
                total_shares += shares
                sub_accounts[sub_key] += shares
                if method == "FIFO":
                    buy_lots.append({"shares": shares, "unit_cost": price})
            elif row["type"] == "SELL":
                avg_cost = total_cost / total_shares if total_shares > 0 else 0
                total_cost -= (shares * avg_cost)
                total_shares -= shares
                sub_accounts[sub_key] = max(0.0, sub_accounts[sub_key] - shares)
                
                if method == "FIFO":
                    rem_sell = shares
                    while rem_sell > 0.0001 and buy_lots:
                        if buy_lots[0]["shares"] <= rem_sell:
                            rem_sell -= buy_lots[0]["shares"]
                            buy_lots.pop(0)
                        else:
                            buy_lots[0]["shares"] -= rem_sell
                            rem_sell = 0

        if total_shares <= 0.0001:
            total_shares = 0.0
            total_cost = 0.0

        if total_shares > 0.0001:
            effective_avg_cost = total_cost / total_shares
            if method == "FIFO":
                rem_cost = sum(lot["shares"] * lot["unit_cost"] for lot in buy_lots)
                effective_avg_cost = rem_cost / total_shares if total_shares > 0 else 0
                total_cost = rem_cost

            breakdown = []
            for (trd, brk), shrs in sub_accounts.items():
                if shrs > 0.0001:
                    breakdown.append({
                        "trader": trd,
                        "broker": brk,
                        "shares": shrs
                    })

            holdings[ticker] = {
                "shares": total_shares,
                "avg_cost": effective_avg_cost,
                "total_cost": total_cost,
                "breakdown": breakdown,
                "sub_account_map": sub_accounts
            }
            
    return holdings

def render_tradingview(symbol):
    tv_code = f"""
    <div class="tradingview-widget-container">
      <div id="tv_chart_{symbol}"></div>
      <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
      <script type="text/javascript">
      new TradingView.widget({{
        "width": "100%",
        "height": 340,
        "symbol": "{symbol}",
        "interval": "D",
        "timezone": "Asia/Jakarta",
        "theme": "dark",
        "style": "1",
        "locale": "en",
        "toolbar_bg": "#1d2024",
        "enable_publishing": false,
        "hide_top_toolbar": false,
        "container_id": "tv_chart_{symbol}"
      }});
      </script>
    </div>
    """
    components.html(tv_code, height=360)

def mask_value(val_str, is_censored):
    return "••••••••" if is_censored else val_str

# ============================================================
# 9. CENTERED HERO & WORKSPACE SELECTOR
# ============================================================

st.markdown("""
<div class="hero-header">
  <div class="hero-title">Portfolio Terminal</div>
</div>
""", unsafe_allow_html=True)

entity_choice = st.radio(
    "Workspace Selector",
    ["👤 Personal Portfolio", "🏛️ Meraki Mahardika Investama"],
    horizontal=True,
    label_visibility="collapsed"
)

is_meraki = (entity_choice == "🏛️ Meraki Mahardika Investama")
entity_prefix = "meraki" if is_meraki else "pers"
active_table = "meraki_transactions" if is_meraki else "stock_transactions"
entity_name = "Meraki Mahardika Investama" if is_meraki else "Personal Portfolio"
badge_html = '<span class="badge-entity">CORPORATE ENTITY</span>' if is_meraki else '<span class="badge-entity" style="background-color: #384656; color: #dbe4f6;">INDIVIDUAL</span>'

auth_key = f"{entity_prefix}_is_authenticated"
time_key = f"{entity_prefix}_last_activity"

# Inactivity Timeout Guard (10 minutes)
if st.session_state.get(auth_key, False):
    last_act = st.session_state.get(time_key, time.time())
    elapsed = time.time() - last_act
    if elapsed > INACTIVITY_TIMEOUT:
        st.session_state[auth_key] = False
        st.warning("⚠️ Session expired due to 10 minutes of inactivity. Please re-enter your password.")
        st.rerun()

# 10. Material You Authentication Card (If not unlocked)
if not st.session_state.get(auth_key, False):
    col_l1, col_l2, col_l3 = st.columns([1, 2, 1])
    with col_l2:
        st.markdown(f"""
            <div class="m3-auth-card">
              <div style="font-size: 2.2rem; margin-bottom: 0.5rem;">🔒</div>
              <div style="font-size: 1.3rem; font-weight: 700; color: #e2e2e9;">{entity_name}</div>
              <div style="font-size: 0.85rem; color: #8c9199; margin-top: 4px; margin-bottom: 1.5rem;">
                Protected Workspace · Password Required
              </div>
            </div>
        """, unsafe_allow_html=True)
        
        with st.form(key=f"auth_form_{entity_prefix}"):
            pwd_input = st.text_input("Enter Password", type="password", placeholder="••••••••••••", key=f"pwd_field_{entity_prefix}")
            submit_login = st.form_submit_button("Unlock Workspace", use_container_width=True)
            
            if submit_login:
                if pwd_input == PASSWORDS[entity_prefix]:
                    st.session_state[auth_key] = True
                    st.session_state[time_key] = time.time()
                    st.success("Access Granted.")
                    st.rerun()
                else:
                    st.error("Incorrect password. Access denied.")
                    
    st.stop()

# 11. Authenticated Centered Banner & Aligned Controls
st.markdown(f"""
<div class="m3-banner-centered">
  <div class="m3-subtitle">Active Trading Account</div>
  <div class="m3-title">{entity_name}</div>
  <div>{badge_html}</div>
</div>
""", unsafe_allow_html=True)

ctrl_left, ctrl_spacer, ctrl_toggle, ctrl_lock = st.columns([3.0, 3.0, 2.2, 1.8])
with ctrl_left:
    cost_method = st.radio(
        "Cost Basis Mode",
        ["AVG", "FIFO"],
        horizontal=True,
        key=f"{entity_prefix}_cost_method",
        label_visibility="collapsed"
    )
with ctrl_toggle:
    is_censored = st.toggle("🔒 Privacy Mode", value=False, key=f"{entity_prefix}_privacy")
with ctrl_lock:
    if st.button("🔒 Lock Terminal", key=f"lock_btn_{entity_prefix}", use_container_width=True):
        st.session_state[auth_key] = False
        st.rerun()

tab_idx, tab_us = st.tabs(["🇮🇩 Indonesia (IDX)", "🇺🇸 United States (US)"])

# 12. Unified Market Rendering Engine
def render_market_dashboard(market, currency, buy_universe, db_table, p_prefix, is_corp):
    tx_res = supabase.table(db_table).select("*").eq("market", market).order("transaction_date", desc=True).execute()
    transactions = tx_res.data or []
    holdings = compute_holdings(transactions, method=cost_method, is_corporate=is_corp)

    live_prices = {}
    holding_sectors = {}
    total_market_val = 0.0
    total_cost_basis = 0.0

    if holdings:
        tickers = list(holdings.keys())
        for t in tickers:
            yf_sym = f"{t}.JK" if market == "IDX" else t
            price = fetch_realtime_price(yf_sym)
            live_prices[t] = price if price is not None else holdings[t]["avg_cost"]
            holding_sectors[t] = fetch_stock_sector(yf_sym)
            
            val = holdings[t]["shares"] * live_prices[t]
            total_market_val += val
            total_cost_basis += holdings[t]["total_cost"]

    net_pnl = total_market_val - total_cost_basis
    net_pnl_pct = (net_pnl / total_cost_basis * 100) if total_cost_basis > 0 else 0
    pnl_class = "badge-tonal-green" if net_pnl >= 0 else "badge-tonal-red"

    # KPI Top Bar
    disp_val = mask_value(f"{total_market_val:,.2f} {currency}", is_censored)
    disp_cost = mask_value(f"{total_cost_basis:,.2f} {currency}", is_censored)
    disp_pnl = mask_value(f"{net_pnl:+,.2f} ({net_pnl_pct:+.2f}%)", is_censored)

    c1, c2, c3 = st.columns(3)
    c1.markdown(f"""
        <div class="m3-kpi-card">
          <div class="m3-kpi-title">Portfolio Value</div>
          <div class="m3-kpi-value">{disp_val}</div>
        </div>
    """, unsafe_allow_html=True)
    c2.markdown(f"""
        <div class="m3-kpi-card">
          <div class="m3-kpi-title">Total Cost Basis</div>
          <div class="m3-kpi-value">{disp_cost}</div>
        </div>
    """, unsafe_allow_html=True)
    c3.markdown(f"""
        <div class="m3-kpi-card">
          <div class="m3-kpi-title">Net Unrealized P&L</div>
          <div class="m3-kpi-value" style="font-size: 1.35rem; margin-top: 0.55rem;">
            <span class="{pnl_class}">{disp_pnl}</span>
          </div>
        </div>
    """, unsafe_allow_html=True)

    # Sector Breakdown
    st.markdown("#### 🏢 Industry Allocation")
    if holdings and total_market_val > 0:
        sector_weights = {}
        for t, h in holdings.items():
            sec = holding_sectors.get(t, "Diversified / Other")
            mkt_v = h["shares"] * live_prices.get(t, h["avg_cost"])
            sector_weights[sec] = sector_weights.get(sec, 0.0) + mkt_v

        pills_html = '<div style="margin-bottom: 1.25rem;">'
        for sec, val in sorted(sector_weights.items(), key=lambda x: x[1], reverse=True):
            pct = (val / total_market_val) * 100
            val_masked = mask_value(f"{val:,.2f} {currency}", is_censored)
            pills_html += f'<span class="m3-chip">{sec} &nbsp;·&nbsp; {pct:.1f}% ({val_masked})</span>'
        pills_html += '</div>'
        st.markdown(pills_html, unsafe_allow_html=True)
    else:
        st.caption("Industry allocation will compute automatically when positions exist.")

    # Portfolio Holdings Section
    st.markdown("#### 💼 Holdings (Grouped by Industry)")
    if holdings:
        grouped_by_sector = {}
        for t, h in holdings.items():
            sec = holding_sectors.get(t, "Diversified / Other")
            if sec not in grouped_by_sector:
                grouped_by_sector[sec] = []
            grouped_by_sector[sec].append((t, h))

        for sec, items in grouped_by_sector.items():
            sec_total_val = sum(h["shares"] * live_prices[t] for t, h in items)
            sec_weight = (sec_total_val / total_market_val * 100) if total_market_val > 0 else 0
            sec_val_display = mask_value(f"{sec_total_val:,.2f} {currency}", is_censored)

            st.markdown(f"##### 🏷️ {sec} &nbsp;<span style='font-size:0.8rem; color:#8c9199;'>({sec_weight:.1f}% · {sec_val_display})</span>", unsafe_allow_html=True)
            
            h_cols = st.columns(2)
            for idx_c, (t, h) in enumerate(items):
                curr_p = live_prices[t]
                val = h["shares"] * curr_p
                pnl_val = val - h["total_cost"]
                pnl_pct = (pnl_val / h["total_cost"] * 100) if h["total_cost"] > 0 else 0

                qty_label = f"{int(h['shares']/100)} Lots" if market == "IDX" else f"{h['shares']:,.2f} Shares"
                cost_str = f"{h['avg_cost']:,.2f}"
                val_str = f"{val:,.2f} {currency}"
                pnl_str = f"{pnl_val:+,.2f} ({pnl_pct:+.2f}%)"
                badge = "badge-tonal-green" if pnl_val >= 0 else "badge-tonal-red"

                sub_html = ""
                if is_corp and h.get("breakdown"):
                    sub_html = '<div style="margin-top: 10px; padding-top: 8px; border-top: 1px solid var(--md-sys-color-outline-variant);">'
                    sub_html += '<div style="color: #8c9199; font-size: 0.72rem; font-weight: 500; text-transform: uppercase; margin-bottom: 4px;">Ownership & Custody Breakdown:</div>'
                    sub_html += '<div style="display: flex; flex-wrap: wrap; gap: 4px;">'
                    for item in h["breakdown"]:
                        sub_qty = f"{int(item['shares']/100)} Lots" if market == "IDX" else f"{item['shares']} Shares"
                        masked_sub_qty = mask_value(sub_qty, is_censored)
                        sub_html += f'<span class="m3-sub-chip">👤 {item["trader"]} · 🏦 {item["broker"]} <strong>({masked_sub_qty})</strong></span>'
                    sub_html += '</div></div>'

                col_target = h_cols[idx_c % 2]
                col_target.markdown(f"""
                    <div class="m3-stock-card">
                      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                        <div>
                          <span style="font-size: 1.25rem; font-weight: 700; color: #a8c7fa;">{t}</span>
                          <span style="font-size: 0.75rem; color: #8c9199; margin-left: 6px;">{sec}</span>
                        </div>
                        <span class="{badge}">{mask_value(pnl_str, is_censored)}</span>
                      </div>
                      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; font-size: 0.85rem;">
                        <div><span style="color: #8c9199;">Live Price:</span> <span style="font-weight: 500;">{curr_p:,.2f}</span></div>
                        <div><span style="color: #8c9199;">Total Position:</span> <span style="font-weight: 500;">{mask_value(qty_label, is_censored)}</span></div>
                        <div><span style="color: #8c9199;">Avg Cost:</span> <span style="font-weight: 500;">{mask_value(cost_str, is_censored)}</span></div>
                        <div><span style="color: #8c9199;">Market Value:</span> <span style="font-weight: 500;">{mask_value(val_str, is_censored)}</span></div>
                      </div>
                      {sub_html}
                    </div>
                """, unsafe_allow_html=True)
            st.markdown("<div style='margin-bottom: 1rem;'></div>", unsafe_allow_html=True)
    else:
        st.info("No active positions held in this account.")

    # Transaction Form
    with st.expander("➕ Log New Transaction (BUY / SELL)"):
        col_t1, col_t2 = st.columns(2)
        with col_t1:
            f_type = st.selectbox("Order Type", ["BUY", "SELL"], key=f"f_type_{p_prefix}_{market}")
            f_ticker = st.text_input("Ticker Symbol", placeholder="e.g. BMRI, AAPL", key=f"f_tick_{p_prefix}_{market}").upper().strip()
        with col_t2:
            if is_corp:
                f_trader = st.selectbox("Trader / Owner", MERAKI_TRADERS, key=f"f_trader_{p_prefix}_{market}")
                broker_opts = MERAKI_BROKERS_IDX if market == "IDX" else MERAKI_BROKERS_US
                f_broker = st.selectbox("Stock Broker Account", broker_opts, key=f"f_broker_{p_prefix}_{market}")
            else:
                f_trader = "Personal"
                f_broker = "Personal"

        col_q1, col_q2 = st.columns(2)
        with col_q1:
            f_qty = st.number_input("Quantity (" + ("Lots" if market == "IDX" else "Shares") + ")", min_value=1.0, step=1.0, key=f"f_qty_{p_prefix}_{market}")
        with col_q2:
            f_price = st.number_input(f"Execution Price ({currency})", min_value=0.01, step=10.0 if market == "IDX" else 0.5, key=f"f_pr_{p_prefix}_{market}")

        shares = f_qty * 100 if market == "IDX" else f_qty
        trade_total = shares * f_price
        st.caption(f"Gross Transaction Value: {trade_total:,.2f} {currency}")

        if st.button("Submit Order", key=f"f_btn_{p_prefix}_{market}"):
            st.session_state[time_key] = time.time()
            if not f_ticker:
                st.error("Please specify a ticker symbol.")
            elif f_type == "SELL":
                ticker_holding = holdings.get(f_ticker, {})
                if is_corp:
                    sub_map = ticker_holding.get("sub_account_map", {})
                    avail_shares = sub_map.get((f_trader, f_broker), 0.0)
                    if avail_shares < shares:
                        avail_disp = f"{int(avail_shares/100)} Lots" if market == "IDX" else f"{avail_shares} Shares"
                        st.error(f"Cannot sell: {f_trader} only holds {avail_disp} of {f_ticker} in {f_broker}.")
                        st.stop()
                else:
                    if ticker_holding.get("shares", 0) < shares:
                        st.error("Cannot sell more shares than currently held.")
                        st.stop()

                supabase.table(db_table).insert({
                    "market": market,
                    "ticker": f_ticker,
                    "type": f_type,
                    "shares": shares,
                    "price_per_share": f_price,
                    "fee": 0,
                    "trader": f_trader,
                    "broker": f_broker
                }).execute()
                st.success(f"Recorded {f_type} for {f_ticker} ({f_trader} · {f_broker}).")
                st.rerun()
            else:
                supabase.table(db_table).insert({
                    "market": market,
                    "ticker": f_ticker,
                    "type": f_type,
                    "shares": shares,
                    "price_per_share": f_price,
                    "fee": 0,
                    "trader": f_trader,
                    "broker": f_broker
                }).execute()
                st.success(f"Recorded {f_type} order for {f_ticker} in {entity_name}.")
                st.rerun()

    # Modify Past Transactions
    with st.expander("🛠️ Modify Past Transactions"):
        if not transactions:
            st.caption("No trade records found for this account.")
        else:
            def format_tx_label(tx):
                date_str = tx["transaction_date"][:16].replace("T", " ")
                qty_dsp = f"{int(tx['shares']/100)} Lots" if market == "IDX" else f"{tx['shares']} Shares"
                tag = f" [{tx.get('trader','')} · {tx.get('broker','')}]" if is_corp else ""
                return f"{date_str} | {tx['type']} {qty_dsp} {tx['ticker']} @ {tx['price_per_share']:,.2f}{tag}"

            tx_map = {format_tx_label(tx): tx for tx in transactions}
            selected_label = st.selectbox("Select Record", list(tx_map.keys()), key=f"sel_{p_prefix}_{market}")
            selected_tx = tx_map[selected_label]

            curr_units = selected_tx["shares"] / 100 if market == "IDX" else selected_tx["shares"]
            
            e1, e2 = st.columns(2)
            with e1:
                e_type = st.selectbox("Type", ["BUY", "SELL"], index=0 if selected_tx["type"] == "BUY" else 1, key=f"e_type_{p_prefix}_{market}")
                e_ticker = st.text_input("Ticker", value=selected_tx["ticker"], key=f"e_tick_{p_prefix}_{market}").upper().strip()
                if is_corp:
                    cur_trader = selected_tx.get("trader") or MERAKI_TRADERS[0]
                    t_idx = MERAKI_TRADERS.index(cur_trader) if cur_trader in MERAKI_TRADERS else 0
                    e_trader = st.selectbox("Trader / Owner", MERAKI_TRADERS, index=t_idx, key=f"e_trader_{p_prefix}_{market}")
                else:
                    e_trader = "Personal"

            with e2:
                e_qty = st.number_input("Units", min_value=1.0, value=float(curr_units), step=1.0, key=f"e_qty_{p_prefix}_{market}")
                e_price = st.number_input("Price", min_value=0.01, value=float(selected_tx["price_per_share"]), key=f"e_pr_{p_prefix}_{market}")
                if is_corp:
                    b_list = MERAKI_BROKERS_IDX if market == "IDX" else MERAKI_BROKERS_US
                    cur_broker = selected_tx.get("broker") or b_list[0]
                    b_idx = b_list.index(cur_broker) if cur_broker in b_list else 0
                    e_broker = st.selectbox("Stock Broker", b_list, index=b_idx, key=f"e_broker_{p_prefix}_{market}")
                else:
                    e_broker = "Personal"

            new_shares = e_qty * 100 if market == "IDX" else e_qty
            b_save, b_del = st.columns(2)
            if b_save.button("💾 Save Update", key=f"btn_s_{p_prefix}_{market}"):
                st.session_state[time_key] = time.time()
                supabase.table(db_table).update({
                    "ticker": e_ticker,
                    "type": e_type,
                    "shares": new_shares,
                    "price_per_share": e_price,
                    "trader": e_trader,
                    "broker": e_broker
                }).eq("id", selected_tx["id"]).execute()
                st.success("Updated record.")
                st.rerun()

            if b_del.button("🗑️ Delete Record", key=f"btn_d_{p_prefix}_{market}"):
                st.session_state[time_key] = time.time()
                supabase.table(db_table).delete().eq("id", selected_tx["id"]).execute()
                st.warning("Deleted record.")
                st.rerun()

    # Holding Catalysts & News
    st.markdown("#### 📰 Holding Catalysts & News")
    if holdings:
        for t in list(holdings.keys())[:4]:
            yf_sym = f"{t}.JK" if market == "IDX" else t
            try:
                news = yf.Ticker(yf_sym).news
                if news:
                    st.markdown(f"**{t}**")
                    for item in news[:2]:
                        st.markdown(f"- [{item.get('title', '')}]({item.get('link', '#')})")
            except Exception:
                pass
    else:
        st.caption("Active positions will populate live news feeds.")

    # AI Broker Team Briefing Module (analyst.md)
    st.markdown("#### 🤖 AI Broker Team (analyst.md)")
    with st.expander("⚡ Request Portfolio Briefing & Stress Test", expanded=False):
        if st.button(f"Summon Analyst Team ({market})", key=f"run_ai_{p_prefix}_{market}"):
            with st.spinner("analyst.md is delegating to economist, stock analyst, and QA..."):
                report = run_ai_broker_team(market, holdings, live_prices)
                st.markdown(report)

    # Swing Recommendations
    st.markdown("#### 🎯 Swing Setups (1-2 Week Horizon)")
    st.markdown("##### 🟢 Recommended Buys")
    for pick in buy_universe:
        with st.expander(f"🟢 {pick['ticker']} — {pick['setup']}"):
            st.markdown(f"**Fundamentals:** {pick['fundamentals']}")
            st.markdown(f"**Technical Setup:** {pick['technicals']}")
            st.markdown(f"**Entry:** {pick['entry']} | **Target:** {pick['target']} | **Stop Loss:** {pick['stop']}")
            tv_sym = f"IDX:{pick['ticker']}" if market == "IDX" else pick['ticker']
            render_tradingview(tv_sym)

    st.markdown("##### 🔴 Exit & Stop Alerts")
    has_sell = False
    if holdings:
        for t, h in holdings.items():
            curr_p = live_prices.get(t, h["avg_cost"])
            pct_change = ((curr_p - h["avg_cost"]) / h["avg_cost"]) * 100
            if pct_change <= -4.5 or pct_change >= 10.0:
                has_sell = True
                status = "Target Reached (+10%)" if pct_change >= 10.0 else "Stop Level (-4.5%)"
                with st.expander(f"🔴 SELL: {t} — {status}"):
                    ret_str = f"{pct_change:+.2f}%"
                    cost_str = f"{h['avg_cost']:,.2f}"
                    st.write(f"Unrealized P&L: {mask_value(ret_str, is_censored)}")
                    st.write(f"Avg Cost: {mask_value(cost_str, is_censored)} | Current Price: {curr_p:,.2f}")
                    tv_sym = f"IDX:{t}" if market == "IDX" else t
                    render_tradingview(tv_sym)
    if not has_sell:
        st.caption("No sell or take-profit triggers tripped for current holdings.")

# Screened Watchlists
idx_buys = [
    {"ticker": "BMRI", "setup": "Pullback to 20-Day EMA", "fundamentals": "ROE 18.2%, PBV 2.1x, Net Profit Growth +14% YoY", "technicals": "Holding 20 EMA support at Rp 6,850; RSI 48 curling upwards.", "entry": "Rp 6,800 - 6,900", "target": "Rp 7,450 (+8.5%)", "stop": "Rp 6,600 (-3.8%)"},
    {"ticker": "TLKM", "setup": "Value Rebound from Support", "fundamentals": "ROE 17.5%, PBV 2.4x, Dividend Yield 5.1%", "technicals": "Double-bottom setup on daily chart; MACD bullish crossover.", "entry": "Rp 2,850 - 2,900", "target": "Rp 3,180 (+10.2%)", "stop": "Rp 2,750 (-4.1%)"}
]

us_buys = [
    {"ticker": "NVDA", "setup": "Bull Flag Consolidation", "fundamentals": "Operating Margin 62%, YoY Revenue +122%", "technicals": "Consolidating above 20 EMA; volume drying up before breakout attempt.", "entry": "$118 - $122", "target": "$135 (+11.0%)", "stop": "$114 (-4.5%)"},
    {"ticker": "AMZN", "setup": "Ascending Triangle Breakout", "fundamentals": "AWS revenue acceleration +19%, Free Cash Flow expansion", "technicals": "Testing $190 resistance; RSI 54 showing steady accumulation.", "entry": "$185 - $188", "target": "$205 (+9.5%)", "stop": "$178 (-4.2%)"}
]

with tab_idx:
    render_market_dashboard("IDX", "IDR", idx_buys, active_table, entity_prefix, is_meraki)

with tab_us:
    render_market_dashboard("US", "USD", us_buys, active_table, entity_prefix, is_meraki)
