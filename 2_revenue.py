import streamlit as st
import pandas as pd
import plotly.express as px

from utils.load_data import load_orders, load_traffic

st.title("💰 Conversion & Revenue Deep Dive")

# =========================
# LOAD DATA
# =========================
orders = load_orders()
traffic = load_traffic()

# (OPTIONAL nếu có order_items)
try:
    order_items = pd.read_csv("data/order_items.csv")
except:
    order_items = None

# =========================
# FILTER
# =========================
st.sidebar.header("Filters")

date_range = st.sidebar.date_input(
    "Select date range",
    [orders['order_date'].min(), orders['order_date'].max()]
)

start_date, end_date = date_range

orders_f = orders[
    (orders['order_date'] >= pd.to_datetime(start_date)) &
    (orders['order_date'] <= pd.to_datetime(end_date))
]

traffic_f = traffic[
    (traffic['date'] >= pd.to_datetime(start_date)) &
    (traffic['date'] <= pd.to_datetime(end_date))
]

# =========================
# MERGE PAYMENT DATA
# =========================
payments = pd.read_csv("data/payments.csv")
payments['order_id'] = payments['order_id']

df = orders_f.merge(payments, on='order_id', how='left')

# =========================
# SECTION A — KPI
# =========================
st.subheader("📊 Revenue Overview")

total_revenue = df['payment_value'].sum()
total_orders = len(df)

sessions = traffic_f['sessions'].sum()

def safe_div(a, b):
    return a / b if b != 0 else 0

aov = safe_div(total_revenue, total_orders)
rev_per_session = safe_div(total_revenue, sessions)

col1, col2, col3 = st.columns(3)

col1.metric("Total Revenue", f"{total_revenue:,.0f}")
col2.metric("AOV", f"{aov:,.2f}")
col3.metric("Revenue / Session", f"{rev_per_session:.2f}")

# =========================
# SECTION B — REVENUE BY SOURCE
# =========================
st.subheader("🌍 Revenue by Traffic Source")

rev_source = df.groupby('order_source')['payment_value'].sum().reset_index()

fig1 = px.bar(
    rev_source,
    x='order_source',
    y='payment_value',
    title="Revenue by Source"
)

st.plotly_chart(fig1, use_container_width=True)

# =========================
# SECTION C — CONVERSION vs VALUE
# =========================
st.subheader("📈 Conversion vs AOV by Source")

orders_by_source = df.groupby('order_source').agg({
    'order_id': 'count',
    'payment_value': 'sum'
}).rename(columns={'order_id': 'orders'})

traffic_by_source = traffic_f.groupby('traffic_source')['sessions'].sum()

combined = orders_by_source.join(traffic_by_source, how='left')

combined['conversion'] = combined['orders'] / combined['sessions']
combined['aov'] = combined['payment_value'] / combined['orders']

combined = combined.reset_index()

fig2 = px.scatter(
    combined,
    x='conversion',
    y='aov',
    size='orders',
    color='order_source',
    hover_name='order_source',
    title="Conversion vs AOV"
)

st.plotly_chart(fig2, use_container_width=True)

# =========================
# SECTION D — PROMOTION IMPACT
# =========================
st.subheader("🎯 Promotion Impact")

if order_items is not None:
    promo_flag = order_items.copy()
    promo_flag['has_promo'] = promo_flag['promo_id'].notna()

    promo_map = promo_flag.groupby('order_id')['has_promo'].max().reset_index()

    df = df.merge(promo_map, on='order_id', how='left')

    promo_group = df.groupby('has_promo')['payment_value'].mean().reset_index()

    fig3 = px.bar(
        promo_group,
        x='has_promo',
        y='payment_value',
        title="AOV: With vs Without Promo"
    )

    st.plotly_chart(fig3, use_container_width=True)

# =========================
# SECTION E — TIME TREND
# =========================
st.subheader("📅 Revenue Trend")

df['month'] = df['order_date'].dt.to_period('M').astype(str)

trend = df.groupby('month').agg({
    'payment_value': 'sum',
    'order_id': 'count'
}).rename(columns={'order_id': 'orders'})

trend['aov'] = trend['payment_value'] / trend['orders']

fig4 = px.line(
    trend,
    x=trend.index,
    y='payment_value',
    title="Revenue Over Time"
)

st.plotly_chart(fig4, use_container_width=True)

fig5 = px.line(
    trend,
    x=trend.index,
    y='aov',
    title="AOV Over Time"
)

st.plotly_chart(fig5, use_container_width=True)