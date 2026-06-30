import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Big Tech Stock Explorer",
    page_icon="📈",
    layout="wide",
)

# ── Header ───────────────────────────────────────────────────────────────────
st.title("📈 Big Tech Stock Explorer")
st.markdown(
    "Compare the price performance of the world's biggest tech companies "
    "over time — and see what your money could have grown into."
)
st.divider()

# ── Did you know? (Fetch MCP — real-world fact) ───────────────────────────────
st.info(
    "💡 **Did you know?** Apple became the first publicly traded US company "
    "to reach a $1 trillion valuation in 2018, and has since grown to over "
    "$4 trillion — making it the most valuable company in history."
)

# ── Load data ────────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    df = px.data.stocks()
    df["date"] = pd.to_datetime(df["date"])
    return df

df = load_data()

STOCK_INFO = {
    "GOOG": {"name": "Alphabet (Google)", "color": "#4285F4"},
    "AAPL": {"name": "Apple",             "color": "#555555"},
    "AMZN": {"name": "Amazon",            "color": "#FF9900"},
    "FB":   {"name": "Meta (Facebook)",   "color": "#1877F2"},
    "NFLX": {"name": "Netflix",           "color": "#E50914"},
    "MSFT": {"name": "Microsoft",         "color": "#00A4EF"},
}

TICKERS = list(STOCK_INFO.keys())

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("🔧 Controls")
    st.markdown("**Select stocks to compare:**")
    selected = st.multiselect(
        label="Stocks",
        options=TICKERS,
        default=["AAPL", "MSFT", "GOOG"],
        format_func=lambda t: f"{t} — {STOCK_INFO[t]['name']}",
    )

    st.divider()
    st.markdown("**Filter by date range:**")
    min_date = df["date"].min().date()
    max_date = df["date"].max().date()
    date_range = st.slider(
        "Date range",
        min_value=min_date,
        max_value=max_date,
        value=(min_date, max_date),
        format="MMM YYYY",
    )

    st.divider()
    st.markdown("**💰 Investment calculator:**")
    investment = st.number_input(
        "If I invested $…", min_value=100, max_value=1_000_000,
        value=1_000, step=100,
    )

    st.divider()
    st.caption("Data: Plotly built-in stock dataset (2018–2019)")
    st.caption("Built with Streamlit + Plotly")

# ── Guard: nothing selected ───────────────────────────────────────────────────
if not selected:
    st.warning("Please select at least one stock from the sidebar.")
    st.stop()

# ── Filter data ───────────────────────────────────────────────────────────────
mask = (df["date"].dt.date >= date_range[0]) & (df["date"].dt.date <= date_range[1])
filtered = df[mask].copy()

cols_needed = ["date"] + [t for t in selected if t in filtered.columns]
filtered = filtered[cols_needed]

# ── Normalize to 100 at start of period ───────────────────────────────────────
price_cols = [t for t in selected if t in filtered.columns]
start_prices = filtered[price_cols].iloc[0]
normalized = filtered.copy()
for col in price_cols:
    normalized[col] = (filtered[col] / start_prices[col]) * 100

# ── Growth metrics ────────────────────────────────────────────────────────────
start_vals = filtered[price_cols].iloc[0]
end_vals   = filtered[price_cols].iloc[-1]
growth_pct = ((end_vals - start_vals) / start_vals * 100).round(2)
best_ticker = growth_pct.idxmax()
worst_ticker = growth_pct.idxmin()
volatility = filtered[price_cols].pct_change().std() * 100

# ── KPI row ───────────────────────────────────────────────────────────────────
st.subheader("📊 Key Metrics")
kpi_cols = st.columns(4)

with kpi_cols[0]:
    st.metric(
        "🏆 Best Performer",
        f"{best_ticker}",
        f"+{growth_pct[best_ticker]:.1f}%",
    )
with kpi_cols[1]:
    st.metric(
        "📉 Lowest Growth",
        f"{worst_ticker}",
        f"{growth_pct[worst_ticker]:.1f}%",
        delta_color="inverse",
    )
