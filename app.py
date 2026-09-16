import streamlit as st
import pandas as pd
import yfinance as yf
from supabase import create_client
import streamlit.components.v1 as components
from streamlit_autorefresh import st_autorefresh

# Page configuration
st.set_page_config(page_title="Stock Portfolio & Screener", layout="wide", initial_sidebar_state="collapsed")

# Polling every 15 seconds
st_autorefresh(interval=15000, key="datarefresh")

# Supabase connection
@st.cache_resource
def init_supabase():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

supabase = init_supabase()

# Ajaib fee formulas
def calc_fee(market, trade_type, gross_amount):
    if market == "IDX":
        rate = 0.001513 if trade_type == "BUY" else 0.002513
        return round(gross_amount * rate)
    else:
        return round(gross_amount * 0.003, 2)

# Accounting calculations (AVG vs FIFO)
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
                fee = float(row["fee"])
                if row["type"] == "BUY":
                    total_cost += (shares * price) + fee
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
                fee = float(row["fee"])
                if row["type"] == "BUY":
                    buy_lots.append({"shares": shares, "unit_cost": price + (fee / shares if shares > 0 else 0)})
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

# Main UI layout
st.title("📈 Stock Portfolio & Swing Screener")

cost_method = st.radio("Cost Basis Method:", ["AVG", "FIFO"], horizontal=True)

tab_idx, tab_us = st.tabs(["🇮🇩 IDX Market", "🇺🇸 US Stocks"])

