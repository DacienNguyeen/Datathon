import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from utils.load_data import load_orders, load_traffic

st.title("🔁 Executive Funnel (Advanced)")

# =========================
# LOAD DATA
# =========================
orders = load_orders()
traffic = load_traffic()

# =========================
# FILTERS
# =========================
st.sidebar.header("Filters")

date_range = st.sidebar.date_input(
    "Select date range",
    [orders['order_date'].min(), orders['order_date'].max()]
)

traffic_sources = ["All"] + list(traffic['traffic_source'].dropna().unique())

selected_source = st.sidebar.selectbox("Traffic Source", traffic_sources)

start_date, end_date = date_range

orders_f = orders[
    (orders['order_date'] >= pd.to_datetime(start_date)) &
    (orders['order_date'] <= pd.to_datetime(end_date))
]

traffic_f = traffic[
    (traffic['date'] >= pd.to_datetime(start_date)) &
    (traffic['date'] <= pd.to_datetime(end_date))
]

if selected_source != "All":
    traffic_f = traffic_f[traffic_f['traffic_source'] == selected_source]
    orders_f = orders_f[orders_f['order_source'] == selected_source]

# =========================
# METRIC FUNCTION
# =========================
def compute_metrics(o, t):
    sessions = t['sessions'].sum()
    total_orders = len(o)

    paid_orders = o[o['order_status'].isin(['paid', 'shipped', 'delivered', 'returned'])].shape[0]
    delivered_orders = o[o['order_status'].isin(['delivered', 'returned'])].shape[0]
    returned_orders = o[o['order_status'] == 'returned'].shape[0]

    def safe_div(a, b):
        return a / b if b != 0 else 0

    return {
        "sessions": sessions,
        "orders": total_orders,
        "paid": paid_orders,
        "delivered": delivered_orders,
        "returned": returned_orders,
        "conversion": safe_div(total_orders, sessions),
        "payment": safe_div(paid_orders, total_orders),
        "delivery": safe_div(delivered_orders, paid_orders),
        "return_rate": safe_div(returned_orders, delivered_orders)
    }

metrics = compute_metrics(orders_f, traffic_f)

# =========================
# PREVIOUS PERIOD (WoW)
# =========================
delta_days = (pd.to_datetime(end_date) - pd.to_datetime(start_date)).days

prev_start = pd.to_datetime(start_date) - pd.Timedelta(days=delta_days)
prev_end = pd.to_datetime(start_date)

orders_prev = orders[
    (orders['order_date'] >= prev_start) &
    (orders['order_date'] < prev_end)
]

traffic_prev = traffic[
    (traffic['date'] >= prev_start) &
    (traffic['date'] < prev_end)
]

metrics_prev = compute_metrics(orders_prev, traffic_prev)

# =========================
# KPI DISPLAY
# =========================
st.subheader("📊 Key Funnel Metrics")

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Conversion Rate",
    f"{metrics['conversion']:.2%}",
    delta=f"{metrics['conversion'] - metrics_prev['conversion']:.2%}"
)

col2.metric(
    "Payment Success",
    f"{metrics['payment']:.2%}",
    delta=f"{metrics['payment'] - metrics_prev['payment']:.2%}"
)

col3.metric(
    "Delivery Rate",
    f"{metrics['delivery']:.2%}",
    delta=f"{metrics['delivery'] - metrics_prev['delivery']:.2%}"
)

col4.metric(
    "Return Rate",
    f"{metrics['return_rate']:.2%}",
    delta=f"{metrics['return_rate'] - metrics_prev['return_rate']:.2%}"
)

# =========================
# FUNNEL CHART
# =========================
fig = go.Figure(go.Funnel(
    y=["Sessions", "Orders", "Paid", "Delivered", "Returned"],
    x=[metrics['sessions'], metrics['orders'], metrics['paid'], metrics['delivered'], metrics['returned']],
    textinfo="value+percent previous"
))

st.plotly_chart(fig, use_container_width=True)

# =========================
# FUNNEL TREND (TIME)
# =========================
st.subheader("📈 Funnel Trend Over Time")

orders_f['month'] = orders_f['order_date'].dt.to_period('M').astype(str)
traffic_f['month'] = traffic_f['date'].dt.to_period('M').astype(str)

monthly_orders = orders_f.groupby('month').size()
monthly_traffic = traffic_f.groupby('month')['sessions'].sum()

trend_df = pd.DataFrame({
    "sessions": monthly_traffic,
    "orders": monthly_orders
}).fillna(0)

trend_df['conversion'] = trend_df['orders'] / trend_df['sessions']

fig2 = go.Figure()

fig2.add_trace(go.Scatter(
    x=trend_df.index,
    y=trend_df['conversion'],
    mode='lines+markers',
    name='Conversion Rate'
))

st.plotly_chart(fig2, use_container_width=True)

# =========================
# DROP-OFF ANALYSIS
# =========================
st.subheader("⚠️ Drop-off Analysis")

drop1 = 1 - metrics['conversion']
drop2 = 1 - metrics['payment']
drop3 = 1 - metrics['delivery']

st.write(f"Sessions → Orders drop: {drop1:.2%}")
st.write(f"Orders → Paid drop: {drop2:.2%}")
st.write(f"Paid → Delivered drop: {drop3:.2%}")

# =========================
# AUTO INSIGHT
# =========================
st.subheader("🧠 Auto Insights")

if metrics['conversion'] < 0.02:
    st.warning("Low conversion rate → Check UX / traffic quality")

if metrics['payment'] < 0.8:
    st.warning("High payment drop-off → Payment friction")

if metrics['delivery'] < 0.9:
    st.warning("Delivery issues detected")

if metrics['return_rate'] > 0.2:
    st.error("High return rate → Product or expectation mismatch")