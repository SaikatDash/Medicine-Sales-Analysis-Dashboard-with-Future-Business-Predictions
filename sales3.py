import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO
import time

# Disable st_aggrid - use regular dataframe instead
AGGRID_AVAILABLE = False


# ---------- DATA LOAD ----------
df = pd.read_csv(
    "C:\\CODE\\python projects\\sir\\Medicine-Sales-Analysis-Dashboard-with-Future-Business-Predictions\\csv\\Mfg_Sales.csv"
)

df["MMYYYY"] = pd.to_datetime(df["MMYYYY"], format="%Y-%m", errors="coerce")
df = df.dropna(subset=["MMYYYY"])
df["Year"] = df["MMYYYY"].dt.year
df["Month"] = df["MMYYYY"].dt.strftime("%B")


# ---------- FINANCIAL YEAR MONTH ORDER ----------
fy_month_order = [
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
    "January",
    "February",
    "March",
]

df["Month"] = pd.Categorical(
    df["MMYYYY"].dt.strftime("%B"),
    categories=fy_month_order,
    ordered=True,
)

df["Month_num"] = df["MMYYYY"].dt.month
month_to_quarter = {
    1: "Q1",
    2: "Q1",
    3: "Q1",
    4: "Q2",
    5: "Q2",
    6: "Q2",
    7: "Q3",
    8: "Q3",
    9: "Q3",
    10: "Q4",
    11: "Q4",
    12: "Q4",
}
df["Quarter"] = df["Month_num"].map(month_to_quarter)

years = sorted(df["Year"].unique())
months = list(df["Month"].unique())
quarters = ["Q1", "Q2", "Q3", "Q4"]

# ---- Financial year labels (YYYY-YY) ----
base_years = years
fy_labels = [f"{y}-{str(y + 1)[-2:]}" for y in base_years]
label_to_year = dict(zip(fy_labels, base_years))
year_to_label = {v: k for k, v in label_to_year.items()}


# ---------- Diwsplay Grid with Export Options ----------


def remove_zero_values(data: pd.DataFrame, value_col: str) -> pd.DataFrame:
    """Remove rows where value column is 0 or empty"""
    return data[data[value_col] > 0].reset_index(drop=True)
def display_grid_with_export(data: pd.DataFrame, title: str, key_prefix: str):
    """Display data in grid format with CSV and Excel download options"""

    st.subheader(title)

    # Display as AgGrid if available, else as regular dataframe
    if AGGRID_AVAILABLE:
        try:
            gob = GridOptionsBuilder.from_dataframe(data)
            gob.configure_default_column(
                resizable=True, sortable=True, filter=True, editable=False
            )
            gob.configure_pagination(paginationAutoPageSize=True)
            grid_options = gob.build()

            AgGrid(
                data,
                gridOptions=grid_options,
                theme="alpine",
                fit_columns_on_grid_load=True,
                height=400,
                key=f"{key_prefix}_grid",
            )
        except Exception as e:
            st.dataframe(data, use_container_width=True)
    else:
        st.dataframe(data, use_container_width=True)

    # Download buttons
    col1, col2 = st.columns(2)

    with col1:
        # CSV Download
        csv = data.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Download CSV",
            data=csv,
            file_name=f"{key_prefix}.csv",
            mime="text/csv",
            key=f"{key_prefix}_csv",
        )

    with col2:
        # Excel Download
        try:
            buffer = BytesIO()
            with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
                data.to_excel(writer, index=False, sheet_name=title[:31])
            buffer.seek(0)
            st.download_button(
                label="Download Excel",
                data=buffer.getvalue(),
                file_name=f"{key_prefix}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key=f"{key_prefix}_excel",
            )
        except Exception as e:
            ("")


# ---------- TITLE ----------
st.markdown(
    "<h1 style='color:violet; font-weight:1000;'>Analytical Dashboard</h1>",
    unsafe_allow_html=True,
)

# ---------- SESSION ----------
if "page" not in st.session_state:
    st.session_state.page = "dashboard"
if "fy_start" not in st.session_state:
    st.session_state.fy_start = base_years[-1]

