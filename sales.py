import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px


# ---------- DATA LOAD ----------
df = pd.read_csv("C:\\CODE\\python projects\\sir\\Sales_Analysis_3\\csv\\Mfg_Sales.csv")


# ---------- BASIC DATE FIELDS ----------
df["MMYYYY"] = pd.to_datetime(df["MMYYYY"], format="%Y-%m")
df["Year"] = df["MMYYYY"].dt.year      # still available if you ever need it
df["Month"] = df["MMYYYY"].dt.strftime("%B")
df["Month_num"] = df["MMYYYY"].dt.month


# Quarter map
month_to_quarter = {
    1: "Q1", 2: "Q1", 3: "Q1",
    4: "Q2", 5: "Q2", 6: "Q2",
    7: "Q3", 8: "Q3", 9: "Q3",
    10: "Q4", 11: "Q4", 12: "Q4",
}
df["Quarter"] = df["Month_num"].map(month_to_quarter)

months = sorted(df["Month"].unique())
quarters = ["Q1", "Q2", "Q3", "Q4"]

# academic years from AcYr like 2020-2021
acyears = sorted(df["AcYr"].unique())


# helper: numeric index for AcYr so we can compute growth
# Example: 2019-2020 -> 2019, 2020-2021 -> 2020, etc.
def acyr_to_index(acyr: str) -> int:
    # safe parse: take first 4 chars as start year
    try:
        return int(str(acyr)[:4])
    except Exception:
        return 0


df["AcYrIndex"] = df["AcYr"].apply(acyr_to_index)


# ---------- SIMPLE FORECAST HELPERS (FINANCIAL YEAR–BASED) ----------

def forecast_total_by_acyr(act_df: pd.DataFrame, value_col: str = "ActAmt"):
    """
    Input: act_df with columns [AcYr, AcYrIndex, value_col]
    Returns: dataframe with columns [AcYr, AcYrIndex, value_col, Forecast]
    Forecast is based on average growth rate over available AcYr.
    """
    tmp = (
        act_df.groupby(["AcYr", "AcYrIndex"])[value_col]
        .sum()
        .reset_index()
        .sort_values("AcYrIndex")
    )

    if len(tmp) < 2:
        tmp["Forecast"] = np.nan
        return tmp

    # Compute year-on-year growth
    tmp["PrevValue"] = tmp[value_col].shift(1)
    tmp["Growth"] = (tmp[value_col] - tmp["PrevValue"]) / tmp["PrevValue"]
    avg_growth = tmp["Growth"].dropna().mean()

    # Use last known value + avg growth to project the next AcYr
    last_row = tmp.iloc[-1]
    next_acyr_index = last_row["AcYrIndex"] + 1
    # build label: e.g., "2020-2021" -> "2021-2022"
    next_acyr_label = f"{next_acyr_index}-{next_acyr_index+1}"
    next_value = last_row[value_col] * (1 + avg_growth if pd.notna(avg_growth) else 1)

    forecast_row = pd.DataFrame(
        {
            "AcYr": [next_acyr_label],
            "AcYrIndex": [next_acyr_index],
            value_col: [np.nan],
            "Forecast": [next_value],
        }
    )

    tmp["Forecast"] = np.nan
    tmp = pd.concat([tmp, forecast_row], ignore_index=True)
    return tmp