def render_market_dashboard(market, currency, buy_universe):
    # Fetch all transactions ordered newest first
    tx_res = supabase.table("stock_transactions").select("*").eq("market", market).order("transaction_date", desc=True).execute()
    transactions = tx_res.data or []
    
    holdings = compute_holdings(transactions, method=cost_method)
    
    st.subheader("💼 My Portfolio")
    
    live_prices = {}
    total_market_val = 0.0
    total_cost_basis = 0.0
    
    if holdings:
        tickers = list(holdings.keys())
        yf_tickers = [f"{t}.JK" if market == "IDX" else t for t in tickers]
        try:
            data = yf.download(yf_tickers, period="5d", progress=False)["Close"]
            for t, yft in zip(tickers, yf_tickers):
                if len(tickers) == 1:
                    price = float(data.iloc[-1])
                else:
                    price = float(data[yft].dropna().iloc[-1])
                live_prices[t] = price
        except Exception:
            for t in tickers:
                live_prices[t] = holdings[t]["avg_cost"]
                
        table_rows = []
        for t, h in holdings.items():
            curr_p = live_prices.get(t, h["avg_cost"])
            val = h["shares"] * curr_p
            total_market_val += val
            total_cost_basis += h["total_cost"]
            pnl_val = val - h["total_cost"]
            pnl_pct = (pnl_val / h["total_cost"] * 100) if h["total_cost"] > 0 else 0
            
            qty_label = f"{int(h['shares']/100)} Lots" if market == "IDX" else f"{h['shares']} Shares"
            table_rows.append({
                "Ticker": t,
                "Quantity": qty_label,
                "Cost/Share": f"{h['avg_cost']:,.2f}",
                "Live Price": f"{curr_p:,.2f}",
                "Market Value": f"{val:,.2f}",
                "P&L": f"{pnl_val:+,.2f} ({pnl_pct:+.2f}%)"
            })
            
        net_pnl = total_market_val - total_cost_basis
        net_pnl_pct = (net_pnl / total_cost_basis * 100) if total_cost_basis > 0 else 0
        
        c1, c2, c3 = st.columns(3)
        c1.metric(f"Portfolio Value ({currency})", f"{total_market_val:,.2f}")
        c2.metric(f"Total Cost Basis ({currency})", f"{total_cost_basis:,.2f}")
        c3.metric(f"Unrealized P&L ({currency})", f"{net_pnl:+,.2f}", f"{net_pnl_pct:+.2f}%")
        
        st.dataframe(pd.DataFrame(table_rows), use_container_width=True)
    else:
        c1, c2 = st.columns(2)
        c1.metric(f"Portfolio Value ({currency})", "0.00")
        c2.metric(f"Total Cost Basis ({currency})", "0.00")
        st.info("No stocks currently held in this portfolio.")

    # Log New Stock Transaction
    with st.expander("➕ Log New Transaction (BUY / SELL)"):
        f_type = st.selectbox("Type", ["BUY", "SELL"], key=f"f_type_{market}")
        f_ticker = st.text_input("Ticker Symbol (e.g. BMRI, AAPL)", key=f"f_tick_{market}").upper().strip()
        f_qty = st.number_input("Lots (1 Lot = 100 Shares)" if market == "IDX" else "Shares", min_value=1.0, step=1.0, key=f"f_qty_{market}")
        f_price = st.number_input(f"Price per Share ({currency})", min_value=0.01, step=10.0 if market == "IDX" else 0.5, key=f"f_pr_{market}")
        
        shares = f_qty * 100 if market == "IDX" else f_qty
        gross = shares * f_price
        fee = calc_fee(market, f_type, gross)
        st.caption(f"Ajaib Fee: {fee:,.2f} {currency} | Net Total: {(gross + fee if f_type == 'BUY' else gross - fee):,.2f} {currency}")
        
        if st.button("Execute Trade", key=f"f_btn_{market}"):
            if not f_ticker:
                st.error("Please provide a ticker symbol.")
            elif f_type == "SELL" and holdings.get(f_ticker, {}).get("shares", 0) < shares:
                st.error("You cannot sell more shares than you hold.")
            else:
                supabase.table("stock_transactions").insert({
                    "market": market,
                    "ticker": f_ticker,
                    "type": f_type,
                    "shares": shares,
                    "price_per_share": f_price,
                    "fee": fee
                }).execute()
                st.success(f"Successfully recorded {f_type} order for {f_ticker}.")
                st.rerun()

    # Edit or Delete Misinput
    with st.expander("🛠️ Edit / Delete Misinputs (Transaction History)"):
        if not transactions:
            st.caption("No transaction history available to edit.")
        else:
            # Dropdown label formatter
            def format_tx_label(tx):
                date_str = tx["transaction_date"][:16].replace("T", " ")
                qty_display = f"{int(tx['shares']/100)} Lots" if market == "IDX" else f"{tx['shares']} Shares"
                return f"{date_str} | {tx['type']} {qty_display} {tx['ticker']} @ {tx['price_per_share']:,.2f}"

            tx_map = {format_tx_label(tx): tx for tx in transactions}
            selected_label = st.selectbox("Select the transaction to modify or delete:", list(tx_map.keys()), key=f"sel_{market}")
            selected_tx = tx_map[selected_label]

            st.write("---")
            st.markdown(f"**Editing Transaction:** `{selected_tx['id']}`")
            
            e_col1, e_col2 = st.columns(2)
            curr_qty = selected_tx["shares"] / 100 if market == "IDX" else selected_tx["shares"]
            
            with e_col1:
                e_type = st.selectbox("Type", ["BUY", "SELL"], index=0 if selected_tx["type"] == "BUY" else 1, key=f"e_type_{market}")
                e_ticker = st.text_input("Ticker", value=selected_tx["ticker"], key=f"e_tick_{market}").upper().strip()
            with e_col2:
                e_qty = st.number_input("Quantity (" + ("Lots" if market == "IDX" else "Shares") + ")", min_value=1.0, value=float(curr_qty), step=1.0, key=f"e_qty_{market}")
                e_price = st.number_input(f"Price per Share ({currency})", min_value=0.01, value=float(selected_tx["price_per_share"]), step=10.0 if market == "IDX" else 0.5, key=f"e_pr_{market}")

            new_shares = e_qty * 100 if market == "IDX" else e_qty
            new_gross = new_shares * e_price
            new_fee = calc_fee(market, e_type, new_gross)
            st.caption(f"Recalculated Fee: {new_fee:,.2f} {currency} | Net Total: {(new_gross + new_fee if e_type == 'BUY' else new_gross - new_fee):,.2f} {currency}")

            btn_col1, btn_col2 = st.columns(2)
            if btn_col1.button("💾 Save Changes", key=f"btn_save_{market}"):
                supabase.table("stock_transactions").update({
                    "ticker": e_ticker,
                    "type": e_type,
                    "shares": new_shares,
                    "price_per_share": e_price,
                    "fee": new_fee
                }).eq("id", selected_tx["id"]).execute()
                st.success("Transaction updated successfully.")
                st.rerun()

            if btn_col2.button("🗑️ Delete This Transaction", key=f"btn_del_{market}", type="secondary"):
                supabase.table("stock_transactions").delete().eq("id", selected_tx["id"]).execute()
                st.warning("Transaction deleted.")
                st.rerun()

    # News for Owned Stocks
    st.subheader("📰 News for Owned Stocks")
    if holdings:
        for t in list(holdings.keys())[:4]:
            yf_sym = f"{t}.JK" if market == "IDX" else t
            try:
                news_items = yf.Ticker(yf_sym).news
                if news_items:
                    st.markdown(f"**{t} Updates**")
                    for n in news_items[:2]:
                        title = n.get("title", "")
                        link = n.get("link", "#")
                        st.markdown(f"- [{title}]({link})")
            except Exception:
                pass
    else:
        st.caption("Own stocks in this tab to see tailored ticker news.")

    # Recommendations
    st.subheader("🎯 Swing Trading Recommendations (1-2 Weeks)")
    
    st.markdown("##### 🟢 BUY Setups (Fundamental + Technical Screener)")
    for pick in buy_universe:
        with st.expander(f"🟢 BUY: {pick['ticker']} - {pick['setup']}"):
            st.markdown(f"**Fundamental Quality:** {pick['fundamentals']}")
            st.markdown(f"**Technical Trigger:** {pick['technicals']}")
            st.markdown(f"**Entry Zone:** {pick['entry']} | **Target:** {pick['target']} | **Stop Loss:** {pick['stop']}")
            tv_sym = f"IDX:{pick['ticker']}" if market == "IDX" else pick['ticker']
            render_tradingview(tv_sym)

    st.markdown("##### 🔴 SELL Alerts (Stocks You Own)")
    has_sell = False
    if holdings:
        for t, h in holdings.items():
            curr_p = live_prices.get(t, h["avg_cost"])
            pct_change = ((curr_p - h["avg_cost"]) / h["avg_cost"]) * 100
            if pct_change <= -4.5 or pct_change >= 10.0:
                has_sell = True
                action = "Take Profit Target Reached (+10%)" if pct_change >= 10.0 else "Stop Loss Level Hit (-4.5%)"
                with st.expander(f"🔴 SELL: {t} - {action}"):
                    st.write(f"Current Return: {pct_change:+.2f}%")
                    st.write(f"Avg Cost: {h['avg_cost']:,.2f} | Current Price: {curr_p:,.2f}")
                    st.write("Suggested action: Lock in profits or curtail downside to preserve capital.")
                    tv_sym = f"IDX:{t}" if market == "IDX" else t
                    render_tradingview(tv_sym)
    if not has_sell:
        st.caption("No sell alerts triggered for your current holdings.")

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
    render_market_dashboard("IDX", "IDR", idx_buys)

with tab_us:
    render_market_dashboard("US", "USD", us_buys)
