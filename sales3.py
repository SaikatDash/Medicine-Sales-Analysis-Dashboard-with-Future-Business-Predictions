import streamlit as st
import pandas as pd
import plotly.express as px


# ---------- DATA LOAD ----------
df = pd.read_csv(r"C:\CODE\python projects\sir\Sales_Analysis_3\csv\Mfg_Sales.csv")


df["MMYYYY"] = pd.to_datetime(df["MMYYYY"], format="%Y-%m")
df["Year"] = df["MMYYYY"].dt.year
df["Month"] = df["MMYYYY"].dt.strftime("%B")

df["Month_num"] = df["MMYYYY"].dt.month
month_to_quarter = {
    1: "Q1", 2: "Q1", 3: "Q1",
    4: "Q2", 5: "Q2", 6: "Q2",
    7: "Q3", 8: "Q3", 9: "Q3",
    10: "Q4", 11: "Q4", 12: "Q4",
}
df["Quarter"] = df["Month_num"].map(month_to_quarter)

years = sorted(df["Year"].unique())
months = list(df["Month"].unique())
quarters = ["Q1", "Q2", "Q3", "Q4"]

# ---- Financial year labels (YYYY-YY) ----
base_years = years
fy_labels = [f"{y}-{str(y+1)[-2:]}" for y in base_years]
label_to_year = dict(zip(fy_labels, base_years))
year_to_label = {v: k for k, v in label_to_year.items()}

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

# ---------- SIDEBAR ----------
st.sidebar.markdown(
    "<h3 style='color:#ffd95a; margin-bottom:0.3rem;'>Way of Analysis</h3>",
    unsafe_allow_html=True,
)

