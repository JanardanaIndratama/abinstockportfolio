import streamlit as st
import pandas as pd
import yfinance as yf
from supabase import create_client
import streamlit.components.v1 as components
from streamlit_autorefresh import st_autorefresh

# 1. Page Configuration
st.set_page_config(
    page_title="FinTech Portfolio & Swing Radar",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 2. Polling every 15 seconds
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

  /* Badges */
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

  /* Form & Expander Polish */
  div[data-testid="stExpander"] {
    background: rgba(18, 24, 38, 0.5) !important;
    border: 1px solid rgba(255, 255, 255, 0.08) !important;
    border-radius: 14px !important;
    backdrop-filter: blur(8px);
    margin-bottom: 1rem;
  }

  /* Buttons */
  div.stButton > button {
    background: linear-gradient(135deg, #4f46e5 0%, #3730a3 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    padding: 0.5rem 1.25rem !important;
    box-shadow: 0 4px 14px rgba(79, 70, 229, 0.3) !important;
  }

  /* Segmented Control Styling */
  div[data-testid="stRadio"] > div {
    gap: 0.75rem;
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

# 5. Cached Sector Lookup (24h Cache)
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

# 6. Real-Time Price Fetcher
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

# 7. Accounting Calculations
def compute_holdings(transactions, method="AVG"):
    if not transactions:
        return {}
    
    df_tx = pd.DataFrame(transactions).sort_values("transaction_date")
    holdings = {}
    
    for ticker, group in df_tx.groupby("ticker"):
        if method == "AVG":
            total_shares = 0.0
            total_cost = 0.0
            for _, row in group.iterrows():
                shares = float(row["shares"])
                price = float(row["price_per_share"])
                if row["type"] == "BUY":
                    total_cost += (shares * price)
                    total_shares += shares
                elif row["type"] == "SELL":
                    avg_cost = total_cost / total_shares if total_shares > 0 else 0
                    total_cost -= (shares * avg_cost)
                    total_shares -= shares
                    if total_shares <= 0.0001:
                        total_shares = 0.0
                        total_cost = 0.0
            if total_shares > 0.0001:
                holdings[ticker] = {
                    "shares": total_shares,
                    "avg_cost": total_cost / total_shares,
                    "total_cost": total_cost
                }
        else: # FIFO
            buy_lots = []
            for _, row in group.iterrows():
                shares = float(row["shares"])
                price = float(row["price_per_share"])
                if row["type"] == "BUY":
                    buy_lots.append({"shares": shares, "unit_cost": price})
                elif row["type"] == "SELL":
                    rem_sell = shares
                    while rem_sell > 0.0001 and buy_lots:
                        if buy_lots[0]["shares"] <= rem_sell:
                            rem_sell -= buy_lots[0]["shares"]
                            buy_lots.pop(0)
                        else:
                            buy_lots[0]["shares"] -= rem_sell
                            rem_sell = 0
            rem_shares = sum(lot["shares"] for lot in buy_lots)
            rem_cost = sum(lot["shares"] * lot["unit_cost"] for lot in buy_lots)
            if rem_shares > 0.0001:
                holdings[ticker] = {
                    "shares": rem_shares,
                    "avg_cost": rem_cost / rem_shares,
                    "total_cost": rem_cost
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

# 8. Master Entity Selection (Placed Above Everything)
st.markdown("""
<div style="display: flex; align-items: baseline; gap: 8px; margin-bottom: 0.25rem;">
  <span style="font-size: 1.5rem; font-weight: 800; letter-spacing: -0.03em; color: #f8fafc;">⚡ FinTech Terminal</span>
  <span style="font-size: 0.85rem; color: #64748b; font-weight: 500;">Multi-Entity Portfolio Hub</span>
</div>
""", unsafe_allow_html=True)

entity_choice = st.radio(
    "Select Active Portfolio Workspace:",
    ["👤 Personal Portfolio", "🏛️ Meraki Mahardika Investama"],
    horizontal=True,
    label_visibility="collapsed"
)

# Route Active Context
if entity_choice == "👤 Personal Portfolio":
    active_table = "stock_transactions"
    entity_prefix = "pers"
    entity_name = "Personal Portfolio"
    badge_html = '<span class="corp-tag" style="background: rgba(99, 102, 241, 0.15); color: #818cf8; border-color: rgba(99, 102, 241, 0.3);">INDIVIDUAL</span>'
else:
    active_table = "meraki_transactions"
    entity_prefix = "meraki"
    entity_name = "Meraki Mahardika Investama"
    badge_html = '<span class="corp-tag">CORPORATE ENTITY</span>'

# Entity Header Banner
st.markdown(f"""
<div class="entity-banner">
  <div>
    <div class="entity-subtitle">Active Trading Account</div>
    <div class="entity-title">{entity_name}</div>
  </div>
  <div>{badge_html}</div>
</div>
""", unsafe_allow_html=True)

# Top Controls
ctrl_c1, ctrl_c2 = st.columns([3, 1])
with ctrl_c1:
    cost_method = st.radio("Accounting Method", ["AVG", "FIFO"], horizontal=True, key=f"{entity_prefix}_cost_method")
with ctrl_c2:
    is_censored = st.toggle("🔒 Privacy Mode", value=False, key=f"{entity_prefix}_privacy")

tab_idx, tab_us = st.tabs(["🇮🇩 Indonesia (IDX)", "🇺🇸 United States (US)"])

# 9. Generic Reusable Market Engine
def render_market_dashboard(market, currency, buy_universe, db_table, p_prefix):
    tx_res = supabase.table(db_table).select("*").eq("market", market).order("transaction_date", desc=True).execute()
    transactions = tx_res.data or []
    holdings = compute_holdings(transactions, method=cost_method)

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

    # KPI Header Cards
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

    # Industry / Sector Breakdown Section
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
                        <div><span style="color: #64748b;">Position:</span> <span style="font-weight: 600;">{mask_value(qty_label, is_censored)}</span></div>
                        <div><span style="color: #64748b;">Avg Cost:</span> <span style="font-weight: 600;">{mask_value(cost_str, is_censored)}</span></div>
                        <div><span style="color: #64748b;">Market Value:</span> <span style="font-weight: 600;">{mask_value(val_str, is_censored)}</span></div>
                      </div>
                    </div>
                """, unsafe_allow_html=True)
            st.markdown("<div style='margin-bottom: 1rem;'></div>", unsafe_allow_html=True)
    else:
        st.info("No active positions held in this account.")

    # Transaction Form (Isolated Keys per Entity)
    with st.expander("➕ Log New Transaction (BUY / SELL)"):
        f_type = st.selectbox("Order Type", ["BUY", "SELL"], key=f"f_type_{p_prefix}_{market}")
        f_ticker = st.text_input("Ticker Symbol", placeholder="e.g. BMRI, AAPL", key=f"f_tick_{p_prefix}_{market}").upper().strip()
        f_qty = st.number_input("Quantity (" + ("Lots" if market == "IDX" else "Shares") + ")", min_value=1.0, step=1.0, key=f"f_qty_{p_prefix}_{market}")
        f_price = st.number_input(f"Execution Price ({currency})", min_value=0.01, step=10.0 if market == "IDX" else 0.5, key=f"f_pr_{p_prefix}_{market}")

        shares = f_qty * 100 if market == "IDX" else f_qty
        trade_total = shares * f_price
        st.caption(f"Gross Transaction Value: {trade_total:,.2f} {currency}")

        if st.button("Submit Order", key=f"f_btn_{p_prefix}_{market}"):
            if not f_ticker:
                st.error("Please specify a ticker symbol.")
            elif f_type == "SELL" and holdings.get(f_ticker, {}).get("shares", 0) < shares:
                st.error("Cannot sell more shares than currently held.")
            else:
                supabase.table(db_table).insert({
                    "market": market,
                    "ticker": f_ticker,
                    "type": f_type,
                    "shares": shares,
                    "price_per_share": f_price,
                    "fee": 0
                }).execute()
                st.success(f"Recorded {f_type} order for {f_ticker} in {entity_name}.")
                st.rerun()

    # Edit / Delete Misinputs (Isolated Keys per Entity)
    with st.expander("🛠️ Modify Past Transactions"):
        if not transactions:
            st.caption("No trade records found for this account.")
        else:
            def format_tx_label(tx):
                date_str = tx["transaction_date"][:16].replace("T", " ")
                qty_dsp = f"{int(tx['shares']/100)} Lots" if market == "IDX" else f"{tx['shares']} Shares"
                return f"{date_str} | {tx['type']} {qty_dsp} {tx['ticker']} @ {tx['price_per_share']:,.2f}"

            tx_map = {format_tx_label(tx): tx for tx in transactions}
            selected_label = st.selectbox("Select Record", list(tx_map.keys()), key=f"sel_{p_prefix}_{market}")
            selected_tx = tx_map[selected_label]

            curr_units = selected_tx["shares"] / 100 if market == "IDX" else selected_tx["shares"]
            e1, e2 = st.columns(2)
            with e1:
                e_type = st.selectbox("Type", ["BUY", "SELL"], index=0 if selected_tx["type"] == "BUY" else 1, key=f"e_type_{p_prefix}_{market}")
                e_ticker = st.text_input("Ticker", value=selected_tx["ticker"], key=f"e_tick_{p_prefix}_{market}").upper().strip()
            with e2:
                e_qty = st.number_input("Units", min_value=1.0, value=float(curr_units), step=1.0, key=f"e_qty_{p_prefix}_{market}")
                e_price = st.number_input("Price", min_value=0.01, value=float(selected_tx["price_per_share"]), key=f"e_pr_{p_prefix}_{market}")

            new_shares = e_qty * 100 if market == "IDX" else e_qty
            b_save, b_del = st.columns(2)
            if b_save.button("💾 Save Update", key=f"btn_s_{p_prefix}_{market}"):
                supabase.table(db_table).update({
                    "ticker": e_ticker,
                    "type": e_type,
                    "shares": new_shares,
                    "price_per_share": e_price
                }).eq("id", selected_tx["id"]).execute()
                st.success("Updated.")
                st.rerun()

            if b_del.button("🗑️ Delete Record", key=f"btn_d_{p_prefix}_{market}"):
                supabase.table(db_table).delete().eq("id", selected_tx["id"]).execute()
                st.warning("Deleted.")
                st.rerun()

    # News Section
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

    # Recommendations Section
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

# Screened universes
idx_buys = [
    {"ticker": "BMRI", "setup": "Pullback to 20-Day EMA", "fundamentals": "ROE 18.2%, PBV 2.1x, Net Profit Growth +14% YoY", "technicals": "Holding 20 EMA support at Rp 6,850; RSI 48 curling upwards.", "entry": "Rp 6,800 - 6,900", "target": "Rp 7,450 (+8.5%)", "stop": "Rp 6,600 (-3.8%)"},
    {"ticker": "TLKM", "setup": "Value Rebound from Support", "fundamentals": "ROE 17.5%, PBV 2.4x, Dividend Yield 5.1%", "technicals": "Double-bottom setup on daily chart; MACD bullish crossover.", "entry": "Rp 2,850 - 2,900", "target": "Rp 3,180 (+10.2%)", "stop": "Rp 2,750 (-4.1%)"}
]

us_buys = [
    {"ticker": "NVDA", "setup": "Bull Flag Consolidation", "fundamentals": "Operating Margin 62%, YoY Revenue +122%", "technicals": "Consolidating above 20 EMA; volume drying up before breakout attempt.", "entry": "$118 - $122", "target": "$135 (+11.0%)", "stop": "$114 (-4.5%)"},
    {"ticker": "AMZN", "setup": "Ascending Triangle Breakout", "fundamentals": "AWS revenue acceleration +19%, Free Cash Flow expansion", "technicals": "Testing $190 resistance; RSI 54 showing steady accumulation.", "entry": "$185 - $188", "target": "$205 (+9.5%)", "stop": "$178 (-4.2%)"}
]

with tab_idx:
    render_market_dashboard("IDX", "IDR", idx_buys, active_table, entity_prefix)

with tab_us:
    render_market_dashboard("US", "USD", us_buys, active_table, entity_prefix)
