import streamlit as st
import pandas as pd
import plotly.express as px

from utils.load_data import load_orders

st.title("⭐ Customer Experience & Return Intelligence")

# =========================
# LOAD DATA
# =========================
orders = load_orders()

reviews = pd.read_csv("data/reviews.csv")
returns = pd.read_csv("data/returns.csv")
products = pd.read_csv("data/products.csv")

reviews['review_date'] = pd.to_datetime(reviews['review_date'])
returns['return_date'] = pd.to_datetime(returns['return_date'])

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

# =========================
# KPI SECTION
# =========================
st.subheader("📊 Experience KPIs")

delivered_orders = orders_f[
    orders_f['order_status'].isin(['delivered', 'returned'])
]['order_id'].nunique()

review_orders = reviews['order_id'].nunique()
return_orders = returns['order_id'].nunique()

def safe_div(a, b):
    return a / b if b != 0 else 0

avg_rating = reviews['rating'].mean()
review_rate = safe_div(review_orders, delivered_orders)
return_rate = safe_div(return_orders, delivered_orders)

col1, col2, col3 = st.columns(3)

col1.metric("Avg Rating", f"{avg_rating:.2f}")
col2.metric("Review Rate", f"{review_rate:.2%}")
col3.metric("Return Rate", f"{return_rate:.2%}")

# =========================
# RATING DISTRIBUTION
# =========================
st.subheader("⭐ Rating Distribution")

fig1 = px.histogram(
    reviews,
    x='rating',
    nbins=5,
    title="Rating Distribution"
)

st.plotly_chart(fig1, use_container_width=True)

# =========================
# RATING OVER TIME
# =========================
st.subheader("📅 Rating Trend")

reviews['month'] = reviews['review_date'].dt.to_period('M').astype(str)

rating_trend = reviews.groupby('month')['rating'].mean()

fig2 = px.line(
    rating_trend,
    x=rating_trend.index,
    y=rating_trend.values,
    title="Average Rating Over Time"
)

st.plotly_chart(fig2, use_container_width=True)

# =========================
# RETURN BY CATEGORY
# =========================
st.subheader("📦 Return Rate by Category")

returns_products = returns.merge(products, on='product_id', how='left')

return_cat = returns_products.groupby('category')['return_id'].count().reset_index()

fig3 = px.bar(
    return_cat,
    x='category',
    y='return_id',
    title="Returns by Category"
)

st.plotly_chart(fig3, use_container_width=True)

# =========================
# RETURN SEVERITY BY CATEGORY
# =========================
st.subheader("🔥 Return Severity by Category")

# total delivered per category (proxy via order_items nếu có)
try:
    order_items = pd.read_csv("data/order_items.csv")

    order_items_cat = order_items.merge(products, on='product_id', how='left')

    delivered_ids = orders_f[
        orders_f['order_status'].isin(['delivered', 'returned'])
    ]['order_id']

    delivered_items = order_items_cat[
        order_items_cat['order_id'].isin(delivered_ids)
    ]

    total_cat = delivered_items.groupby('category')['order_id'].count()

    return_cat = returns.merge(products, on='product_id', how='left') \
                        .groupby('category')['return_id'].count()

    severity = (return_cat / total_cat).fillna(0).reset_index()
    severity.columns = ['category', 'return_rate']

    fig = px.bar(
        severity.sort_values(by='return_rate', ascending=False),
        x='category',
        y='return_rate',
        title="Return Rate by Category"
    )

    st.plotly_chart(fig, use_container_width=True)

except:
    st.info("Need order_items for category-level return rate")

# =========================
# RETURN REASON
# =========================
st.subheader("❗ Return Reason Analysis")

reason_dist = returns['return_reason'].value_counts().reset_index()
reason_dist.columns = ['reason', 'count']

fig4 = px.pie(
    reason_dist,
    names='reason',
    values='count',
    title="Return Reasons"
)

st.plotly_chart(fig4, use_container_width=True)

# =========================
# REVIEW COVERAGE LOSS
# =========================
st.subheader("📉 Review Coverage Loss due to Returns")

delivered_orders = orders_f[
    orders_f['order_status'].isin(['delivered', 'returned'])
]['order_id'].nunique()

returned_orders = returns['order_id'].nunique()

reviewable_orders = delivered_orders - returned_orders

reviewed_orders = reviews['order_id'].nunique()

def safe_div(a, b):
    return a / b if b != 0 else 0

review_coverage = safe_div(reviewed_orders, reviewable_orders)
lost_review_rate = safe_div(returned_orders, delivered_orders)

col1, col2 = st.columns(2)

col1.metric("Review Coverage (Valid Orders)", f"{review_coverage:.2%}")
col2.metric("Lost Review Opportunity", f"{lost_review_rate:.2%}")

# =========================
# PRODUCT LEVEL ANALYSIS
# =========================
st.subheader("🧩 Product-level Issues")

product_return = returns.groupby('product_id')['return_id'].count().reset_index()
product_return = product_return.merge(products, on='product_id', how='left')

top_problem_products = product_return.sort_values(by='return_id', ascending=False).head(10)

fig6 = px.bar(
    top_problem_products,
    x='product_name',
    y='return_id',
    title="Top Returned Products"
)

st.plotly_chart(fig6, use_container_width=True)

