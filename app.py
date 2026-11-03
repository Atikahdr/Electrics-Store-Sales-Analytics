import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

from db import get_data

# 1. Page Configuration

st.set_page_config(
    page_title="Electronics Sales Intelligence",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)


# 2. Load Custom CSS

css_path = Path(__file__).parent / "assets" / "style.css"

with open(css_path, "r", encoding="utf-8") as file:
    st.markdown(
        f"<style>{file.read()}</style>",
        unsafe_allow_html=True
    )


# 3. Colos Palette

NAVY = "#20243A"
PURPLE = "#6659D9"
BLUE = "#4789E8"
TEAL = "#31A99B"
ORANGE = "#F2A65A"
MUTED = "#858BA3"


# 4. Data Date Range

data_query = """
SELECT
    MIN(order_date)::date AS min_date,
    Max(order_date)::date AS max_date
FROM staging.electronics_sales;
"""

date_df = get_data(data_query)

min_date = date_df.loc[0, "min_date"]
max_date = date_df.loc[0, "max_date"]


# 5. SIDEBAR

with st.sidebar:
    st.markdown("## 📊 Sales Intelligence")
    st.caption("ELECTRONIC SALES ANALYTICS")

    st.divider()

    st.markdown("### Monthly Analysis")
    st.write("Explore your sales performance.")

    selected_dates = st.date_input(
        "Select Date Range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )

    st.divider()

    st.caption("DATA SOURCE")
    st.write("PostgreSQL Database")
    st.caption("electronics_dw")

    st.divider()

    st.caption("PROJECT")
    st.write("Electronics Sales Intelligence")
    st.caption("Built with Python & Streamlit")

if len(selected_dates) != 2:
    st.warning("Please select a start date and end date.")
    st.stop()

start_date, end_date = selected_dates

if start_date > end_date:
    st.error("Start date must be earlier than end date.")
    st.stop()

params = {
    "start_date": start_date,
    "end_date": end_date
}

# 6. Dashboard Header

st.title("Monthly Analysis Dashboard")

st.markdown(
    f"""
    <p style="color:#858BA3; margin-top:-12px;">
        Sales performance overview from
        <b>{start_date}</b> to <b>{end_date}</b>
    </p>
    """,
    unsafe_allow_html=True
)

st.divider()

# 7. KPI Section

kpi_query = """
SELECT
    COALESCE(SUM(sales), 0) AS total_sales,
    COUNT(DISTINCT order_id) AS total_orders,
    COALESCE(SUM(quantity_ordered), 0) AS total_units,
    COALESCE(
        SUM(sales) / NULLIF(COUNT(DISTINCT order_id), 0),0
    ) AS average_order

FROM staging.electronics_sales
WHERE order_date >= CAST(:start_date AS date)
  AND order_date < CAST(:end_date AS date) + INTERVAL '1 day';
"""

kpi = get_data(kpi_query, params).iloc[0]

total_sales = float(kpi["total_sales"])
total_orders = int(kpi["total_orders"])
total_units = int(kpi["total_units"])
average_order = float(kpi["average_order"])

st.markdown("### Business Overview")

c1, c2, c3, c4 = st.columns(4)

c1.metric("Total Sales", f"${total_sales:,.2f}")
c2.metric("Total Orders", f"{total_orders:,}")
c3.metric("Units Sold", f"{total_units:,}")
c4.metric("Avg. Sales / Order", f"${average_order:,.2f}")


# 8. Monthly Sales Analysis

monthly_query = """
SELECT
    DATE_TRUNC('month', order_date)::date AS sales_month,
    SUM(sales) AS total_sales,
    SUM(quantity_ordered) AS units_sold,
    COUNT(*) AS transaction_lines
FROM staging.electronics_sales
WHERE order_date >= CAST(:start_date AS date)
  AND order_date < CAST(:end_date AS date) + INTERVAL '1 day'
GROUP BY DATE_TRUNC('month', order_date)
ORDER BY sales_month;
"""

monthly_df = get_data(monthly_query, params)

monthly_df["mom_growth_pct"] = (
    monthly_df["total_sales"].pct_change() * 100
).round(2)

st.markdown("### Monthly Sales Analysis")

left, right = st.columns([2, 1])

with left:
    with st.container(border=True):
        st.markdown("### Revenue Trend")

        fig_monthly = px.area(
            monthly_df,
            x="sales_month",
            y="total_sales",
            markers=True,
            color_discrete_sequence=[PURPLE]
        )

        fig_monthly.update_traces(
            line=dict(width=3),
            fillcolor="rgba(102,89,217,0.12)"
        )

        fig_monthly.update_layout(
            height=330,
            margin=dict(l=10, r=10, t=15, b=10),
            paper_bgcolor="white",
            plot_bgcolor="white",
            font_color=NAVY,
            xaxis_title=None,
            yaxis_title="Revenue (USD)",
            showlegend=False
        )

        fig_monthly.update_xaxes(showgrid=False)
        fig_monthly.update_yaxes(
            gridcolor="#EEF0F6",
            tickprefix="$",
            zeroline=False
        )

        st.plotly_chart(
            fig_monthly,
            use_container_width=True
        )

with right:
    with st.container(border=True):
        st.markdown("### Monthly Growth")

        growth_df = monthly_df.dropna(
            subset=["mom_growth_pct"]
        ).copy()

        if not growth_df.empty:
            fig_growth = px.bar(
                growth_df,
                x="sales_month",
                y="mom_growth_pct",
                color="mom_growth_pct",
                color_continuous_scale=["#E78B8B", "#E6E9F1", TEAL]
            )

            fig_growth.update_layout(
                height=330,
                margin=dict(l=5, r=5, t=15, b=10),
                paper_bgcolor="white",
                plot_bgcolor="white",
                font_color=NAVY,
                coloraxis_showscale=False,
                xaxis_title=None,
                yaxis_title="Growth (%)"
            )

            fig_growth.update_xaxes(showgrid=False)
            fig_growth.update_yaxes(
                gridcolor="#EEF0F6",
                zeroline=True,
                zerolinecolor="#AEB4C5",
                ticksuffix="%"
            )

            st.plotly_chart(
                fig_growth,
                use_container_width=True
            )
        else:
            st.info("Not enough monthly data to calculate growth.")


# 9. Product Performance

product_query = """
SELECT
    product,
    SUM(quantity_ordered) AS units_sold,
    SUM(sales) AS total_sales
FROM staging.electronics_sales
WHERE order_date >= CAST(:start_date AS date)
  AND order_date < CAST(:end_date AS date) + INTERVAL '1 day'
GROUP BY product
ORDER BY total_sales DESC
LIMIT 10;
"""

product_df = get_data(product_query, params)


# 10. City Performance

city_query = """
SELECT
    city,
    SUM(sales) AS total_sales
FROM staging.electronics_sales
WHERE order_date >= CAST(:start_date AS date)
  AND order_date < CAST(:end_date AS date) + INTERVAL '1 day'
GROUP BY city
ORDER BY total_sales DESC;
"""

city_df = get_data(city_query, params)

st.markdown("### Product & City Performance")

col_product, col_city = st.columns(2)

with col_product:
    with st.container(border=True):
        st.markdown("### Top 10 Products")

        fig_product = px.bar(
            product_df.sort_values("total_sales"),
            x="total_sales",
            y="product",
            orientation="h",
            color_discrete_sequence=[BLUE]
        )

        fig_product.update_layout(
            height=430,
            margin=dict(l=5, r=10, t=10, b=10),
            paper_bgcolor="white",
            plot_bgcolor="white",
            font_color=NAVY,
            xaxis_title="Revenue (USD)",
            yaxis_title=None,
            showlegend=False
        )

        fig_product.update_xaxes(
            gridcolor="#EEF0F6",
            tickprefix="$"
        )
        fig_product.update_yaxes(showgrid=False)

        st.plotly_chart(
            fig_product,
            use_container_width=True
        )

with col_city:
    with st.container(border=True):
        st.markdown("### City Performance")

        fig_city = px.bar(
            city_df.sort_values("total_sales"),
            x="total_sales",
            y="city",
            orientation="h",
            color_discrete_sequence=[TEAL]
        )

        fig_city.update_layout(
            height=430,
            margin=dict(l=5, r=10, t=10, b=10),
            paper_bgcolor="white",
            plot_bgcolor="white",
            font_color=NAVY,
            xaxis_title="Revenue (USD)",
            yaxis_title=None,
            showlegend=False   
        )

        fig_city.update_xaxes(
            gridcolor="#EEF0F6",
            tickprefix="$"
        )
        fig_city.update_yaxes(showgrid=False)

        st.plotly_chart(
            fig_city,
            use_container_width=True
        )


# 11. Hour Sales

hourly_query = """
SELECT
    EXTRACT(HOUR FROM order_date)::integer AS hour,
    SUM(sales) AS total_sales,
    SUM(quantity_ordered) AS units_sold
FROM staging.electronics_sales
WHERE order_date >= CAST(:start_date AS date)
  AND order_date < CAST(:end_date AS date) + INTERVAL '1 day'
GROUP BY EXTRACT(HOUR FROM order_date)
ORDER BY hour;
"""

hourly_df = get_data(hourly_query, params)

st.markdown("### Hourly Sales Analysis")

with st.container(border=True):
    fig_hourly = px.bar(
        hourly_df,
        x="hour",
        y="total_sales",
        color_discrete_sequence=[ORANGE]
    )

    fig_hourly.update_layout(
        height=300,
        margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor="white",
        plot_bgcolor="white",
        font_color=NAVY,
        xaxis_title="Hour of Day",
        yaxis_title="Revenue (USD)",
        showlegend=False
    )

    fig_hourly.update_xaxes(
        tickmode="linear",
        dtick=1,
        showgrid=False
    )


    fig_hourly.update_yaxes(
        gridcolor="#EEF0F6",
        tickprefix="$"
    )

    st.plotly_chart(
        fig_hourly,
        use_container_width=True
    )


# 12. Monthly Data Table

with st.expander("View Monthly Analysis Data"):
    display_df = monthly_df.copy()

    display_df["sales_month"] = pd.to_datetime(
        display_df["sales_month"]
    ).dt.strftime("%B %Y")

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True
    )


# 13. Footer

st.markdown(
    """
    <div class="dashboard-footer">
        Electronics Sales Intelligence |
        PostgreSQL · Python · Streamlit
    </div>
    """,
    unsafe_allow_html=True
)