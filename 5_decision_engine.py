import streamlit as st
import pandas as pd
import numpy as np

from utils.load_data import load_orders, load_traffic

st.title("🧠 Decision Engine v2 — Causal-aware Insights")

# =========================
# LOAD DATA
# =========================
orders = load_orders()
traffic = load_traffic()
payments = pd.read_csv("data/payments.csv")

df = orders.merge(payments, on='order_id', how='left')

# =========================
# FILTER
# =========================
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

df_f = df[df['order_id'].isin(orders_f['order_id'])]

# =========================
# SEGMENT: traffic_source
# =========================
seg_orders = orders_f.groupby('order_source').agg({
    'order_id': 'count'
}).rename(columns={'order_id': 'orders'})

seg_traffic = traffic_f.groupby('traffic_source')['sessions'].sum()

seg = seg_orders.join(seg_traffic, how='left')

# attach revenue
rev_by_source = df_f.groupby('order_source')['payment_value'].sum()
seg = seg.join(rev_by_source)

# metrics
seg['conversion'] = seg['orders'] / seg['sessions']
seg['aov'] = seg['payment_value'] / seg['orders']

seg = seg.replace([np.inf, -np.inf], 0).fillna(0)

# =========================
# BASELINE (best segment)
# =========================
best_conv = seg['conversion'].max()
best_aov = seg['aov'].max()

# =========================
# CONFIDENCE
# =========================
seg['confidence'] = np.where(seg['sessions'] > 1000, "High",
                     np.where(seg['sessions'] > 300, "Medium", "Low"))

# =========================
# INSIGHT ENGINE
# =========================
insights = []

for idx, row in seg.iterrows():

    # Skip weak data
    if row['sessions'] < 100:
        continue

    # ---- Conversion gap ----
    if row['conversion'] < best_conv * 0.8:

        gap = best_conv - row['conversion']
        potential_orders = row['sessions'] * gap
        impact = potential_orders * row['aov']

        insights.append({
            "segment": idx,
            "problem": "Low Conversion vs Best Segment",
            "metric": f"{row['conversion']:.2%}",
            "benchmark": f"{best_conv:.2%}",
            "action": "Improve targeting / landing page",
            "impact": impact,
            "confidence": row['confidence']
        })

    # ---- AOV gap ----
    if row['aov'] < best_aov * 0.8:

        gap = best_aov - row['aov']
        uplift = gap * row['orders']

        insights.append({
            "segment": idx,
            "problem": "Low AOV vs Best Segment",
            "metric": f"{row['aov']:.2f}",
            "benchmark": f"{best_aov:.2f}",
            "action": "Upsell / bundle / pricing",
            "impact": uplift,
            "confidence": row['confidence']
        })

# =========================
# DISPLAY INSIGHTS
# =========================
st.subheader("🚨 Segment-level Insights")

if len(insights) == 0:
    st.success("No major issues detected 🎉")
else:
    df_ins = pd.DataFrame(insights)
    df_ins = df_ins.sort_values(by='impact', ascending=False)

    for _, row in df_ins.iterrows():
        st.warning(f"""
        **Segment: {row['segment']}**

        - Problem: {row['problem']}
        - Current: {row['metric']}
        - Benchmark: {row['benchmark']}
        - Action: {row['action']}
        - Estimated Impact: {row['impact']:,.0f}
        - Confidence: {row['confidence']}
        """)

# =========================
# SCENARIO SIMULATION
# =========================
st.subheader("🧪 Scenario Simulation")

scenario_conv = st.slider("Increase Conversion (%)", 0.0, 0.1, 0.01)
scenario_aov = st.slider("Increase AOV (%)", 0.0, 0.5, 0.05)

base_revenue = df_f['payment_value'].sum()

new_orders = len(orders_f) * (1 + scenario_conv)
new_aov = df_f['payment_value'].mean() * (1 + scenario_aov)

sim_revenue = new_orders * new_aov

delta = sim_revenue - base_revenue

st.metric("Simulated Revenue", f"{sim_revenue:,.0f}", delta=f"{delta:,.0f}")

# =========================
# PRIORITY TABLE
# =========================
st.subheader("📊 Insight Table")

if len(insights) > 0:
    st.dataframe(df_ins)