menu = {
    "Quarter vs Year Comparison": "comparison",
    "Business Analysis": "business",
    "Branch–Business Analysis": "branchbusiness",
    "Top Category / MKTType": "category",
    "Product–Month Analysis": "prodmonth",
    "Credit Note Analysis": "credit",
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

    # map default 2 earliest years to labels
    default_years = years[:2]
    default_labels = [year_to_label[y] for y in default_years]

    selected_fy_labels_for_cmp = st.multiselect(
        "Select Financial Years for Comparison",
        fy_labels,
        default=default_labels,
    )

    if len(selected_fy_labels_for_cmp) > 6:
        st.warning("You can select up to 6 financial years only. Extra selections will be ignored.")
        selected_fy_labels_for_cmp = selected_fy_labels_for_cmp[:6]

    selected_years_for_cmp = [label_to_year[lbl] for lbl in selected_fy_labels_for_cmp]

    filtered_df = df[(df["Quarter"] == selected_quarter) & (df["Year"].isin(selected_years_for_cmp))]
    compare_chart = (
        filtered_df.groupby("Year")["ActAmt"]
        .sum()
        .reset_index()
    )

    # Add FY label for nicer x-axis
    if not compare_chart.empty:
        compare_chart["FinancialYear"] = compare_chart["Year"].map(year_to_label)

    if compare_chart.empty:
        st.warning("No data available for the selected filter.")
    else:
        fig_cmp = px.bar(
            compare_chart,
            x="FinancialYear",
            y="ActAmt",
            title=f"Sales Comparison for {selected_quarter} (by Financial Year)",
        )
        fig_cmp.update_traces(text=None)
        st.plotly_chart(fig_cmp, key="cmp_chart")

        best_row = compare_chart.loc[compare_chart["ActAmt"].idxmax()]
        best_fy_label = best_row["FinancialYear"]
        best_value = best_row["ActAmt"]

        st.markdown(
            f"""
            <hr>
            <p style="font-size:22px; font-weight:700;">
             Highest sales in <span style="color:#00ff88;">{selected_quarter}</span>
            were in financial year
            <span style="color:#ffdd55;">{best_fy_label}</span> with
            <span style="color:#00c0ff;">₹{best_value:,.0f}</span>.
            </p>
            """,
            unsafe_allow_html=True,
        )

# =====================================================================
# PAGE 2: BUSINESS Analysis
# =====================================================================
elif st.session_state.page == "business":
    st.header(f"Business Analysis on FY {financial_year}")

    year_df = df[df["Year"] == fy_year]

    # --- Month-wise aggregations ---
    month_act = (
        year_df.groupby("Month")["ActAmt"]
        .sum()
        .reset_index()
    )
    month_cn = (
        year_df.groupby("Month")["CNAmt"]
        .sum()
        .reset_index()
    )

    month_total = (
        year_df.groupby("Month")[["ActAmt", "CNAmt"]]
        .sum()
        .reset_index()
    )
    month_total["TotalAmt"] = month_total["ActAmt"] + month_total["CNAmt"]

    # --- UI Buttons ---
    st.subheader("Choose Analysis Type")

    analysis_type = st.radio(
        "Select View",
        [
            "Total Month-wise Analysis",
            "Month-wise Actual Sales",
            "Month-wise Credit Note Analysis",
        ],
        index=0,
        horizontal=True
    )

    # --- Display graphs ---
    if analysis_type == "Total Month-wise Analysis":
        fig = px.bar(
            month_total,
            x="Month",
            y="TotalAmt",
            title=f"Total Month-wise Amount (FY {current_fy_label})",
        )
        st.plotly_chart(fig, key="total_chart")

        if not month_total.empty:
            top_row = month_total.sort_values("TotalAmt", ascending=False).iloc[0]
            st.markdown(
                f"""
                <hr>
                <p style="font-size:20px; font-weight:650;">
                Highest total value was in
                <span style="color:#00ff88;">{top_row['Month']}</span>
                with <span style="color:#00c0ff;">₹{top_row['TotalAmt']:,.0f}</span>.
                </p>
                """,
                unsafe_allow_html=True,
            )

    elif analysis_type == "Month-wise Actual Sales":
        fig = px.bar(
            month_act,
            x="Month",
            y="ActAmt",
            title=f"Month-wise Actual Sales (FY {current_fy_label})",
        )
        st.plotly_chart(fig, key="act_chart")

        if not month_act.empty:
            top_row = month_act.sort_values("ActAmt", ascending=False).iloc[0]
            st.markdown(
                f"""
                <hr>
                <p style="font-size:20px; font-weight:650;">
                Best Sales Month:
                <span style="color:#00ff88;">{top_row['Month']}</span>
                with <span style="color:#00c0ff;">₹{top_row['ActAmt']:,.0f}</span>.
                </p>
                """,
                unsafe_allow_html=True,
            )

    elif analysis_type == "Month-wise Credit Note Analysis":
        fig = px.bar(
            month_cn,
            x="Month",
            y="CNAmt",
            title=f"Month-wise Credit Notes (FY {current_fy_label})",
        )
        st.plotly_chart(fig, key="cn_chart")

        if not month_cn.empty:
            top_row = month_cn.sort_values("CNAmt", ascending=False).iloc[0]
            st.markdown(
                f"""
                <hr>
                <p style="font-size:20px; font-weight:650;">
                Highest credit note value was in
                <span style="color:#00ff88;">{top_row['Month']}</span>
                with <span style="color:#ff6b6b;">₹{top_row['CNAmt']:,.0f}</span>.
                </p>
                """,
                unsafe_allow_html=True,
            )

# =====================================================================
# PAGE 3: TOP CATEGORY / MKTType (use FY in titles)
# =====================================================================
elif st.session_state.page == "category":
    year_df = df[df["Year"] == fy_year]

    st.header(f"Top category for medicine highest sales (FY {current_fy_label})")
    model_chart = (
        year_df.groupby(["Year", "BranchName", "MKTType", "BrandName", "Month"])["ActAmt"]
        .sum()
        .reset_index()
    )
    st.dataframe(model_chart, use_container_width=True)

    prod_line = (
        year_df.groupby(["BranchName", "MKTType"])["ActAmt"]
        .sum()
        .reset_index()
        .sort_values("ActAmt", ascending=False)
    )

    prod_chart = st.selectbox(
        "Choose chart type for Product Line Sales",
        ["Bar", "Line", "Pie", "Area", "Scatter"],
        key="prodline_chart_type",
    )

    if not prod_line.empty and prod_line["ActAmt"].sum() > 0:
        if prod_chart == "Bar":
            fig_prod = px.bar(
                prod_line,
                x="BranchName",
                y="ActAmt",
                color="MKTType",
                title=f"Product Line Sales for FY {current_fy_label}",
            )
        elif prod_chart == "Line":
            fig_prod = px.line(
                prod_line,
                x="BranchName",
                y="ActAmt",
                color="MKTType",
                title=f"Product Line Sales for FY {current_fy_label}",
                markers=True,
            )
        elif prod_chart == "Pie":
            pie_data = prod_line.groupby("MKTType")["ActAmt"].sum().reset_index()
            fig_prod = px.pie(
                pie_data,
                names="MKTType",
                values="ActAmt",
                title=f"Product Line Sales for FY {current_fy_label}",
            )
            fig_prod.update_traces(textinfo="none")
        elif prod_chart == "Area":
            fig_prod = px.area(
                prod_line,
                x="BranchName",
                y="ActAmt",
                color="MKTType",
                title=f"Category-wise Sales for FY {current_fy_label}",
            )
        elif prod_chart == "Scatter":
            fig_prod = px.scatter(
                prod_line,
                x="MKTType",
                y="BranchName",
                size="ActAmt",
                color="MKTType",
                title=f"Product Line Sales for FY {current_fy_label}",
            )

        if prod_chart != "Pie":
            fig_prod.update_traces(text=None)
        st.plotly_chart(fig_prod, key=f"prodline_chart_{prod_chart}")

        top_row = prod_line.iloc[0]
        st.markdown(
            f"""
            <hr>
            <p style="font-size:20px; font-weight:650;">
             Top combination is branch
            <span style="color:#ffdd55;">{top_row['BranchName']}</span>
            with market type
            <span style="color:#00ff88;">{top_row['MKTType']}</span>
            giving <span style="color:#00c0ff;">₹{top_row['ActAmt']:,.0f}</span>.
            </p>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.warning("No data available for product line.")

# =====================================================================
# PAGE 4: PRODUCT–MONTH (use FY in titles)
# =====================================================================
elif st.session_state.page == "prodmonth":
    year_df = df[df["Year"] == fy_year]

    st.header(f"Product–Month Analysis (FY {current_fy_label})")
    model_chart = (
        year_df.groupby(["Year", "Month", "BrandName", "MKTType"])["ActAmt"]
        .sum()
        .reset_index()
    )
    st.dataframe(model_chart, use_container_width=True)

    code_line = (
        year_df.groupby(["MKTType"])["ActAmt"]
        .sum()
        .reset_index()
        .sort_values("ActAmt", ascending=False)
    )

    code_chart = st.selectbox(
        "Choose chart type for Product Line Sales",
        ["Bar", "Line", "Pie", "Area", "Scatter"],
        key="code_chart_type",
    )

    if not code_line.empty and code_line["ActAmt"].sum() > 0:
        if code_chart == "Bar":
            fig_prod = px.bar(
                code_line,
                x="MKTType",
                y="ActAmt",
                title=f"Product Line Sales for FY {current_fy_label}",
            )
        elif code_chart == "Line":
            fig_prod = px.line(
                code_line,
                x="MKTType",
                y="ActAmt",
                title=f"Product Line Sales for FY {current_fy_label}",
                markers=True,
            )
        elif code_chart == "Pie":
            fig_prod = px.pie(
                code_line,
                names="MKTType",
                values="ActAmt",
                title=f"Product Line Sales for FY {current_fy_label}",
            )
            fig_prod.update_traces(textinfo="none")
        elif code_chart == "Area":
            fig_prod = px.area(
                code_line,
                x="MKTType",
                y="ActAmt",
                title=f"Product Line Sales for FY {current_fy_label}",
            )
        elif code_chart == "Scatter":
            fig_prod = px.scatter(
                code_line,
                x="MKTType",
                y="ActAmt",
                title=f"Product Line Sales for FY {current_fy_label}",
                size="ActAmt",
                color="MKTType",
            )

        if code_chart != "Pie":
            fig_prod.update_traces(text=None)
        st.plotly_chart(fig_prod, key=f"code_chart_{code_chart}")

        top_row = code_line.iloc[0]
        st.markdown(
            f"""
            <hr>
            <p style="font-size:20px; font-weight:650;">
             Market type <span style="color:#00ff88;">{top_row['MKTType']}</span>
            leads with <span style="color:#00c0ff;">₹{top_row['ActAmt']:,.0f}</span> sales.
            </p>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.warning("No data available for product line.")

# =====================================================================
# PAGE 5: BRANCH–BUSINESS (MONTH) using FY
# =====================================================================
elif st.session_state.page == "branchbusiness":
    year_df = df[df["Year"] == fy_year]

    st.header(f"Branch–Month Analysis (FY {current_fy_label})")

    # ---------- FILTERS ----------
    branch_list = sorted(year_df["BranchName"].unique())
    month_list = list(df["Month"].unique())

    colA, colB = st.columns(2)
    with colA:
        selected_branch = st.selectbox("Select Branch", branch_list)

    with colB:
        selected_months = st.multiselect(
            "Select Month(s)",
            month_list,
            default=month_list  # show all by default
        )

    # ---------- METRIC TYPE SELECTOR ----------
    metric_type = st.radio(
        "Choose Analysis Type",
        [
            "Total Branch Month-wise Sales",
            "Actual Branch Month-wise Sales",
            "Credit Note Branch Month-wise Sales",
        ],
        index=0,
        horizontal=True
    )

    # ---------- CHART TYPE ----------
    chart_type = st.selectbox(
        "Choose Chart Type",
        ["Bar", "Line", "Pie", "Area", "Scatter"],
        key="branch_chart_type",
    )

    # ---------- AGGREGATE ----------
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

    # Select column based on metric choice
    if metric_type == "Total Branch Month-wise Sales":
        value_col = "TotalAmt"
        title = f"Total Sales — {selected_branch} (FY {current_fy_label})"
    elif metric_type == "Actual Branch Month-wise Sales":
        value_col = "ActAmt"
        title = f"Actual Sales — {selected_branch} (FY {current_fy_label})"
    else:
        value_col = "CNAmt"
        title = f"Credit Notes — {selected_branch} (FY {current_fy_label})"

    # ---------- PLOT ----------
    if not branch_month.empty and branch_month[value_col].sum() > 0:

        if chart_type == "Bar":
            fig = px.bar(branch_month, x="Month", y=value_col, title=title)

        elif chart_type == "Line":
            fig = px.line(branch_month, x="Month", y=value_col, title=title, markers=True)

        elif chart_type == "Pie":
            fig = px.pie(branch_month, names="Month", values=value_col, title=title)
            fig.update_traces(textinfo="none")

        elif chart_type == "Area":
            fig = px.area(branch_month, x="Month", y=value_col, title=title)

        elif chart_type == "Scatter":
            fig = px.scatter(
                branch_month,
                x="Month",
                y=value_col,
                size=value_col,
                color="Month",
                title=title,
            )

        if chart_type != "Pie":
            fig.update_traces(text=None)

        st.plotly_chart(fig, key="branch_month_chart")

        # ---------- INSIGHT ----------
        top_row = branch_month.sort_values(value_col, ascending=False).iloc[0]

        st.markdown(
            f"""
            <hr>
            <p style="font-size:20px; font-weight:650;">
            Highest value month for <b>{selected_branch}</b> in FY {current_fy_label} is
            <span style="color:#00ff88;">{top_row['Month']}</span>
            with <span style="color:#00c0ff;">₹{top_row[value_col]:,.0f}</span>.
            </p>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.warning("No data available for the selected filters.")

# ==============================================================================
# PAGE 6: CREDIT NOTE (using FY label + FY vs FY)
# ==============================================================================
elif st.session_state.page == "credit":
    st.header("Credit Note Analysis")

    col_f1, col_f2 = st.columns(2)
    with col_f1:
        st.markdown(
            f"**Month-wise Credit Notes in FY {current_fy_label}**"
        )
    with col_f2:
        selected_month_cn = st.selectbox(
            "Select Month (Year-wise view)", months, key="credit_month"
        )

    # 1) Month-wise credit notes within selected financial year
    year_df_cn = df[df["Year"] == fy_year]
    chart_month_in_year = (
        year_df_cn.groupby("Month")["CNAmt"]
        .sum()
        .reset_index()
        .sort_values("CNAmt", ascending=False)
    )

    if chart_month_in_year.empty:
        st.warning("No credit-note data for the selected financial year.")
    else:
        fig_cn_month = px.bar(
            chart_month_in_year,
            x="Month",
            y="CNAmt",
            title=f"Month-wise Credit Note Analysis (FY {current_fy_label})",
        )
        fig_cn_month.update_traces(text=None)
        st.plotly_chart(fig_cn_month, key="cn_chart_month")

        top_row_m = chart_month_in_year.iloc[0]
        st.markdown(
            f"""
            <p style="font-size:18px; font-weight:600;">
             In financial year <span style="color:#ffdd55;">{current_fy_label}</span>,
            highest credit notes were in
            <span style="color:#00ff88;">{top_row_m['Month']}</span> with
            <span style="color:#ff6b6b;">₹{top_row_m['CNAmt']:,.0f}</span>.
            </p>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<hr>", unsafe_allow_html=True)

    # 2) Year-wise credit notes for selected month (as FY comparison)
    month_df_cn = df[df["Month"] == selected_month_cn]
    chart_year_for_month = (
        month_df_cn.groupby("Year")["CNAmt"]
        .sum()
        .reset_index()
        .sort_values("CNAmt", ascending=False)
    )
    if not chart_year_for_month.empty:
        chart_year_for_month["FinancialYear"] = chart_year_for_month["Year"].map(year_to_label)

    if chart_year_for_month.empty:
        st.warning("No credit-note data for the selected month across years.")
    else:
        fig_cn_year = px.bar(
            chart_year_for_month,
            x="FinancialYear",
            y="CNAmt",
            title=f"Financial Year-wise Credit Note Analysis for {selected_month_cn}",
        )
        fig_cn_year.update_traces(text=None)
        st.plotly_chart(fig_cn_year, key="cn_chart_year")

        top_row_y = chart_year_for_month.iloc[0]
        st.markdown(
            f"""
            <hr>
            <p style="font-size:18px; font-weight:600;">
             For <span style="color:#00ff88;">{selected_month_cn}</span>,
            maximum credit notes were in financial year
            <span style="color:#ffdd55;">{top_row_y['FinancialYear']}</span> with
            <span style="color:#ff6b6b;">₹{top_row_y['CNAmt']:,.0f}</span>.
            </p>
            """,
            unsafe_allow_html=True,
        )