def forecast_month_share_for_next_acyr(df_full: pd.DataFrame, value_col: str = "ActAmt"):
    """
    Uses last completed AcYr to get month-wise share, and multiplies
    forecasted total of next AcYr.
    Returns df with [Month, ForecastValue, NextAcYr].
    """
    # total per AcYr
    base_df = df_full[["AcYr", "AcYrIndex", value_col]].copy()
    total_forecast = forecast_total_by_acyr(base_df, value_col=value_col)

    # if no forecast possible
    if total_forecast["Forecast"].isna().all():
        return pd.DataFrame(columns=["Month", "ForecastValue", "NextAcYr"])

    # next ac year info
    next_row = total_forecast[total_forecast["Forecast"].notna()].iloc[-1]
    next_acyr_label = next_row["AcYr"]
    total_next_value = next_row["Forecast"]

    # last completed acyr
    existing = total_forecast[total_forecast[value_col].notna()]
    if existing.empty:
        return pd.DataFrame(columns=["Month", "ForecastValue", "NextAcYr"])
    last_completed_acyr = existing.iloc[-1]["AcYr"]

    last_df = df_full[df_full["AcYr"] == last_completed_acyr]
    if last_df.empty:
        return pd.DataFrame(columns=["Month", "ForecastValue", "NextAcYr"])

    month_tot = (
        last_df.groupby("Month")[value_col]
        .sum()
        .reset_index()
    )
    if month_tot[value_col].sum() == 0:
        return pd.DataFrame(columns=["Month", "ForecastValue", "NextAcYr"])

    month_tot["Share"] = month_tot[value_col] / month_tot[value_col].sum()
    month_tot["ForecastValue"] = month_tot["Share"] * total_next_value
    month_tot["NextAcYr"] = next_acyr_label
    return month_tot[["Month", "ForecastValue", "NextAcYr"]]


def forecast_dimension_share_next_acyr(
    df_full: pd.DataFrame,
    dim_cols,
    value_col: str = "ActAmt",
):
    """
    General: uses last completed AcYr to get share by given dimension(s),
    and multiplies by forecasted total of next AcYr.
    Returns df with [*dim_cols, ForecastValue, NextAcYr].
    """
    base_df = df_full[["AcYr", "AcYrIndex", value_col]].copy()
    total_forecast = forecast_total_by_acyr(base_df, value_col=value_col)

    if total_forecast["Forecast"].isna().all():
        return pd.DataFrame(columns=list(dim_cols) + ["ForecastValue", "NextAcYr"])

    next_row = total_forecast[total_forecast["Forecast"].notna()].iloc[-1]
    next_acyr_label = next_row["AcYr"]
    total_next_value = next_row["Forecast"]

    existing = total_forecast[total_forecast[value_col].notna()]
    if existing.empty:
        return pd.DataFrame(columns=list(dim_cols) + ["ForecastValue", "NextAcYr"])
    last_completed_acyr = existing.iloc[-1]["AcYr"]

    last_df = df_full[df_full["AcYr"] == last_completed_acyr]
    if last_df.empty:
        return pd.DataFrame(columns=list(dim_cols) + ["ForecastValue", "NextAcYr"])

    dim_tot = (
        last_df.groupby(dim_cols)[value_col]
        .sum()
        .reset_index()
    )
    if dim_tot[value_col].sum() == 0:
        return pd.DataFrame(columns=list(dim_cols) + ["ForecastValue", "NextAcYr"])

    dim_tot["Share"] = dim_tot[value_col] / dim_tot[value_col].sum()
    dim_tot["ForecastValue"] = dim_tot["Share"] * total_next_value
    dim_tot["NextAcYr"] = next_acyr_label
    return dim_tot[list(dim_cols) + ["ForecastValue", "NextAcYr"]]


# ---------- TITLE ----------
st.markdown(
    "<h1 style='color:violet; font-weight:1000;'>Analytical Dashboard</h1>",
    unsafe_allow_html=True,
)


# ---------- SESSION ----------
if "page" not in st.session_state:
    st.session_state.page = "dashboard"
if "ac_year" not in st.session_state and len(acyears) > 0:
    st.session_state.ac_year = acyears[-1]  # default to latest FY


# ---------- CSS FOR COLORFUL CARDS ----------
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


# ---------- GLOBAL YEAR SELECTOR ----------
st.subheader("Select Financial / Academic Year")
current_ac_year = st.selectbox(
    "Financial Year (AcYr)",
    acyears,
    index=acyears.index(st.session_state.ac_year) if st.session_state.ac_year in acyears else 0,
    key="ac_year",
)


