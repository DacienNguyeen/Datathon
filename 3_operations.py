import streamlit as st
import pandas as pd
import plotly.express as px

from utils.load_data import load_orders

st.title("🚚 Fulfillment & Logistics Performance")

# =========================
# LOAD DATA
# =========================
orders = load_orders()

shipments = pd.read_csv("data/shipments.csv")
shipments['ship_date'] = pd.to_datetime(shipments['ship_date'])
shipments['delivery_date'] = pd.to_datetime(shipments['delivery_date'])

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

ship_f = shipments.merge(orders_f[['order_id']], on='order_id', how='inner')

# =========================
# PREP DATA
# =========================
ship_f['delivery_time'] = (ship_f['delivery_date'] - ship_f['ship_date']).dt.days

# =========================
# KPI SECTION
# =========================
st.subheader("📊 Fulfillment KPIs")

total_orders = len(orders_f)

shipped = orders_f[
    orders_f['order_status'].isin(['shipped', 'delivered', 'returned'])
].shape[0]

delivered = orders_f[
    orders_f['order_status'].isin(['delivered', 'returned'])
].shape[0]

def safe_div(a, b):
    return a / b if b != 0 else 0

shipping_rate = safe_div(shipped, total_orders)
delivery_rate = safe_div(delivered, shipped)
avg_delivery_time = ship_f['delivery_time'].mean()

# define on-time (<=3 days as proxy)
on_time_rate = (ship_f['delivery_time'] <= 3).mean()

col1, col2, col3, col4 = st.columns(4)

col1.metric("Shipping Rate", f"{shipping_rate:.2%}")
col2.metric("Delivery Rate", f"{delivery_rate:.2%}")
col3.metric("Avg Delivery Time", f"{avg_delivery_time:.2f} days")
col4.metric("On-time Rate", f"{on_time_rate:.2%}")

# =========================
# DELIVERY DISTRIBUTION
# =========================
st.subheader("⏱ Delivery Time Distribution")

fig1 = px.histogram(
    ship_f,
    x='delivery_time',
    nbins=20,
    title="Delivery Time Distribution (Days)"
)

st.plotly_chart(fig1, use_container_width=True)

# =========================
# DELIVERY BY REGION
# =========================
st.subheader("🌍 Delivery Performance by Region")

geo = pd.read_csv("data/geography.csv")

orders_geo = orders_f.merge(geo, on='zip', how='left')

ship_geo = ship_f.merge(orders_geo[['order_id', 'region']], on='order_id', how='left')

region_perf = ship_geo.groupby('region')['delivery_time'].mean().reset_index()

fig2 = px.bar(
    region_perf,
    x='region',
    y='delivery_time',
    title="Avg Delivery Time by Region"
)

st.plotly_chart(fig2, use_container_width=True)

# =========================
# DELAY vs RETURN
# =========================
st.subheader("⚠️ Delivery Delay vs Return")

returns = pd.read_csv("data/returns.csv")

returned_orders = returns['order_id'].unique()

ship_f['is_returned'] = ship_f['order_id'].isin(returned_orders)

delay_analysis = ship_f.groupby('delivery_time')['is_returned'].mean().reset_index()

fig3 = px.line(
    delay_analysis,
    x='delivery_time',
    y='is_returned',
    title="Return Rate vs Delivery Time"
)

st.plotly_chart(fig3, use_container_width=True)

# =========================
# TREND OVER TIME
# =========================
st.subheader("📅 Delivery Trend")

ship_f['month'] = ship_f['delivery_date'].dt.to_period('M').astype(str)

trend = ship_f.groupby('month')['delivery_time'].mean()

fig4 = px.line(
    trend,
    x=trend.index,
    y=trend.values,
    title="Avg Delivery Time Over Time"
)

st.plotly_chart(fig4, use_container_width=True)