# ---------- CSS ----------
st.markdown(
    """
    <style>
    .nav-card {
        border-radius: 22px;
        padding: 0;
        margin: 0.5rem 0;
        background: #3169ff;
        box-shadow: 0 4px 10px rgba(0,0,0,0.35);
    }
    .nav-card-header {
        height: 34px;
        border-radius: 22px 22px 0 0;
        background: linear-gradient(90deg, #000000, #202020);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 14px;
        font-weight: 600;
        color: #ffffff;
        letter-spacing: 0.5px;
    }
    .nav-card-body {
        padding: 0.55rem 0.9rem 0.75rem 0.9rem;
        border-radius: 0 0 22px 22px;
        color: #f5f5f5;
        font-size: 13px;
    }
    .nav-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 16px rgba(0,0,0,0.55);
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <style>
    .insight-card {
        background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
        border-radius: 18px;
        padding: 18px;
        height: 10vh
        width: 8vw
        color: white;
        box-shadow: 0 6px 16px rgba(0,0,0,0.4);
        text-align: center;
    }
    .insight-title {
        font-size: 14px;
        color: #d1d1d1;
    }
    .insight-value {
        font-size: 28px;
        font-weight: 800;
        color: #00ffcc;
        margin-top: 6px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------- SIDEBAR ----------
st.sidebar.markdown(
    "<h3 style='color:#ffd95a; margin-bottom:0.3rem;'>Way of Analysis</h3>",
    unsafe_allow_html=True,
)

menu = {
    "Quarter vs Year Comparison": "comparison",
    "Business Analysis": "business",
    "Branch–Business Analysis": "branchbusiness",
    "Product–Month Analysis": "prodmonth",
    "Credit Note Analysis": "credit",
    "Branch Business-Comparison": "branchcomparison",
    "Product Category-Comparison": "productcategorycomparison",
}

for title, key in menu.items():
    with st.sidebar.container():
        st.markdown("<div class='nav-card'>", unsafe_allow_html=True)
        st.markdown(
            f"<div class='nav-card-header'>{title}</div>",
            unsafe_allow_html=True,
        )
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(
                "<div class='nav-card-body'>Click to explore detailed insights.</div>",
                unsafe_allow_html=True,
            )
        with col2:
            if st.button("Go", key=f"btn_{key}"):
                st.session_state.page = key
        st.markdown("</div>", unsafe_allow_html=True)


# =====================================================================
# PAGE 1: QUARTER COMPARISON
# =====================================================================
if st.session_state.page == "comparison":
    st.header("Sales Comparison")

    selected_quarter = st.selectbox("Select Quarter for Comparison", quarters)

    default_years = years[:2]
    default_labels = [year_to_label[y] for y in default_years]

    selected_fy_labels_for_cmp = st.multiselect(
        "Select Financial Years for Comparison",
        fy_labels,
        default=default_labels,
    )

    if len(selected_fy_labels_for_cmp) > 3:
        st.warning("You can select up to 3 financial years only.")
        selected_fy_labels_for_cmp = selected_fy_labels_for_cmp[:3]

    selected_years_for_cmp = [label_to_year[lbl] for lbl in selected_fy_labels_for_cmp]

    filtered_df = df[
        (df["Quarter"] == selected_quarter) & (df["Year"].isin(selected_years_for_cmp))
    ]
    compare_chart = filtered_df.groupby("Year")["ActAmt"].sum().reset_index()
    compare_chart = remove_zero_values(compare_chart, "ActAmt")

    if not compare_chart.empty:
        compare_chart["FinancialYear"] = compare_chart["Year"].map(year_to_label)

    if compare_chart.empty:
        st.warning("No data available for the selected filter.")
    else:
        # Chart
        fig_cmp = px.bar(
            compare_chart,
            x="FinancialYear",
            y="ActAmt",
            title=f"Sales Comparison for {selected_quarter} (by Financial Year)",
            color="FinancialYear",
            text="ActAmt",
        )
        fig_cmp.update_traces(text=None)
        st.plotly_chart(fig_cmp, use_container_width=True)

        # Grid with export
        display_grid_with_export(compare_chart, "Sales Data Table", "comparison_data")

        best_row = compare_chart.loc[compare_chart["ActAmt"].idxmax()]
        best_fy_label = best_row["FinancialYear"]
        best_value = best_row["ActAmt"]

        st.markdown(
            f"""
            <hr>
            <p style="font-size:22px; font-weight:700;">
            Highest sales in <span style="color:#00ff88;">{selected_quarter}</span>
            were in <span style="color:#ffdd55;">{best_fy_label}</span> with
            <span style="color:#00c0ff;">₹{best_value:,.0f}</span>.
            </p>
            """,
            unsafe_allow_html=True,
        )


# =====================================================================
# PAGE 2: BUSINESS Analysis
# =====================================================================
elif st.session_state.page == "business":
    st.header("Business Analysis")

    selected_fy_labels_business = st.multiselect(
        "Select exactly 3 Financial Year sessions",
        fy_labels,
        default=fy_labels[:3] if len(fy_labels) >= 3 else fy_labels,
        max_selections=3,
    )

    if len(selected_fy_labels_business) < 3 :
        st.warning("Please select exactly 3 financial year sessions.")
        st.stop()

    selected_fy_years_business = [
        label_to_year[lbl] for lbl in selected_fy_labels_business
    ]



    primary_fy_year = selected_fy_years_business[0]
    year_df = df[df["Year"] == primary_fy_year]

    # ---------- YEAR INSIGHTS ----------
    total_sales = year_df["ActAmt"].sum() + year_df["CNAmt"].sum()

    best_month = (
        year_df.groupby("Month")["ActAmt"].sum().idxmax()
        if not year_df.empty else "N/A"
    )

    top_branch = (
        year_df.groupby("BranchName")["ActAmt"].sum().idxmax()
        if not year_df.empty else "N/A"
    )

    top_product = (
        year_df.groupby("MKTType")["ActAmt"].sum().idxmax()
        if not year_df.empty else "N/A"
    )

    st.subheader(f"📌 Financial Year Snapshot — {year_to_label[primary_fy_year]}")

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.markdown(
            f"""
            <div class="insight-card">
                <div class="insight-title">💰 Total Sales</div>
                <div class="insight-value">₹{total_sales:,.0f}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c2:
        st.markdown(
            f"""
            <div class="insight-card">
                <div class="insight-title">🗓 Best Month</div>
                <div class="insight-value">{best_month}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c3:
        st.markdown(
            f"""
            <div class="insight-card">
                <div class="insight-title">🏢 Top Branch</div>
                <div class="insight-value">{top_branch}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c4:
        st.markdown(
            f"""
            <div class="insight-card">
                <div class="insight-title">🧪 Top Product</div>
                <div class="insight-value">{top_product}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("---")


    month_act = year_df.groupby("Month")["ActAmt"].sum().reset_index()
    month_act = remove_zero_values(month_act, "ActAmt")
    month_cn = year_df.groupby("Month")["CNAmt"].sum().reset_index()
    month_cn = remove_zero_values(month_cn, "CNAmt")
    month_total = (
        year_df.groupby("Month")[["ActAmt", "CNAmt"]].sum().reset_index()
    )
    month_total["TotalAmt"] = month_total["ActAmt"] + month_total["CNAmt"]
    month_total = remove_zero_values(month_total, "TotalAmt")

    st.subheader("Choose Analysis Type")

    analysis_type = st.radio(
        "Select View",
        [
            "Total Month-wise Analysis",
            "Month-wise Actual Sales",
            "Month-wise Credit Note Analysis",
        ],
        index=0,
        horizontal=True,
    )

    if analysis_type == "Total Month-wise Analysis":
        fig = px.bar(
            month_total,
            x="Month",
            y="TotalAmt",
            title="Total Month-wise Amount",
            color="Month",
            text="TotalAmt",
        )
        fig.update_traces(text=None)
        st.plotly_chart(fig, use_container_width=True)

        display_grid_with_export(
            month_total, "Total Sales by Month", "business_total_month"
        )

        if not month_total.empty:
            top_row = month_total.sort_values("TotalAmt", ascending=False).iloc[0]
            st.markdown(
                f"""
                <hr>
                <p style="font-size:20px; font-weight:650;">
                Highest total: <span style="color:#00ff88;">{top_row['Month']}</span>
                with <span style="color:#00c0ff;">₹{top_row['TotalAmt']:,.0f}</span>
                </p>
                """,
                unsafe_allow_html=True,
            )

    elif analysis_type == "Month-wise Actual Sales":
        fig = px.bar(
            month_act,
            x="Month",
            y="ActAmt",
            title="Month-wise Actual Sales",
            color="Month",
            text="ActAmt",
        )
        fig.update_traces(text=None)
        st.plotly_chart(fig, use_container_width=True)

        display_grid_with_export(
            month_act, "Actual Sales by Month", "business_actual_month"
        )

        if not month_act.empty:
            top_row = month_act.sort_values("ActAmt", ascending=False).iloc[0]
            st.markdown(
                f"""
                <hr>
                <p style="font-size:20px; font-weight:650;">
                Best Sales Month: <span style="color:#00ff88;">{top_row['Month']}</span>
                with <span style="color:#00c0ff;">₹{top_row['ActAmt']:,.0f}</span>
                </p>
                """,
                unsafe_allow_html=True,
            )

    elif analysis_type == "Month-wise Credit Note Analysis":
        fig = px.bar(
            month_cn,
            x="Month",
            y="CNAmt",
            title="Month-wise Credit Notes",
            color="Month",
            text="CNAmt",
        )
        fig.update_traces(text=None)
        st.plotly_chart(fig, use_container_width=True)

        display_grid_with_export(
            month_cn, "Credit Notes by Month", "business_cn_month"
        )

        if not month_cn.empty:
            top_row = month_cn.sort_values("CNAmt", ascending=False).iloc[0]
            st.markdown(
                f"""
                <hr>
                <p style="font-size:20px; font-weight:650;">
                Highest credit note: <span style="color:#00ff88;">{top_row['Month']}</span>
                with <span style="color:#ff6b6b;">₹{top_row['CNAmt']:,.0f}</span>
                </p>
                """,
                unsafe_allow_html=True,
            )


# =====================================================================
# PAGE 3: PRODUCT–MONTH
# =====================================================================
elif st.session_state.page == "prodmonth":
    year_df = df[df["Year"] == st.session_state.fy_start]
    current_fy_label = year_to_label.get(
        st.session_state.fy_start, f"{st.session_state.fy_start}"
    )

    st.header("Product–Month Analysis")

    col1, col2 = st.columns(2)

    with col1:
        selected_categories = st.multiselect(
            "Select Product Category (MKTType)",
            options=sorted(year_df["MKTType"].unique()),
            default=sorted(year_df["MKTType"].unique()),
        )

    with col2:
        selected_months = st.multiselect(
            "Select Month(s)",
            options=sorted(year_df["Month"].unique()),
            default=sorted(year_df["Month"].unique()),
        )

    analysis_level = st.radio(
        "Choose Analysis Level",
        [
            "Month-wise Product Category Sales",
            "Yearly Product Category Sales",
        ],
        horizontal=True,
    )

    chart_type = st.selectbox(
        "Choose Chart Type",
        ["Bar", "Line", "Pie", "Area"],
        key="prodmonth_chart_type",
    )

    filtered_df = year_df[
        (year_df["MKTType"].isin(selected_categories))
        & (year_df["Month"].isin(selected_months))
    ]

    if filtered_df.empty:
        st.warning("No data available for the selected filters.")
    else:
        if analysis_level == "Month-wise Product Category Sales":
            agg_df = (
                filtered_df.groupby(["Month", "MKTType"])["ActAmt"]
                .sum()
                .reset_index()
            )
            agg_df = remove_zero_values(agg_df, "ActAmt")
            title = "Month-wise Product Category Sales"
            x_col = "Month"
            color_col = "MKTType"
        else:
            agg_df = (
                filtered_df.groupby("MKTType")["ActAmt"].sum().reset_index()
            )
            agg_df = remove_zero_values(agg_df, "ActAmt")
            title = "Yearly Product Category Sales"
            x_col = "MKTType"
            color_col = "MKTType"

        if chart_type == "Bar":
            fig = px.bar(agg_df, x=x_col, y="ActAmt", color=color_col, title=title)
        elif chart_type == "Line":
            fig = px.line(
                agg_df,
                x=x_col,
                y="ActAmt",
                color=color_col,
                markers=True,
                title=title,
            )
        elif chart_type == "Pie":
            pie_df = agg_df.groupby(color_col)["ActAmt"].sum().reset_index()
            fig = px.pie(pie_df, names=color_col, values="ActAmt", title=title)
        elif chart_type == "Area":
            fig = px.area(
                agg_df,
                x=x_col,
                y="ActAmt",
                color=color_col,
                title=title,
            )

        fig.update_traces(text=None)
        st.plotly_chart(fig, use_container_width=True)

        display_grid_with_export(agg_df, "Product Sales Data", "prodmonth_data")

        top_row = agg_df.sort_values("ActAmt", ascending=False).iloc[0]
        st.markdown(
            f"""
            <hr>
            <p style="font-size:20px; font-weight:650;">
            Highest sales: <span style="color:#00ff88;">{top_row[color_col]}</span>
            with <span style="color:#00c0ff;">₹{top_row['ActAmt']:,.0f}</span>
            </p>
            """,
            unsafe_allow_html=True,
        )


# =====================================================================
# PAGE 4: BRANCH–BUSINESS (MONTH)
# =====================================================================
elif st.session_state.page == "branchbusiness":
    year_df = df[df["Year"] == st.session_state.fy_start]
    current_fy_label = year_to_label.get(
        st.session_state.fy_start, f"{st.session_state.fy_start}"
    )

    st.header("Branch–Month Analysis")

    branch_list = sorted(year_df["BranchName"].unique())
    month_list = list(df["Month"].unique())

    colA, colB = st.columns(2)
    with colA:
        selected_branch = st.selectbox("Select Branch", branch_list)

    with colB:
        selected_months = st.multiselect("Select Month(s)", month_list, default=month_list)

    metric_type = st.radio(
        "Choose Analysis Type",
        [
            "Total Branch Month-wise Sales",
            "Actual Branch Month-wise Sales",
            "Credit Note Branch Month-wise Sales",
        ],
        index=0,
        horizontal=True,
    )

    chart_type = st.selectbox(
        "Choose Chart Type",
        ["Bar", "Line", "Pie", "Area"],
        key="branch_chart_type",
    )

    branch_month = (
        year_df[
            (year_df["BranchName"] == selected_branch)
            & (year_df["Month"].isin(selected_months))
        ]
        .groupby(["Month"])[["ActAmt", "CNAmt"]]
        .sum()
        .reset_index()
    )

    branch_month["TotalAmt"] = branch_month["ActAmt"] + branch_month["CNAmt"]

    if metric_type == "Total Branch Month-wise Sales":
        value_col = "TotalAmt"
        title = f"Total Sales — {selected_branch}"
    elif metric_type == "Actual Branch Month-wise Sales":
        value_col = "ActAmt"
        title = f"Actual Sales — {selected_branch}"
    else:
        value_col = "CNAmt"
        title = f"Credit Notes — {selected_branch}"

    # ---------- BRANCH INSIGHTS ----------
    branch_total = branch_month[value_col].sum()

    best_month_branch = (
        branch_month.sort_values(value_col, ascending=False).iloc[0]["Month"]
        if not branch_month.empty else "N/A"
    )

    st.subheader(f"📌 Branch Performance — {selected_branch}")

    c1, c2 = st.columns(2)

    with c1:
        st.markdown(
            f"""
            <div class="insight-card">
                <div class="insight-title">💰 Total {title}</div>
                <div class="insight-value">₹{branch_total:,.0f}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c2:
        st.markdown(
            f"""
            <div class="insight-card">
                <div class="insight-title">🏆 Best Month</div>
                <div class="insight-value">{best_month_branch}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("---")
    



    

    if not branch_month.empty and branch_month[value_col].sum() > 0:

        if chart_type == "Bar":
            fig = px.bar(branch_month, x="Month", y=value_col, title=title, color="Month")
        elif chart_type == "Line":
            fig = px.line(
                branch_month,
                x="Month",
                y=value_col,
                title=title,
                markers=True,
            )
        elif chart_type == "Pie":
            fig = px.pie(
                branch_month,
                names="Month",
                values=value_col,
                title=title,
            )
        elif chart_type == "Area":
            fig = px.area(
                branch_month,
                x="Month",
                y=value_col,
                title=title,
            )

        fig.update_traces(text=None)
        st.plotly_chart(fig, use_container_width=True)

        display_grid_with_export(
            branch_month, f"Branch Sales - {selected_branch}", "branch_month_data"
        )

        top_row = branch_month.sort_values(value_col, ascending=False).iloc[0]

        st.markdown(
            f"""
            <hr>
            <p style="font-size:20px; font-weight:650;">
            Highest for <b>{selected_branch}</b>: <span style="color:#00ff88;">{top_row['Month']}</span>
            with <span style="color:#00c0ff;">₹{top_row[value_col]:,.0f}</span>
            </p>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.warning("No data available for the selected filters.")

# ==============================================================================
# PAGE 5: CREDIT NOTE
# ==============================================================================
elif st.session_state.page == "credit":

    st.header("Financial Year Business Analysis")

    fy_options = sorted(years)
    fy_labels_sorted = [year_to_label[y] for y in fy_options]

    selected_fy_labels = st.multiselect(
        "Select up to 3 Consecutive Financial Years",
        fy_labels_sorted,
        default=[fy_labels_sorted[-1]],
    )

    if len(selected_fy_labels) > 3:
        st.warning("You can select a maximum of 3 financial years.")
        selected_fy_labels = selected_fy_labels[:3]

    selected_fy_years = sorted([label_to_year[lbl] for lbl in selected_fy_labels])

    if len(selected_fy_years) > 1:
        if selected_fy_years != list(
            range(
                selected_fy_years[0],
                selected_fy_years[0] + len(selected_fy_years),
            )
        ):
            st.error("Please select consecutive financial years only.")
            st.stop()

    analysis_type = st.radio(
        "Choose Month-wise Analysis Type",
        [
            "Month-wise Actual Sales",
            "Month-wise Credit Note Analysis",
            "Month-wise Total Sales",
        ],
        horizontal=True,
    )

    cumulative_view = st.checkbox("Show Cumulative Analysis")

    fy_df = df[df["Year"].isin(selected_fy_years)]

    if analysis_type == "Month-wise Actual Sales":
        value_col = "ActAmt"
        title_prefix = "Actual Sales"
    elif analysis_type == "Month-wise Credit Note Analysis":
        value_col = "CNAmt"
        title_prefix = "Credit Notes"
    else:
        fy_df = fy_df.copy()
        fy_df["TotalAmt"] = fy_df["ActAmt"] + fy_df["CNAmt"]
        value_col = "TotalAmt"
        title_prefix = "Total Sales"

    month_fy = fy_df.groupby(["Year", "Month"])[value_col].sum().reset_index()

    month_fy["FinancialYear"] = month_fy["Year"].map(year_to_label)

    if cumulative_view:
        month_fy_plot = month_fy.groupby("Month")[value_col].sum().reset_index()
        fig = px.bar(
            month_fy_plot,
            x="Month",
            y=value_col,
            title=f"Cumulative Month-wise {title_prefix}",
            color="Month",
        )
        display_grid_with_export(month_fy_plot, "Cumulative Data", "credit_cumulative")
    else:
        month_fy_plot = month_fy
        fig = px.bar(
            month_fy_plot,
            x="Month",
            y=value_col,
            color="FinancialYear",
            barmode="group",
            title=f"Month-wise {title_prefix} Comparison",
        )
        display_grid_with_export(
            month_fy_plot, "Financial Year Comparison Data", "credit_fy_data"
        )

    fig.update_traces(text=None)
    st.plotly_chart(fig, use_container_width=True)

    if not month_fy.empty:
        top_row = month_fy.sort_values(value_col, ascending=False).iloc[0]
        st.markdown(
            f"""
            <hr>
            <p style="font-size:18px; font-weight:600;">
            Highest {title_prefix.lower()}: <span style="color:#00ff88;">{top_row['Month']}</span>
            with <span style="color:#00c0ff;">₹{top_row[value_col]:,.0f}</span>
            </p>
            """,
            unsafe_allow_html=True,
        )



# ==============================================================================
# PAGE 6: BRANCH BUSINESS
# ==============================================================================
elif st.session_state.page == "branchcomparison":

    st.header("Branch Business Comparison (Financial Year-wise)")

    branch_list = sorted(df["BranchName"].unique())
    selected_branch = st.selectbox("Select Branch", branch_list)

    fy_labels_sorted = [year_to_label[y] for y in sorted(years)]

    selected_fy_labels = st.multiselect(
        "Select up to 3 Consecutive Financial Years",
        fy_labels_sorted,
        default=[fy_labels_sorted[-1]],
    )

    if len(selected_fy_labels) > 3:
        st.warning("You can select a maximum of 3 financial years.")
        selected_fy_labels = selected_fy_labels[:3]

    selected_fy_years = sorted([label_to_year[lbl] for lbl in selected_fy_labels])

    if len(selected_fy_years) > 1:
        if selected_fy_years != list(
            range(
                selected_fy_years[0],
                selected_fy_years[0] + len(selected_fy_years),
            )
        ):
            st.error("Please select consecutive financial years only.")
            st.stop()

    analysis_type = st.radio(
        "Choose Month-wise Branch Analysis Type",
        [
            "Month-wise Actual Branch Sales",
            "Month-wise Branch Credit Note Analysis",
            "Month-wise Branch Total Sales",
        ],
        horizontal=True,
    )

    cumulative_view = st.checkbox("Show Cumulative Analysis")

    branch_df = df[
        (df["BranchName"] == selected_branch) & (df["Year"].isin(selected_fy_years))
    ]

    if analysis_type == "Month-wise Actual Branch Sales":
        value_col = "ActAmt"
        title_prefix = "Actual Sales"
    elif analysis_type == "Month-wise Branch Credit Note Analysis":
        value_col = "CNAmt"
        title_prefix = "Credit Notes"
    else:
        branch_df = branch_df.copy()
        branch_df["TotalAmt"] = branch_df["ActAmt"] + branch_df["CNAmt"]
        value_col = "TotalAmt"
        title_prefix = "Total Sales"

    month_fy_branch = (
        branch_df.groupby(["Year", "Month"])[value_col].sum().reset_index()
    )

    month_fy_branch["FinancialYear"] = month_fy_branch["Year"].map(year_to_label)

    if cumulative_view:
        cum_df = month_fy_branch.groupby("Month")[value_col].sum().reset_index()

        fig = px.bar(
            cum_df,
            x="Month",
            y=value_col,
            title=f"Cumulative {title_prefix} — {selected_branch}",
            color="Month",
        )
        display_grid_with_export(cum_df, "Cumulative Branch Data", "branch_cumulative")
    else:
        fig = px.bar(
            month_fy_branch,
            x="Month",
            y=value_col,
            color="FinancialYear",
            barmode="group",
            title=f"Month-wise {title_prefix} — {selected_branch}",
        )
        display_grid_with_export(
            month_fy_branch, "Branch FY Comparison Data", "branch_fy_data"
        )

    fig.update_traces(text=None)
    st.plotly_chart(fig, use_container_width=True)

    if not month_fy_branch.empty:
        top_row = month_fy_branch.sort_values(value_col, ascending=False).iloc[0]
        st.markdown(
            f"""
            <hr>
            <p style="font-size:18px; font-weight:600;">
            Peak {title_prefix.lower()} for <b>{selected_branch}</b>: <span style="color:#00ff88;">{top_row['Month']}</span>
            ({top_row['FinancialYear']}) with <span style="color:#00c0ff;">₹{top_row[value_col]:,.0f}</span>
            </p>
            """,
            unsafe_allow_html=True,
        )


# ==============================================================================
# PAGE 7: PRODUCT CATEGORY – COMPARISON
# ==============================================================================
elif st.session_state.page == "productcategorycomparison":

    st.header("Product Category Comparison (Branch-wise)")

    branch_list = sorted(df["BranchName"].unique())
    selected_branch = st.selectbox("Select Branch", branch_list)

    fy_labels_sorted = [year_to_label[y] for y in sorted(years)]

    selected_fy_labels = st.multiselect(
        "Select up to 3 Consecutive Financial Years",
        fy_labels_sorted,
        default=[fy_labels_sorted[-1]],
    )

    if len(selected_fy_labels) > 3:
        st.warning("You can select a maximum of 3 financial years.")
        selected_fy_labels = selected_fy_labels[:3]

    selected_fy_years = sorted([label_to_year[lbl] for lbl in selected_fy_labels])

    if len(selected_fy_years) > 1:
        if selected_fy_years != list(
            range(
                selected_fy_years[0],
                selected_fy_years[0] + len(selected_fy_years),
            )
        ):
            st.error("Please select consecutive financial years only.")
            st.stop()

    base_df = df[
        (df["BranchName"] == selected_branch) & (df["Year"].isin(selected_fy_years))
    ]

    category_list = sorted(base_df["MKTType"].unique())
    selected_categories = st.multiselect(
        "Select Product Category (MKTType)",
        category_list,
        default=category_list,
    )

    month_list = sorted(base_df["Month"].unique())
    selected_months = st.multiselect(
        "Select Month(s)",
        month_list,
        default=month_list,
    )

    analysis_level = st.radio(
        "Choose Analysis Level",
        [
            "Month-wise Product Category Sales",
            "Yearly Product Category Sales",
        ],
        horizontal=True,
    )

    cumulative_view = st.checkbox("Show Cumulative Analysis")

    metric_type = st.radio(
        "Choose Sales Type",
        [
            "Actual Sales",
            "Credit Note Sales",
            "Total Sales",
        ],
        horizontal=True,
    )

    filtered_df = base_df[
        (base_df["MKTType"].isin(selected_categories))
        & (base_df["Month"].isin(selected_months))
    ]

    if filtered_df.empty:
        st.warning("No data available for selected filters.")
        st.stop()

    if metric_type == "Actual Sales":
        value_col = "ActAmt"
        title_prefix = "Actual Sales"
    elif metric_type == "Credit Note Sales":
        value_col = "CNAmt"
        title_prefix = "Credit Notes"
    else:
        filtered_df = filtered_df.copy()
        filtered_df["TotalAmt"] = filtered_df["ActAmt"] + filtered_df["CNAmt"]
        value_col = "TotalAmt"
        title_prefix = "Total Sales"

    if analysis_level == "Month-wise Product Category Sales":
        agg_df = (
            filtered_df.groupby(["Year", "Month", "MKTType"])[value_col]
            .sum()
            .reset_index()
        )
        agg_df["FinancialYear"] = agg_df["Year"].map(year_to_label)
        x_col = "Month"
        color_col = "MKTType"
    else:
        agg_df = (
            filtered_df.groupby(["Year", "MKTType"])[value_col].sum().reset_index()
        )
        agg_df["FinancialYear"] = agg_df["Year"].map(year_to_label)
        x_col = "MKTType"
        color_col = "FinancialYear"


        # ---------- PRODUCT INSIGHTS ----------
    top_product_row = agg_df.sort_values(value_col, ascending=False).iloc[0]

    st.subheader("📌 Product Performance Snapshot")

    c1, c2 = st.columns(2)

    with c1:
        st.markdown(
            f"""
            <div class="insight-card">
                <div class="insight-title">🏆 Top Product</div>
                <div class="insight-value">{top_product_row['MKTType']}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with c2:
        st.markdown(
            f"""
            <div class="insight-card">
                <div class="insight-title">💰 Highest Sales</div>
                <div class="insight-value">₹{top_product_row[value_col]:,.0f}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("---")


    if cumulative_view:
        cum_df = agg_df.groupby(x_col)[value_col].sum().reset_index()

        fig = px.bar(
            cum_df,
            x=x_col,
            y=value_col,
            title=f"Cumulative {analysis_level} — {title_prefix}",
            color=x_col,
        )
        display_grid_with_export(cum_df, "Cumulative Product Data", "product_cumulative")
    else:
        fig = px.bar(
            agg_df,
            x=x_col,
            y=value_col,
            color=color_col,
            barmode="group",
            title=f"{analysis_level} — {title_prefix}",
        )
        display_grid_with_export(agg_df, "Product Category Data", "product_category_data")

    fig.update_traces(text=None)
    st.plotly_chart(fig, use_container_width=True)

    top_row = agg_df.sort_values(value_col, ascending=False).iloc[0]
    st.markdown(
        f"""
        <hr>
        <p style="font-size:18px; font-weight:600;">
        Highest: <span style="color:#00ff88;">{top_row['MKTType']}</span>
        with <span style="color:#00c0ff;">₹{top_row[value_col]:,.0f}</span>
        </p>
        """,
        unsafe_allow_html=True,
    )
