import streamlit as st
import pandas as pd
import yfinance as yf
import time
from supabase import create_client
import streamlit.components.v1 as components
from streamlit_autorefresh import st_autorefresh

# 1. Page Configuration
st.set_page_config(
    page_title="FinTech Portfolio & Swing Radar",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 2. Auto-refresh every 15 seconds (Acts as a price poller and security heartbeat)
st_autorefresh(interval=15000, key="datarefresh")

# 3. FinTech Glassmorphism Design System (CSS Injection)
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
  
  html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  }

  .stApp {
    background: radial-gradient(circle at 10% 20%, #0c101c 0%, #07090e 90%);
    color: #f1f5f9;
  }

  /* Entity Switcher Header Banner */
  .entity-banner {
    background: linear-gradient(90deg, rgba(30, 41, 59, 0.7) 0%, rgba(15, 23, 42, 0.7) 100%);
    border: 1px solid rgba(255, 255, 255, 0.08);
    backdrop-filter: blur(12px);
    border-radius: 16px;
    padding: 1rem 1.5rem;
    margin-bottom: 1.5rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .entity-title {
    font-size: 1.35rem;
    font-weight: 700;
    letter-spacing: -0.02em;
    color: #f8fafc;
  }

  .entity-subtitle {
    font-size: 0.8rem;
    font-weight: 500;
    color: #94a3b8;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  /* Frosted Glass KPI Cards */
  .kpi-card {
    background: rgba(22, 28, 45, 0.65);
    border: 1px solid rgba(255, 255, 255, 0.08);
    backdrop-filter: blur(14px);
    border-radius: 16px;
    padding: 1.25rem;
    box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
    margin-bottom: 1rem;
  }

  .kpi-title {
    font-size: 0.825rem;
    font-weight: 500;
    color: #94a3b8;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .kpi-value {
    font-size: 1.65rem;
    font-weight: 700;
    color: #f8fafc;
    margin-top: 0.35rem;
  }

  /* Stock Holding Cards */
  .stock-card {
    background: rgba(20, 26, 42, 0.7);
    border: 1px solid rgba(255, 255, 255, 0.07);
    border-radius: 14px;
    padding: 1.15rem;
    margin-bottom: 0.85rem;
    backdrop-filter: blur(10px);
    transition: transform 0.15s ease, border-color 0.15s ease;
  }

  .stock-card:hover {
    border-color: rgba(99, 102, 241, 0.4);
    transform: translateY(-2px);
  }

  /* Sector Summary Container */
  .sector-container {
    background: rgba(18, 24, 40, 0.55);
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 14px;
    padding: 1rem 1.25rem;
    margin-bottom: 1.5rem;
    backdrop-filter: blur(8px);
  }

  .sector-pill {
    background: rgba(99, 102, 241, 0.15);
    color: #a5b4fc;
    border: 1px solid rgba(99, 102, 241, 0.3);
    padding: 4px 10px;
    border-radius: 9999px;
    font-size: 0.78rem;
    font-weight: 600;
    display: inline-flex;
    align-items: center;
    margin-right: 0.5rem;
    margin-bottom: 0.4rem;
  }

  .sub-badge {
    background: rgba(30, 41, 59, 0.85);
    border: 1px solid rgba(255, 255, 255, 0.1);
    color: #cbd5e1;
    padding: 3px 8px;
    border-radius: 6px;
    font-size: 0.75rem;
    font-weight: 500;
    display: inline-flex;
    align-items: center;
    gap: 4px;
    margin-right: 4px;
    margin-top: 4px;
  }

  .badge-green {
    background: rgba(16, 185, 129, 0.15);
    color: #10b981;
    border: 1px solid rgba(16, 185, 129, 0.3);
    padding: 3px 10px;
    border-radius: 9999px;
    font-weight: 600;
    font-size: 0.78rem;
  }

  .badge-red {
    background: rgba(239, 68, 68, 0.15);
    color: #ef4444;
    border: 1px solid rgba(239, 68, 68, 0.3);
    padding: 3px 10px;
    border-radius: 9999px;
    font-weight: 600;
    font-size: 0.78rem;
  }

  .corp-tag {
    background: rgba(245, 158, 11, 0.15);
    color: #f59e0b;
    border: 1px solid rgba(245, 158, 11, 0.35);
    padding: 4px 12px;
    border-radius: 9999px;
    font-size: 0.75rem;
    font-weight: 700;
    letter-spacing: 0.05em;
  }

  /* Glassmorphic Login Gateway Card */
  .auth-card {
    background: rgba(22, 28, 45, 0.85);
    border: 1px solid rgba(255, 255, 255, 0.12);
    backdrop-filter: blur(20px);
    border-radius: 20px;
    padding: 2.5rem 2rem;
    max-width: 460px;
    margin: 3rem auto;
    box-shadow: 0 20px 45px rgba(0, 0, 0, 0.6);
    text-align: center;
  }

  div[data-testid="stExpander"] {
    background: rgba(18, 24, 38, 0.5) !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    border-radius: 14px !important;
    backdrop-filter: blur(8px);
    margin-bottom: 1rem;
  }

  div.stButton > button {
    background: linear-gradient(135deg, #4f46e5 0%, #3730a3 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    padding: 0.5rem 1.25rem !important;
    box-shadow: 0 4px 14px rgba(79, 70, 229, 0.3) !important;
  }
</style>
""", unsafe_allow_html=True)

# 4. Database Setup
@st.cache_resource
def init_supabase():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_supabase()

# 5. Master Constants
MERAKI_TRADERS = ["Abin", "Fery", "Osi", "Eisha"]
MERAKI_BROKERS_IDX = ["Stockbit", "SimInvest", "Mirae", "growin'", "Ajaib"]
MERAKI_BROKERS_US = ["Ajaib", "Pluang", "Interactive Brokers", "Other"]

# Explicit Entity Passwords & Inactivity Duration
PASSWORDS = {
    "pers": "Janardana2001Abin!",
    "meraki": "Upin7Ipin!"
}
INACTIVITY_TIMEOUT = 600  # 10 minutes in seconds

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
        "toolbar_bg": "#f1f3f6",
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

# 9. Top Navigation & Workspace Selection
st.markdown("""
<div style="display: flex; align-items: baseline; gap: 8px; margin-bottom: 0.25rem;">
  <span style="font-size: 1.5rem; font-weight: 800; letter-spacing: -0.03em; color: #f8fafc;">⚡ FinTech Terminal</span>
  <span style="font-size: 0.85rem; color: #64748b; font-weight: 500;">Zero-Trust Portfolio Hub</span>
</div>
""", unsafe_allow_html=True)

entity_choice = st.radio(
    "Select Workspace:",
    ["👤 Personal Portfolio", "🏛️ Meraki Mahardika Investama"],
    horizontal=True,
    label_visibility="collapsed"
)

is_meraki = (entity_choice == "🏛️ Meraki Mahardika Investama")
entity_prefix = "meraki" if is_meraki else "pers"
active_table = "meraki_transactions" if is_meraki else "stock_transactions"
entity_name = "Meraki Mahardika Investama" if is_meraki else "Personal Portfolio"
badge_html = '<span class="corp-tag">CORPORATE ENTITY</span>' if is_meraki else '<span class="corp-tag" style="background: rgba(99, 102, 241, 0.15); color: #818cf8; border-color: rgba(99, 102, 241, 0.3);">INDIVIDUAL</span>'

# Session State Keys
auth_key = f"{entity_prefix}_is_authenticated"
time_key = f"{entity_prefix}_last_activity"

# Check Inactivity Timeout (10 minutes)
if st.session_state.get(auth_key, False):
    last_act = st.session_state.get(time_key, time.time())
    elapsed = time.time() - last_act
    if elapsed > INACTIVITY_TIMEOUT:
        st.session_state[auth_key] = False
        st.warning("⚠️ Session expired due to 10 minutes of inactivity. Please re-enter your password.")
        st.rerun()

# 10. Authentication Gateway (If not authenticated)
if not st.session_state.get(auth_key, False):
    col_l1, col_l2, col_l3 = st.columns([1, 2, 1])
    with col_l2:
        st.markdown(f"""
            <div class="auth-card">
              <div style="font-size: 2.2rem; margin-bottom: 0.5rem;">🔒</div>
              <div style="font-size: 1.25rem; font-weight: 700; color: #f8fafc;">{entity_name}</div>
              <div style="font-size: 0.8rem; color: #94a3b8; margin-top: 4px; margin-bottom: 1.5rem;">
                Protected Terminal · Password Required
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
                    
    # Strict execution stop: Prevent rendering data or querying tables downstream
    st.stop()

# 11. Authenticated Workspace Header
st.markdown(f"""
<div class="entity-banner">
  <div>
    <div class="entity-subtitle">Active Trading Account</div>
    <div class="entity-title">{entity_name}</div>
  </div>
  <div>{badge_html}</div>
</div>
""", unsafe_allow_html=True)

ctrl_c1, ctrl_c2, ctrl_c3 = st.columns([3, 1, 1])
with ctrl_c1:
    cost_method = st.radio("Accounting Method", ["AVG", "FIFO"], horizontal=True, key=f"{entity_prefix}_cost_method")
with ctrl_c2:
    is_censored = st.toggle("🔒 Privacy Mode", value=False, key=f"{entity_prefix}_privacy")
with ctrl_c3:
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
    pnl_class = "badge-green" if net_pnl >= 0 else "badge-red"

    # KPI Top Bar
    disp_val = mask_value(f"{total_market_val:,.2f} {currency}", is_censored)
    disp_cost = mask_value(f"{total_cost_basis:,.2f} {currency}", is_censored)
    disp_pnl = mask_value(f"{net_pnl:+,.2f} ({net_pnl_pct:+.2f}%)", is_censored)

    c1, c2, c3 = st.columns(3)
    c1.markdown(f"""
        <div class="kpi-card">
          <div class="kpi-title">Portfolio Value</div>
          <div class="kpi-value">{disp_val}</div>
        </div>
    """, unsafe_allow_html=True)
    c2.markdown(f"""
        <div class="kpi-card">
          <div class="kpi-title">Total Cost Basis</div>
          <div class="kpi-value">{disp_cost}</div>
        </div>
    """, unsafe_allow_html=True)
    c3.markdown(f"""
        <div class="kpi-card">
          <div class="kpi-title">Net Unrealized P&L</div>
          <div class="kpi-value" style="font-size: 1.35rem; margin-top: 0.55rem;">
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

        pills_html = '<div class="sector-container"><div style="margin-bottom: 8px; font-weight: 600; font-size: 0.85rem; color: #94a3b8;">SECTOR EXPOSURE:</div>'
        for sec, val in sorted(sector_weights.items(), key=lambda x: x[1], reverse=True):
            pct = (val / total_market_val) * 100
            val_masked = mask_value(f"{val:,.2f} {currency}", is_censored)
            pills_html += f'<span class="sector-pill">{sec} &nbsp;|&nbsp; {pct:.1f}% ({val_masked})</span>'
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

            st.markdown(f"##### 🏷️ {sec} &nbsp;<span style='font-size:0.8rem; color:#94a3b8;'>({sec_weight:.1f}% · {sec_val_display})</span>", unsafe_allow_html=True)
            
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
                badge = "badge-green" if pnl_val >= 0 else "badge-red"

                sub_html = ""
                if is_corp and h.get("breakdown"):
                    sub_html = '<div style="margin-top: 10px; padding-top: 8px; border-top: 1px solid rgba(255,255,255,0.08);">'
                    sub_html += '<div style="color: #94a3b8; font-size: 0.72rem; font-weight: 600; text-transform: uppercase; margin-bottom: 4px;">Ownership & Custody Breakdown:</div>'
                    sub_html += '<div style="display: flex; flex-wrap: wrap; gap: 4px;">'
                    for item in h["breakdown"]:
                        sub_qty = f"{int(item['shares']/100)} Lots" if market == "IDX" else f"{item['shares']} Shares"
                        masked_sub_qty = mask_value(sub_qty, is_censored)
                        sub_html += f'<span class="sub-badge">👤 {item["trader"]} · 🏦 {item["broker"]} <strong style="color: #60a5fa; margin-left: 2px;">({masked_sub_qty})</strong></span>'
                    sub_html += '</div></div>'

                col_target = h_cols[idx_c % 2]
                col_target.markdown(f"""
                    <div class="stock-card">
                      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                        <div>
                          <span style="font-size: 1.2rem; font-weight: 700; color: #60a5fa;">{t}</span>
                          <span style="font-size: 0.72rem; color: #94a3b8; margin-left: 6px;">{sec}</span>
                        </div>
                        <span class="{badge}">{mask_value(pnl_str, is_censored)}</span>
                      </div>
                      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; font-size: 0.85rem;">
                        <div><span style="color: #64748b;">Live Price:</span> <span style="font-weight: 600;">{curr_p:,.2f}</span></div>
                        <div><span style="color: #64748b;">Total Position:</span> <span style="font-weight: 600;">{mask_value(qty_label, is_censored)}</span></div>
                        <div><span style="color: #64748b;">Avg Cost:</span> <span style="font-weight: 600;">{mask_value(cost_str, is_censored)}</span></div>
                        <div><span style="color: #64748b;">Market Value:</span> <span style="font-weight: 600;">{mask_value(val_str, is_censored)}</span></div>
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
            st.session_state[time_key] = time.time()  # Reset inactivity timer
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
                st.session_state[time_key] = time.time()  # Reset inactivity timer
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
                st.session_state[time_key] = time.time()  # Reset inactivity timer
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