with kpi_cols[2]:
    most_volatile = volatility.idxmax()
    st.metric(
        "⚡ Most Volatile",
        f"{most_volatile}",
        f"σ = {volatility[most_volatile]:.2f}%",
        delta_color="off",
    )
with kpi_cols[3]:
    best_final = investment * (end_vals[best_ticker] / start_vals[best_ticker])
    st.metric(
        f"💰 ${investment:,} → {best_ticker}",
        f"${best_final:,.0f}",
        f"+${best_final - investment:,.0f}",
    )

st.divider()

# ── Normalized line chart ─────────────────────────────────────────────────────
st.subheader("📈 Normalized Price Performance (Base = 100)")
fig_line = go.Figure()
for ticker in price_cols:
    fig_line.add_trace(go.Scatter(
        x=normalized["date"],
        y=normalized[ticker],
        name=f"{ticker} — {STOCK_INFO[ticker]['name']}",
        line=dict(color=STOCK_INFO[ticker]["color"], width=2.5),
        hovertemplate=f"<b>{ticker}</b><br>Date: %{{x|%b %d, %Y}}<br>Index: %{{y:.1f}}<extra></extra>",
    ))
fig_line.add_hline(y=100, line_dash="dot", line_color="gray", annotation_text="Start")
fig_line.update_layout(
    xaxis_title="Date",
    yaxis_title="Price Index (Start = 100)",
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    hovermode="x unified",
    height=420,
    margin=dict(l=10, r=10, t=30, b=10),
)
st.plotly_chart(fig_line, use_container_width=True)

# ── Bar chart of total growth ─────────────────────────────────────────────────
st.subheader("📊 Total Growth Over Selected Period")
bar_df = pd.DataFrame({
    "Ticker": price_cols,
    "Growth (%)": [growth_pct[t] for t in price_cols],
    "Company": [STOCK_INFO[t]["name"] for t in price_cols],
    "Color": [STOCK_INFO[t]["color"] for t in price_cols],
})
fig_bar = px.bar(
    bar_df, x="Ticker", y="Growth (%)",
    color="Ticker",
    color_discrete_map={t: STOCK_INFO[t]["color"] for t in price_cols},
    text="Growth (%)",
    hover_data=["Company"],
    labels={"Growth (%)": "Total Growth (%)"},
)
fig_bar.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
fig_bar.update_layout(
    showlegend=False,
    height=350,
    margin=dict(l=10, r=10, t=10, b=10),
)
st.plotly_chart(fig_bar, use_container_width=True)

# ── Investment calculator table ───────────────────────────────────────────────
st.subheader(f"💰 What if you invested ${investment:,}?")
inv_rows = []
for t in price_cols:
    final_val = investment * (end_vals[t] / start_vals[t])
    inv_rows.append({
        "Stock": f"{t} — {STOCK_INFO[t]['name']}",
        "Growth": f"{growth_pct[t]:+.1f}%",
        "Final Value": f"${final_val:,.0f}",
        "Gain / Loss": f"${final_val - investment:+,.0f}",
    })
inv_df = pd.DataFrame(inv_rows)
st.dataframe(inv_df, use_container_width=True, hide_index=True)

# ── Analyst note ──────────────────────────────────────────────────────────────
st.divider()
with st.expander("🧠 Analyst Note — How to read this dashboard"):
    st.markdown("""
**Normalized Price Index:** All stocks start at 100 on the first day of your selected period.
A value of 150 means the stock is up 50% from that starting point — regardless of its actual share price.
This lets you compare companies fairly even when their prices are very different.

**Volatility (σ):** Measured as the standard deviation of daily percentage returns.
A higher number means the stock moved more dramatically day-to-day — higher risk, potentially higher reward.

**Investment Calculator:** Shows the hypothetical outcome of investing a fixed amount at the start of the period.
Past performance does not guarantee future results.

*Data source: Plotly's built-in `px.data.stocks()` dataset, covering 2018–2019.*
    """)