# ---------- SIDEBAR ----------
st.sidebar.markdown(
    "<h3 style='color:#ffd95a; margin-bottom:0.3rem;'>Way of Analysis</h3>",
    unsafe_allow_html=True,
)

menu = {
    "Quarter vs Year Comparison": "comparison",
    "Month-wise Sales": "monthwise",
    "Top Category / MKTType": "category",
    "Product–Month Analysis": "prodmonth",
    "Branch–Month Analysis": "branchmonth",
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


# helper: filter by current academic year
def filter_ac_year(frame: pd.DataFrame) -> pd.DataFrame:
    return frame[frame["AcYr"] == current_ac_year]


# =====================================================================
# PAGE 1: QUARTER COMPARISON (multi-year) using FINANCIAL YEAR + forecast
# =====================================================================
if st.session_state.page == "comparison":
    st.header("Sales Comparison on different Financial Years and Quarters")

    acyears_all = sorted(df["AcYr"].unique())
    selected_quarter = st.selectbox("Select Quarter for Comparison", quarters)
    selected_acyears = st.multiselect(
        "Select Financial Years (AcYr) for Comparison",
        acyears_all,
        default=acyears_all[:2]
    )
    if len(selected_acyears) > 6:
        st.warning("You can select up to 6 financial years only. Extra selections will be ignored.")
        selected_acyears = selected_acyears[:6]

    show_forecast = st.checkbox("Show forecast for next financial year (AcYr)", value=True)

    filtered_df = df[(df["Quarter"] == selected_quarter) & (df["AcYr"].isin(selected_acyears))]
    compare_chart = (
        filtered_df.groupby("AcYr")["ActAmt"]
        .sum()
        .reset_index()
        .rename(columns={"AcYr": "FinancialYear"})
    )

    if compare_chart.empty:
        st.warning("No data available for the selected filter.")
    else:
        fig_cmp = px.bar(
            compare_chart,
            x="FinancialYear",
            y="ActAmt",
            title=f"Sales Comparison for {selected_quarter} (Financial Years)",
        )
        fig_cmp.update_traces(text=None)

        # show forecast as text (over financial year aggregation)
        if show_forecast:
            acyr_tot = df.groupby(["AcYr", "AcYrIndex"])["ActAmt"].sum().reset_index()
            acyr_forecast = forecast_total_by_acyr(acyr_tot, value_col="ActAmt")
            f_rows = acyr_forecast[acyr_forecast["Forecast"].notna()]
            if not f_rows.empty:
                f_row = f_rows.iloc[-1]
                st.markdown(
                    f"""
                    <hr>
                    <p style="font-size:20px; font-weight:650;">
                    Predicted total sales in next financial year
                    <span style="color:#ffdd55;">{f_row['AcYr']}</span>:
                    <span style="color:#00c0ff;">₹{f_row['Forecast']:,.0f}</span>.
                    </p>
                    """,
                    unsafe_allow_html=True,
                )

        st.plotly_chart(fig_cmp, key="cmp_chart")

        best_row = compare_chart.loc[compare_chart["ActAmt"].idxmax()]
        best_fy = best_row["FinancialYear"]
        best_value = best_row["ActAmt"]

        st.markdown(
            f"""
            <hr>
            <p style="font-size:22px; font-weight:700;">
            Highest sales in <span style="color:#00ff88;">{selected_quarter}</span>
            were in financial year
            <span style="color:#ffdd55;">{best_fy}</span> with
            <span style="color:#00c0ff;">₹{best_value:,.0f}</span>.
            </p>
            """,
            unsafe_allow_html=True,
        )


# =====================================================================
# PAGE 2: MONTH-WISE SALES + forecast
# =====================================================================
elif st.session_state.page == "monthwise":
    st.header(f"Month-wise Sales Analysis ({current_ac_year})")

    year_df = filter_ac_year(df)
    month_chart = (
        year_df.groupby("Month")["ActAmt"]
        .sum()
        .reset_index()
        .sort_values("ActAmt", ascending=False)
    )

    plot_type = st.selectbox(
        "Choose chart type for Month Sales",
        ["Bar", "Line", "Pie", "Area", "Scatter"],
        key="month_chart_type",
    )

    show_forecast_month = st.checkbox("Show forecast for next financial year (month-wise)", value=True)

    if not month_chart.empty and month_chart["ActAmt"].sum() > 0:
        # build actual chart
        if plot_type == "Bar":
            fig_mon = px.bar(
                month_chart,
                x="Month",
                y="ActAmt",
                title=f"Month-wise Sales for {current_ac_year}",
            )
        elif plot_type == "Line":
            fig_mon = px.line(
                month_chart,
                x="Month",
                y="ActAmt",
                title=f"Month-wise Sales for {current_ac_year}",
                markers=True,
            )
        elif plot_type == "Pie":
            fig_mon = px.pie(
                month_chart,
                names="Month",
                values="ActAmt",
                title=f"Month-wise Sales for {current_ac_year}",
            )
            fig_mon.update_traces(textinfo="none")
        elif plot_type == "Area":
            fig_mon = px.area(
                month_chart,
                x="Month",
                y="ActAmt",
                title=f"Month-wise Sales for {current_ac_year}",
            )
        elif plot_type == "Scatter":
            fig_mon = px.scatter(
                month_chart,
                x="Month",
                y="ActAmt",
                title=f"Month-wise Sales for {current_ac_year}",
                size="ActAmt",
                color="Month",
            )

        if plot_type != "Pie":
            fig_mon.update_traces(text=None)

        # overlay forecast for next AcYr (month-wise)
        if show_forecast_month and plot_type != "Pie":
            month_fore = forecast_month_share_for_next_acyr(df, value_col="ActAmt")
            if not month_fore.empty:
                # align month category order
                month_order = month_chart["Month"].tolist()
                month_fore = month_fore.set_index("Month").reindex(month_order).reset_index()
                fig_mon.add_scatter(
                    x=month_fore["Month"],
                    y=month_fore["ForecastValue"],
                    mode="lines+markers",
                    name=f"Forecast {month_fore['NextAcYr'].iloc[0]}",
                    line=dict(color="red", dash="dash"),
                )

        st.plotly_chart(fig_mon, key=f"month_chart_{plot_type}")

        top_month = month_chart.iloc[0]["Month"]
        top_month_sales = month_chart.iloc[0]["ActAmt"]
        st.markdown(
            f"""
            <hr>
            <p style="font-size:20px; font-weight:650;">
             In <span style="color:#ffdd55;">{current_ac_year}</span>,
            the best month was
            <span style="color:#00ff88;">{top_month}</span> with
            <span style="color:#00c0ff;">₹{top_month_sales:,.0f}</span> sales.
            </p>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.warning("No data available for selected year/month.")


# =====================================================================
# PAGE 3: TOP CATEGORY / MKTType + forecast by Branch/MKTType
# =====================================================================
elif st.session_state.page == "category":
    year_df = filter_ac_year(df)

    st.header(f"Top category for medicine highest sales ({current_ac_year})")
    model_chart = (
        year_df.groupby(["AcYr", "BranchName", "MKTType", "BrandName", "Month"])["ActAmt"]
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

    show_forecast_prod = st.checkbox("Show forecast for next financial year (Branch + MKTType)", value=True)

    if not prod_line.empty and prod_line["ActAmt"].sum() > 0:
        if prod_chart == "Bar":
            fig_prod = px.bar(
                prod_line,
                x="BranchName",
                y="ActAmt",
                color="MKTType",
                title=f"Product Line Sales for {current_ac_year}",
            )
        elif prod_chart == "Line":
            fig_prod = px.line(
                prod_line,
                x="BranchName",
                y="ActAmt",
                color="MKTType",
                title=f"Product Line Sales for {current_ac_year}",
                markers=True,
            )
        elif prod_chart == "Pie":
            pie_data = prod_line.groupby("MKTType")["ActAmt"].sum().reset_index()
            fig_prod = px.pie(
                pie_data,
                names="MKTType",
                values="ActAmt",
                title=f"Product Line Sales for {current_ac_year}",
            )
            fig_prod.update_traces(textinfo="none")
        elif prod_chart == "Area":
            fig_prod = px.area(
                prod_line,
                x="BranchName",
                y="ActAmt",
                color="MKTType",
                title=f"Category-wise Sales for {current_ac_year}",
            )
        elif prod_chart == "Scatter":
            fig_prod = px.scatter(
                prod_line,
                x="MKTType",
                y="BranchName",
                size="ActAmt",
                color="MKTType",
                title=f"Product Line Sales for {current_ac_year}",
            )

        if prod_chart != "Pie":
            fig_prod.update_traces(text=None)

        # Forecast by BranchName + MKTType for next AcYr
        if show_forecast_prod and prod_chart in ["Bar", "Line", "Area", "Scatter"]:
            dim_fore = forecast_dimension_share_next_acyr(
                df,
                dim_cols=["BranchName", "MKTType"],
                value_col="ActAmt",
            )
            if not dim_fore.empty:
                # show total forecast of top combination as text
                top_f = dim_fore.sort_values("ForecastValue", ascending=False).iloc[0]
                st.markdown(
                    f"""
                    <p style="font-size:18px; font-weight:600;">
                    Predicted top (Branch, MKTType) in next financial year
                    <span style="color:#ffdd55;">{top_f['NextAcYr']}</span> is
                    <span style="color:#ffdd55;">{top_f['BranchName']}</span> –
                    <span style="color:#00ff88;">{top_f['MKTType']}</span> with
                    <span style="color:#00c0ff;">₹{top_f['ForecastValue']:,.0f}</span>.
                    </p>
                    """,
                    unsafe_allow_html=True,
                )

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
# PAGE 4: PRODUCT–MONTH (by MKTType) + forecast
# =====================================================================
elif st.session_state.page == "prodmonth":
    year_df = filter_ac_year(df)

    st.header(f"Product–Month Analysis ({current_ac_year})")
    model_chart = (
        year_df.groupby(["AcYr", "Month", "BrandName", "MKTType"])["ActAmt"]
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

    show_forecast_mkt = st.checkbox("Show forecast for next financial year (MKTType total)", value=True)

    if not code_line.empty and code_line["ActAmt"].sum() > 0:
        if code_chart == "Bar":
            fig_prod = px.bar(
                code_line,
                x="MKTType",
                y="ActAmt",
                title=f"Product Line Sales for {current_ac_year}",
            )
        elif code_chart == "Line":
            fig_prod = px.line(
                code_line,
                x="MKTType",
                y="ActAmt",
                title=f"Product Line Sales for {current_ac_year}",
                markers=True,
            )
        elif code_chart == "Pie":
            fig_prod = px.pie(
                code_line,
                names="MKTType",
                values="ActAmt",
                title=f"Product Line Sales for {current_ac_year}",
            )
            fig_prod.update_traces(textinfo="none")
        elif code_chart == "Area":
            fig_prod = px.area(
                code_line,
                x="MKTType",
                y="ActAmt",
                title=f"Product Line Sales for {current_ac_year}",
            )
        elif code_chart == "Scatter":
            fig_prod = px.scatter(
                code_line,
                x="MKTType",
                y="ActAmt",
                title=f"Product Line Sales for {current_ac_year}",
                size="ActAmt",
                color="MKTType",
            )

        if code_chart != "Pie":
            fig_prod.update_traces(text=None)

        # Forecast per MKTType for next AcYr
        if show_forecast_mkt and code_chart in ["Bar", "Line", "Area", "Scatter"]:
            dim_fore = forecast_dimension_share_next_acyr(
                df,
                dim_cols=["MKTType"],
                value_col="ActAmt",
            )
            if not dim_fore.empty:
                # show best MKTType forecast
                top_f = dim_fore.sort_values("ForecastValue", ascending=False).iloc[0]
                st.markdown(
                    f"""
                    <p style="font-size:18px; font-weight:600;">
                    Predicted top market type in next financial year
                    <span style="color:#ffdd55;">{top_f['NextAcYr']}</span> is
                    <span style="color:#00ff88;">{top_f['MKTType']}</span> with
                    <span style="color:#00c0ff;">₹{top_f['ForecastValue']:,.0f}</span>.
                    </p>
                    """,
                    unsafe_allow_html=True,
                )

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
# PAGE 5: BRANCH–MONTH + forecast per Branch
# =====================================================================
elif st.session_state.page == "branchmonth":
    year_df = filter_ac_year(df)

    st.header(f"Branch–Month Analysis ({current_ac_year})")
    branch_month_chart = (
        year_df.groupby(["AcYr", "Month", "BranchName"])["ActAmt"]
        .sum()
        .reset_index()
    )
    st.dataframe(branch_month_chart, use_container_width=True)

    branch_line = (
        year_df.groupby(["BranchName"])["ActAmt"]
        .sum()
        .reset_index()
        .sort_values("ActAmt", ascending=False)
    )

    branch_chart_2 = st.selectbox(
        "Choose chart type for Branch Sales",
        ["Bar", "Line", "Pie", "Area", "Scatter"],
        key="branchline_chart_type",
    )

    show_forecast_branch = st.checkbox("Show forecast for next financial year (Branch total)", value=True)

    if not branch_line.empty and branch_line["ActAmt"].sum() > 0:
        if branch_chart_2 == "Bar":
            fig_country = px.bar(
                branch_line,
                x="BranchName",
                y="ActAmt",
                title=f"Branch Sales for {current_ac_year}",
            )
        elif branch_chart_2 == "Line":
            fig_country = px.line(
                branch_line,
                x="BranchName",
                y="ActAmt",
                title=f"Branch Sales for {current_ac_year}",
                markers=True,
            )
        elif branch_chart_2 == "Pie":
            fig_country = px.pie(
                branch_line,
                names="BranchName",
                values="ActAmt",
                title=f"Branch Sales for {current_ac_year}",
            )
            fig_country.update_traces(textinfo="none")
        elif branch_chart_2 == "Area":
            fig_country = px.area(
                branch_line,
                x="BranchName",
                y="ActAmt",
                title=f"Branch Sales for {current_ac_year}",
            )
        elif branch_chart_2 == "Scatter":
            fig_country = px.scatter(
                branch_line,
                x="BranchName",
                y="ActAmt",
                title=f"Branch Sales for {current_ac_year}",
                size="ActAmt",
                color="BranchName",
            )

        if branch_chart_2 != "Pie":
            fig_country.update_traces(text=None)

        # Forecast per BranchName
        if show_forecast_branch and branch_chart_2 in ["Bar", "Line", "Area", "Scatter"]:
            dim_fore = forecast_dimension_share_next_acyr(
                df,
                dim_cols=["BranchName"],
                value_col="ActAmt",
            )
            if not dim_fore.empty:
                top_f = dim_fore.sort_values("ForecastValue", ascending=False).iloc[0]
                st.markdown(
                    f"""
                    <p style="font-size:18px; font-weight:600;">
                    Predicted top branch in next financial year
                    <span style="color:#ffdd55;">{top_f['NextAcYr']}</span> is
                    <span style="color:#ffdd55;">{top_f['BranchName']}</span> with
                    <span style="color:#00c0ff;">₹{top_f['ForecastValue']:,.0f}</span>.
                    </p>
                    """,
                    unsafe_allow_html=True,
                )

        st.plotly_chart(fig_country, key=f"branchline_chart_{branch_chart_2}")

        top_row = branch_line.iloc[0]
        st.markdown(
            f"""
            <hr>
            <p style="font-size:20px; font-weight:650;">
             Branch <span style="color:#ffdd55;">{top_row['BranchName']}</span>
            recorded the highest sales of
            <span style="color:#00c0ff;">₹{top_row['ActAmt']:,.0f}</span>.
            </p>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.warning("No data available for branch sales.")


# =====================================================================
# PAGE 6: CREDIT NOTE + forecast
# =====================================================================
elif st.session_state.page == "credit":
    st.header(f"Credit Note Analysis ({current_ac_year})")

    col_f1, col_f2 = st.columns(2)
    with col_f1:
        st.markdown(
            f"**Month-wise Credit Notes in {current_ac_year}**"
        )
    with col_f2:
        selected_month_cn = st.selectbox(
            "Select Month (Year-wise view)", months, key="credit_month"
        )

    show_forecast_cn = st.checkbox("Show forecast for next financial year (Credit notes)", value=True)

    # 1) Month-wise credit notes within selected academic year
    df_year_cn = filter_ac_year(df)
    chart_month_in_year = (
        df_year_cn.groupby("Month")["CNAmt"]
        .sum()
        .reset_index()
        .sort_values("CNAmt", ascending=False)
    )

    if chart_month_in_year.empty:
        st.warning("No credit-note data for the selected academic year.")
    else:
        fig_cn_month = px.bar(
            chart_month_in_year,
            x="Month",
            y="CNAmt",
            title=f"Month-wise Credit Note Analysis ({current_ac_year})",
        )
        fig_cn_month.update_traces(text=None)

        # overlay forecast for next AcYr (monthwise CNAmt)
        if show_forecast_cn:
            cn_fore = forecast_month_share_for_next_acyr(df, value_col="CNAmt")
            if not cn_fore.empty:
                month_order = chart_month_in_year["Month"].tolist()
                cn_fore = cn_fore.set_index("Month").reindex(month_order).reset_index()
                fig_cn_month.add_scatter(
                    x=cn_fore["Month"],
                    y=cn_fore["ForecastValue"],
                    mode="lines+markers",
                    name=f"CN Forecast {cn_fore['NextAcYr'].iloc[0]}",
                    line=dict(color="red", dash="dash"),
                )

        st.plotly_chart(fig_cn_month, key="cn_chart_month")

        top_row_m = chart_month_in_year.iloc[0]
        st.markdown(
            f"""
            <p style="font-size:18px; font-weight:600;">
             In <span style="color:#ffdd55;">{current_ac_year}</span>,
            highest credit notes were in
            <span style="color:#00ff88;">{top_row_m['Month']}</span> with
            <span style="color:#ff6b6b;">₹{top_row_m['CNAmt']:,.0f}</span>.
            </p>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<hr>", unsafe_allow_html=True)

    # 2) Year-wise credit notes for selected month across AcYr
    month_df_cn = df[df["Month"] == selected_month_cn]
    chart_year_for_month = (
        month_df_cn.groupby("AcYr")["CNAmt"]
        .sum()
        .reset_index()
        .sort_values("CNAmt", ascending=False)
    )

    if chart_year_for_month.empty:
        st.warning("No credit-note data for the selected month across years.")
    else:
        fig_cn_year = px.bar(
            chart_year_for_month,
            x="AcYr",
            y="CNAmt",
            title=f"Academic Year-wise Credit Note Analysis for {selected_month_cn}",
        )
        fig_cn_year.update_traces(text=None)
        st.plotly_chart(fig_cn_year, key="cn_chart_year")

        top_row_y = chart_year_for_month.iloc[0]
        st.markdown(
            f"""
            <hr>
            <p style="font-size:18px; font-weight:600;">
             For <span style="color:#00ff88;">{selected_month_cn}</span>,
            maximum credit notes were in
            <span style="color:#ffdd55;">{top_row_y['AcYr']}</span> with
            <span style="color:#ff6b6b;">₹{top_row_y['CNAmt']:,.0f}</span>.
            </p>
            """,
            unsafe_allow_html=True,
        )
