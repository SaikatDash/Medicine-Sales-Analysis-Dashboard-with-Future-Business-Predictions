import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO
import time
import numpy as np
import warnings
import math
import matplotlib.pyplot as plt
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.stattools import adfuller
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
import statsmodels.api as sm
import statsmodels.tsa.api as smt
from sklearn.metrics import mean_squared_error, mean_absolute_error
import plotly.graph_objects as go
from pandas.tseries.offsets import DateOffset

warnings.filterwarnings('ignore')

# Disable st_aggrid - use regular dataframe instead
AGGRID_AVAILABLE = False

# ---------- GLOBAL PLOT SETTINGS ----------
COLOR_SEQ = px.colors.qualitative.Bold  # colorful discrete palette [web:16][web:17]
TEMPLATE = "plotly_dark"               # dark stylish template [web:25]

# ---------- DATA LOAD ----------

df = pd.read_csv("csv/Mfg_Sales.csv")

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

# ---------- HELPERS ----------

def test_stationarity(timeseries):
    """Test stationarity using Augmented Dickey-Fuller test."""
    dftest = adfuller(timeseries, autolag='AIC')
    return {
        'Test Statistic': dftest[0],
        'p-value': dftest[1],
        '#Lags Used': dftest[2],
        'Observations': dftest[3],
        'Critical Values': dftest[4]
    }

def run_arima_forecast(data: pd.DataFrame, arima_order=(2, 1, 2), test_size=30, forecast_periods=48):
    """
    Run comprehensive ARIMA forecasting from notebook.
    
    Parameters:
    - data: DataFrame with MMYYYY and ActAmt columns
    - arima_order: ARIMA order tuple (p, d, q) - default (2,1,2) from notebook
    - test_size: number of observations for backtesting 
    - forecast_periods: number of future periods to forecast
    """
    try:
        # Prepare time series data
        ts_data = data.groupby('MMYYYY')['ActAmt'].sum().reset_index()
        ts_data = ts_data.sort_values('MMYYYY').set_index('MMYYYY')
        
        # ===== STATIONARITY TEST =====
        stationarity_results = test_stationarity(ts_data['ActAmt'])
        is_stationary = stationarity_results['p-value'] < 0.05
        
        # ===== IN-SAMPLE FORECASTING (Backtesting) =====
        train_size = len(ts_data) - test_size
        train, test = ts_data['ActAmt'][0:train_size], ts_data['ActAmt'][train_size:len(ts_data)]
        
        history = [x for x in train]
        in_sample_predictions = []
        
        for t in range(len(test)):
            model = ARIMA(history, order=arima_order)
            model_fit = model.fit()
            output = model_fit.forecast(steps=1)
            yhat = float(output[0])
            in_sample_predictions.append(yhat)
            history.append(test.iloc[t])
        
        # Calculate error metrics
        mse = mean_squared_error(test[:len(in_sample_predictions)], in_sample_predictions)
        rmse = math.sqrt(mse)
        mae = mean_absolute_error(test[:len(in_sample_predictions)], in_sample_predictions)
        
        # ===== OUT-OF-SAMPLE FORECASTING (Future Prediction) =====
        # Train final model on all historical data
        model = ARIMA(ts_data['ActAmt'], order=arima_order)
        model_fit = model.fit()
        
        # Generate future dates (using weeks like in notebook)
        future_dates = [ts_data.index[-1] + DateOffset(weeks=x) for x in range(1, forecast_periods+1)]
        out_sample_predictions = []
        
        history_forecast = [x for x in ts_data['ActAmt']]
        for t in range(forecast_periods):
            model_temp = ARIMA(history_forecast, order=arima_order)
            model_fit_temp = model_temp.fit()
            output = model_fit_temp.forecast(steps=1)
            forecast_value = float(output[0])
            out_sample_predictions.append(forecast_value)
            history_forecast.append(forecast_value)
        
        # Create output dataframes
        historical_df = ts_data.reset_index()
        historical_df.columns = ['Date', 'Actual_Sales']
        
        backtest_df = pd.DataFrame({
            'Date': test.index,
            'Actual_Sales': test.values,
            'Predicted_Sales': in_sample_predictions
        })
        
        forecast_df = pd.DataFrame({
            'Date': future_dates,
            'Forecasted_Sales': out_sample_predictions
        })
        
        return {
            'historical': historical_df,
            'backtest': backtest_df,
            'forecast': forecast_df,
            'model': model_fit,
            'metrics': {
                'rmse': rmse,
                'mae': mae
            },
            'stationarity': stationarity_results,
            'is_stationary': is_stationary
        }
    except Exception as e:
        st.error(f"Error in ARIMA forecasting: {str(e)}")
        return None

def plot_arima_diagnostics(ts_data):
    """Plot ACF and PACF for time series data (from notebook)."""
    fig, axes = plt.subplots(2, 1, figsize=(12, 6))
    
    # ACF plot
    plot_acf(ts_data, lags=20, ax=axes[0])
    axes[0].set_title('Autocorrelation Function (ACF)')
    
    # PACF plot
    plot_pacf(ts_data, lags=20, ax=axes[1])
    axes[1].set_title('Partial Autocorrelation Function (PACF)')
    
    plt.tight_layout()
    return fig

def plot_seasonal_decomposition(ts_data):
    """Plot seasonal decomposition (from notebook)."""
    decomposition = sm.tsa.seasonal_decompose(ts_data, period=12, model='additive')
    fig = decomposition.plot()
    fig.set_size_inches(12, 8)
    return fig

def plot_forecast_comparison(historical_df, backtest_df, forecast_df):
    """Plot historical, backtest, and forecast data together."""
    fig = go.Figure()
    
    # Historical data
    fig.add_trace(go.Scatter(
        x=historical_df['Date'],
        y=historical_df['Actual_Sales'],
        mode='lines',
        name='Historical Sales',
        line=dict(color='blue', width=2)
    ))
    
    # Backtest predictions
    fig.add_trace(go.Scatter(
        x=backtest_df['Date'],
        y=backtest_df['Predicted_Sales'],
        mode='lines+markers',
        name='Backtest Predictions',
        line=dict(color='orange', width=2, dash='dash')
    ))
    
    # Future forecast
    fig.add_trace(go.Scatter(
        x=forecast_df['Date'],
        y=forecast_df['Forecasted_Sales'],
        mode='lines+markers',
        name='Future Forecast',
        line=dict(color='green', width=2, dash='dot')
    ))
    
    fig.update_layout(
        title='ARIMA Forecast: Historical, Backtest & Future',
        xaxis_title='Date',
        yaxis_title='Sales Amount',
        hovermode='x unified',
        template=TEMPLATE,
        height=500
    )
    return fig

def calculate_profit_loss_analysis(forecast_df, historical_df, profit_margin_pct=20, cost_per_unit=None):
    """
    Calculate profit/loss projections based on sales forecasts.
    
    Parameters:
    - forecast_df: DataFrame with forecasted sales
    - historical_df: DataFrame with historical sales for baseline comparison
    - profit_margin_pct: Expected profit margin percentage (default 20%)
    - cost_per_unit: Optional cost per unit for detailed analysis
    
    Returns:
    - Dictionary with profit/loss metrics and analysis
    """
    # Get historical baseline
    historical_avg = historical_df['Actual_Sales'].mean()
    historical_total = historical_df['Actual_Sales'].sum()
    
    # Get forecast metrics
    forecast_total = forecast_df['Forecasted_Sales'].sum()
    forecast_avg = forecast_df['Forecasted_Sales'].mean()
    
    # Calculate growth rate
    growth_rate = ((forecast_avg - historical_avg) / historical_avg * 100) if historical_avg > 0 else 0
    
    # Calculate projected profit (assuming margin)
    projected_profit = forecast_total * (profit_margin_pct / 100)
    
    # Compare to historical period
    historical_profit = historical_total * (profit_margin_pct / 100)
    profit_change = projected_profit - historical_profit
    
    return {
        'historical_avg': historical_avg,
        'historical_total': historical_total,
        'forecast_avg': forecast_avg,
        'forecast_total': forecast_total,
        'growth_rate': growth_rate,
        'projected_profit': projected_profit,
        'historical_profit': historical_profit,
        'profit_change': profit_change,
        'profit_margin_pct': profit_margin_pct,
        'health_status': 'Good' if growth_rate > 0 else 'Warning' if growth_rate > -10 else 'Critical'
    }

def plot_profit_loss_chart(forecast_df, historical_df, profit_margin_pct=20):
    """Create visualization comparing historical vs forecasted profitability."""
    # Aggregate by month for better visualization
    forecast_monthly = forecast_df.copy()
    forecast_monthly['Profit'] = forecast_monthly['Forecasted_Sales'] * (profit_margin_pct / 100)
    
    historical_monthly = historical_df.copy()
    historical_monthly['Profit'] = historical_monthly['Actual_Sales'] * (profit_margin_pct / 100)
    
    # Create figure with secondary y-axis
    fig = go.Figure()
    
    # Historical sales
    fig.add_trace(go.Scatter(
        x=historical_monthly['Date'],
        y=historical_monthly['Actual_Sales'],
        mode='lines+markers',
        name='Historical Sales',
        line=dict(color='blue', width=2),
        yaxis='y1'
    ))
    
    # Forecasted sales
    fig.add_trace(go.Scatter(
        x=forecast_monthly['Date'],
        y=forecast_monthly['Forecasted_Sales'],
        mode='lines+markers',
        name='Forecasted Sales',
        line=dict(color='green', width=2, dash='dash'),
        yaxis='y1'
    ))
    
    # Projected profit area
    fig.add_trace(go.Scatter(
        x=forecast_monthly['Date'],
        y=forecast_monthly['Profit'],
        mode='lines+markers',
        name=f'Projected Profit ({profit_margin_pct}% margin)',
        line=dict(color='gold', width=2),
        fill='tozeroy',
        yaxis='y2'
    ))
    
    fig.update_layout(
        title=f'Sales vs Profit Projection (Margin: {profit_margin_pct}%)',
        xaxis_title='Date',
        yaxis=dict(title='Sales Amount (₹)', side='left'),
        yaxis2=dict(title='Profit Amount (₹)', overlaying='y', side='right'),
        hovermode='x unified',
        template=TEMPLATE,
        height=500
    )
    return fig

def remove_zero_values(data: pd.DataFrame, value_col: str) -> pd.DataFrame:
    """Remove rows where value column is 0 or empty."""
    if value_col not in data.columns:
        return data.reset_index(drop=True)
    return data[data[value_col] > 0].reset_index(drop=True)

def display_grid_with_export(data: pd.DataFrame, title: str, key_prefix: str):
    """Display data in grid format with CSV and Excel download options (rounded)."""

    ##st.set_page_config(layout="wide")

    st.subheader(title)

    # Round numeric columns to 0 decimals for display & export. [web:9][web:26][web:15]
    rounded_data = data.copy()
    num_cols = rounded_data.select_dtypes(include="number").columns
    if len(num_cols) > 0:
        rounded_data[num_cols] = rounded_data[num_cols].round(0)

    # Display as AgGrid if available, else as regular dataframe
    if AGGRID_AVAILABLE:
        try:
            gob = GridOptionsBuilder.from_dataframe(rounded_data)
            gob.configure_default_column(
                resizable=True, sortable=True, filter=True, editable=False
            )
            gob.configure_pagination(paginationAutoPageSize=True)
            grid_options = gob.build()

            AgGrid(
                rounded_data,
                gridOptions=grid_options,
                theme="alpine",
                fit_columns_on_grid_load=True,
                height=400,
                key=f"{key_prefix}_grid",
            )
        except Exception:
            st.dataframe(rounded_data, use_container_width=True)
    else:
        st.dataframe(rounded_data, use_container_width=True)

    # Download buttons
    col1, col2 = st.columns(2)

    with col1:
        # CSV Download
        csv = rounded_data.to_csv(index=False).encode("utf-8")
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
                rounded_data.to_excel(writer, index=False, sheet_name=title[:31])
            buffer.seek(0)
            st.download_button(
                label="Download Excel",
                data=buffer.getvalue(),
                file_name=f"{key_prefix}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key=f"{key_prefix}_excel",
            )
        except Exception:
            ""

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
    "Product–Month Analysis": "prodmonth",
    "Credit Note Analysis": "credit",
    "Branch Business-Comparison": "branchcomparison",
    "Product Category-Comparison": "productcategorycomparison",
    "ARIMA Sales Forecasting": "arima",
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
            color_discrete_sequence=COLOR_SEQ,
            template=TEMPLATE,
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

    selected_fy_label = st.selectbox(
    "Select Financial Year",
    fy_labels
)

    # if len(selected_fy_labels_business) < 3:
    #     st.warning("Please select exactly 3 financial year sessions.")
    #     st.stop()

    selected_year = label_to_year[selected_fy_label]
    year_df = df[df["Year"] == selected_year].copy()

    #primary_fy_year = selected_fy_years_business
    #year_df = df[df["Year"] == primary_fy_year]

    month_act = year_df.groupby("Month")["ActAmt"].sum().reset_index()
    month_act = remove_zero_values(month_act, "ActAmt")
    month_act["Month"] = month_act["Month"].cat.remove_unused_categories() 

    month_cn = year_df.groupby("Month")["CNAmt"].sum().reset_index()
    month_cn = remove_zero_values(month_cn, "CNAmt")
    month_cn["Month"] = month_cn["Month"].cat.remove_unused_categories()

    month_total = (
        year_df.groupby("Month")[["ActAmt", "CNAmt"]].sum().reset_index()
    )
    month_total["TotalAmt"] = month_total["ActAmt"] + month_total["CNAmt"]
    month_total = remove_zero_values(month_total, "TotalAmt")
    month_total["Month"] = month_total["Month"].cat.remove_unused_categories()

    st.subheader("Choose Analysis Type")


    
    fig = px.bar(
        month_total,
        x="Month",
        y="TotalAmt",
        title="Total Month-wise Amount",
        color="Month",
        text="TotalAmt",
        color_discrete_sequence=COLOR_SEQ,
        template=TEMPLATE,
    )
    fig.update_traces(text=None)
    fig.update_layout(bargap=0.1, bargroupgap=0.05)
    fig.update_traces(width=0.8)
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

    
        fig = px.bar(
            month_act,
            x="Month",
            y="ActAmt",
            title="Month-wise Actual Sales",
            color="Month",
            text="ActAmt",
            color_discrete_sequence=COLOR_SEQ,
            template=TEMPLATE,
        )
        fig.update_traces(text=None)
        fig.update_layout(bargap=0.1, bargroupgap=0.05)
        fig.update_traces(width=0.8)
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

    
        fig = px.bar(
            month_cn,
            x="Month",
            y="CNAmt",
            title="Month-wise Credit Notes",
            color="Month",
            text="CNAmt",
            color_discrete_sequence=COLOR_SEQ,
            template=TEMPLATE,
        )
        fig.update_traces(text=None)
        fig.update_layout(bargap=0.1, bargroupgap=0.05)
        fig.update_traces(width=0.8)
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
    selected_fy_label = st.selectbox(
    "Select Financial Year",
    fy_labels
)

    selected_year = label_to_year[selected_fy_label]
    year_df = df[df["Year"] == selected_year].copy()
    # st.session_state.fy_start = year_df
    # year_df = df[year_df["Year"] == st.session_state.fy_start]
    # current_fy_label = year_to_label.get(
    #     st.session_state.fy_start, f"{st.session_state.fy_start}"
    # )

    st.header("Product–Month Analysis")

    col1, col2 = st.columns(2)

    with col1:
        mkt_types = year_df["MKTType"].dropna().unique()
        mkt_types = sorted([str(x) for x in mkt_types])
        selected_categories = st.multiselect(
            "Select Product Category (MKTType)",
            options=mkt_types,
            default=mkt_types,
        )

    with col2:
        months = year_df["Month"].dropna().unique()
        months = sorted([str(x) for x in months])
        selected_months = st.multiselect(
            "Select Month(s)",
            options=months,
            default=months,
        )

    # analysis_level = st.radio(
    #     "Choose Analysis Level",
    #     [
    #         "Month-wise Product Category Sales",
    #         "Yearly Product Category Sales",
    #     ],
    #     horizontal=True,
    # )

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
        # if analysis_level == "Month-wise Product Category Sales":
        agg_df_monthly = (
            filtered_df.groupby(["Month", "MKTType"])["ActAmt"]
            .sum()
            .reset_index()
        )
        agg_df_monthly = remove_zero_values(agg_df_monthly, "ActAmt")
        title = "Month-wise Product Category Sales"
        x_col = "Month"
        color_col = "MKTType"
        # else:
        # agg_df = (
        #     filtered_df.groupby("MKTType")["ActAmt"].sum().reset_index()
        # )
        # agg_df = remove_zero_values(agg_df, "ActAmt")
        # title = "Yearly Product Category Sales"
        # x_col = "MKTType"
        # color_col = "MKTType"

        if agg_df_monthly.empty:
            st.warning("No non-zero sales for the selected filters.")
        else:
            if chart_type == "Bar":
                fig = px.bar(
                    agg_df_monthly,
                    x=x_col,
                    y="ActAmt",
                    color=color_col,
                    title=title,
                    color_discrete_sequence=COLOR_SEQ,
                    template=TEMPLATE,
                )
                # fig.update_traces(text=None)
                # fig.update_layout(bargap=0.1, bargroupgap=0.05)
                # fig.update_traces(width=0.8)
            elif chart_type == "Line":
                fig = px.line(
                    agg_df_monthly,
                    x=x_col,
                    y="ActAmt",
                    color=color_col,
                    markers=True,
                    title=title,
                    color_discrete_sequence=COLOR_SEQ,
                    template=TEMPLATE,
                )
            elif chart_type == "Pie":
                pie_df = agg_df_monthly.groupby(color_col)["ActAmt"].sum().reset_index()
                pie_df = remove_zero_values(pie_df, "ActAmt")
                fig = px.pie(
                    pie_df,
                    names=color_col,
                    values="ActAmt",
                    title=title,
                    color_discrete_sequence=COLOR_SEQ,
                    template=TEMPLATE,
                )
            elif chart_type == "Area":
                fig = px.area(
                    agg_df_monthly,
                    x=x_col,
                    y="ActAmt",
                    color=color_col,
                    title=title,
                    color_discrete_sequence=COLOR_SEQ,
                    template=TEMPLATE,
                )

            fig.update_traces(text=None)
            st.plotly_chart(fig, use_container_width=True)

            display_grid_with_export(agg_df_monthly, "Product Sales Data", "prodmonth_data")

            # top_row = agg_df.sort_values("ActAmt", ascending=False).iloc[0]
            # st.markdown(
            #     f"""
            #     <hr>
            #     <p style="font-size:20px; font-weight:650;">
            #     Highest sales: <span style="color:#00ff88;">{top_row[color_col]}</span>
            #     with <span style="color:#00c0ff;">₹{top_row['ActAmt']:,.0f}</span>
            #     </p>
            #     """,
            #     unsafe_allow_html=True,
            # )

    if filtered_df.empty:
        st.warning("No data available for the selected filters.")
    else:
        # if analysis_level == "Month-wise Product Category Sales":
        # agg_df = (
        #     filtered_df.groupby(["Month", "MKTType"])["ActAmt"]
        #     .sum()
        #     .reset_index()
        # )
        # agg_df = remove_zero_values(agg_df, "ActAmt")
        # title = "Month-wise Product Category Sales"
        # x_col = "Month"
        # color_col = "MKTType"
        # else:
        agg_df_yearly = (
            filtered_df.groupby("MKTType")["ActAmt"].sum().reset_index()
        )
        agg_df_yearly = remove_zero_values(agg_df_yearly, "ActAmt")
        title = "Yearly Product Category Sales"
        x_col = "MKTType"
        color_col = "MKTType"

        if agg_df_yearly.empty:
            st.warning("No non-zero sales for the selected filters.")
        else:
            if chart_type == "Bar":
                fig = px.bar(
                    agg_df_yearly,
                    x=x_col,
                    y="ActAmt",
                    color=color_col,
                    title=title,
                    color_discrete_sequence=COLOR_SEQ,
                    template=TEMPLATE,
                )
                # fig.update_traces(text=None)
                # fig.update_layout(bargap=0.1, bargroupgap=0.05)
                # fig.update_traces(width=0.8)
            elif chart_type == "Line":
                fig = px.line(
                    agg_df_yearly,
                    x=x_col,
                    y="ActAmt",
                    color=color_col,
                    markers=True,
                    title=title,
                    color_discrete_sequence=COLOR_SEQ,
                    template=TEMPLATE,
                )
            elif chart_type == "Pie":
                pie_df = agg_df_yearly.groupby(color_col)["ActAmt"].sum().reset_index()
                pie_df = remove_zero_values(pie_df, "ActAmt")
                fig = px.pie(
                    pie_df,
                    names=color_col,
                    values="ActAmt",
                    title=title,
                    color_discrete_sequence=COLOR_SEQ,
                    template=TEMPLATE,
                )
            elif chart_type == "Area":
                fig = px.area(
                    agg_df_yearly,
                    x=x_col,
                    y="ActAmt",
                    color=color_col,
                    title=title,
                    color_discrete_sequence=COLOR_SEQ,
                    template=TEMPLATE,
                )

            fig.update_traces(text=None)
            st.plotly_chart(fig, use_container_width=True)

            display_grid_with_export(agg_df_yearly, "Product Sales Data", "prodmonth_data1")

            top_row = agg_df_yearly.sort_values("ActAmt", ascending=False).iloc[0]
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
    selected_fy_label = st.selectbox(
    "Select Financial Year",
    fy_labels
)

    selected_year = label_to_year[selected_fy_label]
    year_df = df[df["Year"] == selected_year].copy()

    st.header("Branch–Month Analysis")

    branch_list = sorted(year_df["BranchName"].unique())
    month_list = list(df["Month"].unique())

    colA, colB = st.columns(2)
    with colA:
        selected_branch = st.selectbox("Select Branch", branch_list)

    with colB:
        selected_months = st.multiselect("Select Month(s)", month_list, default=month_list)

    # metric_type = st.radio(
    #     "Choose Analysis Type",
    #     [
    #         "Total Branch Month-wise Sales",
    #         "Actual Branch Month-wise Sales",
    #         "Credit Note Branch Month-wise Sales",
    #     ],
    #     index=0,
    #     horizontal=True,
    # )

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

    # if metric_type == "Total Branch Month-wise Sales":
    value_col = "TotalAmt"
    title = f"Total Sales — {selected_branch}"
    # elif metric_type == "Actual Branch Month-wise Sales":
    #     value_col = "ActAmt"
    #     title = f"Actual Sales — {selected_branch}"
    # else:
    #     value_col = "CNAmt"
    #     title = f"Credit Notes — {selected_branch}"

    branch_month = remove_zero_values(branch_month, value_col)
    branch_month["Month"] = branch_month["Month"].cat.remove_unused_categories()

    if not branch_month.empty and branch_month[value_col].sum() > 0:
        if chart_type == "Bar":
            fig = px.bar(
                branch_month,
                x="Month",
                y=value_col,
                title=title,
                color="Month",
                color_discrete_sequence=COLOR_SEQ,
                template=TEMPLATE,
            )
            fig.update_traces(text=None)
            fig.update_layout(bargap=0.1, bargroupgap=0.05)
            fig.update_traces(width=0.8)
        elif chart_type == "Line":
            fig = px.line(
                branch_month,
                x="Month",
                y=value_col,
                title=title,
                markers=True,
                color="Month",
                color_discrete_sequence=COLOR_SEQ,
                template=TEMPLATE,
            )
        elif chart_type == "Pie":
            pie_df = branch_month[["Month", value_col]].copy()
            pie_df = remove_zero_values(pie_df, value_col)
            fig = px.pie(
                pie_df,
                names="Month",
                values=value_col,
                title=title,
                color_discrete_sequence=COLOR_SEQ,
                template=TEMPLATE,
            )
        elif chart_type == "Area":
            fig = px.area(
                branch_month,
                x="Month",
                y=value_col,
                title=title,
                color="Month",
                color_discrete_sequence=COLOR_SEQ,
                template=TEMPLATE,
            )

        fig.update_traces(text=None)
        st.plotly_chart(fig, use_container_width=True)

        display_grid_with_export(
            branch_month, f"Branch Sales - {selected_branch}", "branch_month_data1"
        )

        # top_row = branch_month.sort_values(value_col, ascending=False).iloc[0]

    value_col = "ActAmt"
    title = f"Actual Sales — {selected_branch}"
    # else:
    #     value_col = "CNAmt"
    #     title = f"Credit Notes — {selected_branch}"

    branch_month = remove_zero_values(branch_month, value_col)
    branch_month["Month"] = branch_month["Month"].cat.remove_unused_categories()

    if not branch_month.empty and branch_month[value_col].sum() > 0:
        if chart_type == "Bar":
            fig = px.bar(
                branch_month,
                x="Month",
                y=value_col,
                title=title,
                color="Month",
                color_discrete_sequence=COLOR_SEQ,
                template=TEMPLATE,
            )
            fig.update_traces(text=None)
            fig.update_layout(bargap=0.1, bargroupgap=0.05)
            fig.update_traces(width=0.8)
        elif chart_type == "Line":
            fig = px.line(
                branch_month,
                x="Month",
                y=value_col,
                title=title,
                markers=True,
                color="Month",
                color_discrete_sequence=COLOR_SEQ,
                template=TEMPLATE,
            )
        elif chart_type == "Pie":
            pie_df = branch_month[["Month", value_col]].copy()
            pie_df = remove_zero_values(pie_df, value_col)
            fig = px.pie(
                pie_df,
                names="Month",
                values=value_col,
                title=title,
                color_discrete_sequence=COLOR_SEQ,
                template=TEMPLATE,
            )
        elif chart_type == "Area":
            fig = px.area(
                branch_month,
                x="Month",
                y=value_col,
                title=title,
                color="Month",
                color_discrete_sequence=COLOR_SEQ,
                template=TEMPLATE,
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

    # if len(selected_fy_years) > 1:
    #     if selected_fy_years != list(
    #         range(
    #             selected_fy_years[0],
    #             selected_fy_years[0] + len(selected_fy_years),
    #         )
    #     ):
    #         st.error("Please select consecutive financial years only.")
    #         st.stop()

    # analysis_type = st.radio(
    #     "Choose Month-wise Analysis Type",
    #     [
    #         "Month-wise Actual Sales",
    #         "Month-wise Credit Note Analysis",
    #         "Month-wise Total Sales",
    #     ],
    #     horizontal=True,
    # )

    cumulative_view = st.checkbox("Show Cumulative Analysis")

    fy_df = df[df["Year"].isin(selected_fy_years)]

    analysis_type = "Month-wise Actual Sales"
    value_col = "ActAmt"
    title_prefix = "Actual Sales"
    # elif analysis_type == "Month-wise Credit Note Analysis":
    #     value_col = "CNAmt"
    #     title_prefix = "Credit Notes"
    # else:
    #     fy_df = fy_df.copy()
    #     fy_df["TotalAmt"] = fy_df["ActAmt"] + fy_df["CNAmt"]
    #     value_col = "TotalAmt"
    #     title_prefix = "Total Sales"

    month_fy = fy_df.groupby(["Year", "Month"])[value_col].sum().reset_index()
    month_fy = remove_zero_values(month_fy, value_col)

    month_fy["FinancialYear"] = month_fy["Year"].map(year_to_label)

    if cumulative_view:
        month_fy_plot = month_fy.groupby("Month")[value_col].sum().reset_index()
        month_fy_plot = remove_zero_values(month_fy_plot, value_col)
        month_fy["Month"] = month_fy["Month"].cat.remove_unused_categories()
        fig = px.bar(
            month_fy_plot,
            x="Month",
            y=value_col,
            title=f"Cumulative Month-wise {title_prefix}",
            color="Month",
            color_discrete_sequence=COLOR_SEQ,
            template=TEMPLATE,
        )
        display_grid_with_export(month_fy_plot, "Cumulative Data", "credit_cumulative1")
    else:
        month_fy_plot = month_fy
        fig = px.bar(
            month_fy_plot,
            x="Month",
            y=value_col,
            color="FinancialYear",
            barmode="group",
            title=f"Month-wise {title_prefix} Comparison",
            color_discrete_sequence=COLOR_SEQ,
            template=TEMPLATE,
        )
        display_grid_with_export(
            month_fy_plot, "Financial Year Comparison Data", "credit_fy_data1"
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

    analysis_type = "Month-wise Credit Note Analysis"
    value_col = "CNAmt"
    title_prefix = "Credit Notes"
    # else:
    #     fy_df = fy_df.copy()
    #     fy_df["TotalAmt"] = fy_df["ActAmt"] + fy_df["CNAmt"]
    #     value_col = "TotalAmt"
    #     title_prefix = "Total Sales"

    month_fy = fy_df.groupby(["Year", "Month"])[value_col].sum().reset_index()
    month_fy = remove_zero_values(month_fy, value_col)

    month_fy["FinancialYear"] = month_fy["Year"].map(year_to_label)

    if cumulative_view:
        month_fy_plot = month_fy.groupby("Month")[value_col].sum().reset_index()
        month_fy_plot = remove_zero_values(month_fy_plot, value_col)
        month_fy["Month"] = month_fy["Month"].cat.remove_unused_categories()
        fig = px.bar(
            month_fy_plot,
            x="Month",
            y=value_col,
            title=f"Cumulative Month-wise {title_prefix}",
            color="Month",
            color_discrete_sequence=COLOR_SEQ,
            template=TEMPLATE,
        )
        display_grid_with_export(month_fy_plot, "Cumulative Data", "credit_cumulative2")
    else:
        month_fy_plot = month_fy
        fig = px.bar(
            month_fy_plot,
            x="Month",
            y=value_col,
            color="FinancialYear",
            barmode="group",
            title=f"Month-wise {title_prefix} Comparison",
            color_discrete_sequence=COLOR_SEQ,
            template=TEMPLATE,
        )
        display_grid_with_export(
            month_fy_plot, "Financial Year Comparison Data", "credit_fy_data2"
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

    analysis_type = "Month-wise Total Sales"
    fy_df = fy_df.copy()
    fy_df["TotalAmt"] = fy_df["ActAmt"] + fy_df["CNAmt"]
    value_col = "TotalAmt"
    title_prefix = "Total Sales"

    month_fy = fy_df.groupby(["Year", "Month"])[value_col].sum().reset_index()
    month_fy = remove_zero_values(month_fy, value_col)

    month_fy["FinancialYear"] = month_fy["Year"].map(year_to_label)

    if cumulative_view:
        month_fy_plot = month_fy.groupby("Month")[value_col].sum().reset_index()
        month_fy_plot = remove_zero_values(month_fy_plot, value_col)
        month_fy["Month"] = month_fy["Month"].cat.remove_unused_categories()
        fig = px.bar(
            month_fy_plot,
            x="Month",
            y=value_col,
            title=f"Cumulative Month-wise {title_prefix}",
            color="Month",
            color_discrete_sequence=COLOR_SEQ,
            template=TEMPLATE,
        )
        display_grid_with_export(month_fy_plot, "Cumulative Data", "credit_cumulative3")
    else:
        month_fy_plot = month_fy
        fig = px.bar(
            month_fy_plot,
            x="Month",
            y=value_col,
            color="FinancialYear",
            barmode="group",
            title=f"Month-wise {title_prefix} Comparison",
            color_discrete_sequence=COLOR_SEQ,
            template=TEMPLATE,
        )
        display_grid_with_export(
            month_fy_plot, "Financial Year Comparison Data", "credit_fy_data3"
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

    # if len(selected_fy_years) > 1:
    #     if selected_fy_years != list(
    #         range(
    #             selected_fy_years[0],
    #             selected_fy_years[0] + len(selected_fy_years),
    #         )
    #     ):
    #         st.error("Please select consecutive financial years only.")
    #         st.stop()

    # analysis_type = st.radio(
    #     "Choose Month-wise Branch Analysis Type",
    #     [
    #         "Month-wise Actual Branch Sales",
    #         "Month-wise Branch Credit Note Analysis",
    #         "Month-wise Branch Total Sales",
    #     ],
    #     horizontal=True,
    # )

    cumulative_view = st.checkbox("Show Cumulative Analysis")

    branch_df = df[
        (df["BranchName"] == selected_branch) & (df["Year"].isin(selected_fy_years))
    ]

    analysis_type = "Month-wise Actual Branch Sales"
    value_col = "ActAmt"
    title_prefix = "Actual Sales"
    # elif analysis_type == "Month-wise Branch Credit Note Analysis":
    #     value_col = "CNAmt"
    #     title_prefix = "Credit Notes"
    # else:
    #     branch_df = branch_df.copy()
    #     branch_df["TotalAmt"] = branch_df["ActAmt"] + branch_df["CNAmt"]
    #     value_col = "TotalAmt"
    #     title_prefix = "Total Sales"

    month_fy_branch = (
        branch_df.groupby(["Year", "Month"])[value_col].sum().reset_index()
    )
    month_fy_branch = remove_zero_values(month_fy_branch, value_col)

    month_fy_branch["FinancialYear"] = month_fy_branch["Year"].map(year_to_label)

    if cumulative_view:
        cum_df = month_fy_branch.groupby("Month")[value_col].sum().reset_index()
        cum_df = remove_zero_values(cum_df, value_col)
        month_fy_branch["Month"] = month_fy_branch["Month"].cat.remove_unused_categories()

        fig = px.bar(
            cum_df,
            x="Month",
            y=value_col,
            title=f"Cumulative {title_prefix} — {selected_branch}",
            color="Month",
            color_discrete_sequence=COLOR_SEQ,
            template=TEMPLATE,
        )
        display_grid_with_export(cum_df, "Cumulative Branch Data", "branch_cumulative1")
    else:
        fig = px.bar(
            month_fy_branch,
            x="Month",
            y=value_col,
            color="FinancialYear",
            barmode="group",
            title=f"Month-wise {title_prefix} — {selected_branch}",
            color_discrete_sequence=COLOR_SEQ,
            template=TEMPLATE,
        )
        display_grid_with_export(
            month_fy_branch, "Branch FY Comparison Data", "branch_fy_data1"
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


    analysis_type = "Month-wise Branch Credit Note Analysis"
    value_col = "CNAmt"
    title_prefix = "Credit Notes"
    # else:
    #     branch_df = branch_df.copy()
    #     branch_df["TotalAmt"] = branch_df["ActAmt"] + branch_df["CNAmt"]
    #     value_col = "TotalAmt"
    #     title_prefix = "Total Sales"

    month_fy_branch = (
        branch_df.groupby(["Year", "Month"])[value_col].sum().reset_index()
    )
    month_fy_branch = remove_zero_values(month_fy_branch, value_col)

    month_fy_branch["FinancialYear"] = month_fy_branch["Year"].map(year_to_label)

    if cumulative_view:
        cum_df = month_fy_branch.groupby("Month")[value_col].sum().reset_index()
        cum_df = remove_zero_values(cum_df, value_col)
        month_fy_branch["Month"] = month_fy_branch["Month"].cat.remove_unused_categories()

        fig = px.bar(
            cum_df,
            x="Month",
            y=value_col,
            title=f"Cumulative {title_prefix} — {selected_branch}",
            color="Month",
            color_discrete_sequence=COLOR_SEQ,
            template=TEMPLATE,
        )
        display_grid_with_export(cum_df, "Cumulative Branch Data", "branch_cumulative2")
    else:
        fig = px.bar(
            month_fy_branch,
            x="Month",
            y=value_col,
            color="FinancialYear",
            barmode="group",
            title=f"Month-wise {title_prefix} — {selected_branch}",
            color_discrete_sequence=COLOR_SEQ,
            template=TEMPLATE,
        )
        display_grid_with_export(
            month_fy_branch, "Branch FY Comparison Data", "branch_fy_data2"
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


    analysis_type = "Month-wise Branch Total Sales"
    branch_df = branch_df.copy()
    branch_df["TotalAmt"] = branch_df["ActAmt"] + branch_df["CNAmt"]
    value_col = "TotalAmt"
    title_prefix = "Total Sales"

    month_fy_branch = (
        branch_df.groupby(["Year", "Month"])[value_col].sum().reset_index()
    )
    month_fy_branch = remove_zero_values(month_fy_branch, value_col)

    month_fy_branch["FinancialYear"] = month_fy_branch["Year"].map(year_to_label)

    if cumulative_view:
        cum_df = month_fy_branch.groupby("Month")[value_col].sum().reset_index()
        cum_df = remove_zero_values(cum_df, value_col)
        month_fy_branch["Month"] = month_fy_branch["Month"].cat.remove_unused_categories()

        fig = px.bar(
            cum_df,
            x="Month",
            y=value_col,
            title=f"Cumulative {title_prefix} — {selected_branch}",
            color="Month",
            color_discrete_sequence=COLOR_SEQ,
            template=TEMPLATE,
        )
        display_grid_with_export(cum_df, "Cumulative Branch Data", "branch_cumulative3")
    else:
        fig = px.bar(
            month_fy_branch,
            x="Month",
            y=value_col,
            color="FinancialYear",
            barmode="group",
            title=f"Month-wise {title_prefix} — {selected_branch}",
            color_discrete_sequence=COLOR_SEQ,
            template=TEMPLATE,
        )
        display_grid_with_export(
            month_fy_branch, "Branch FY Comparison Data", "branch_fy_data3"
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

    # if len(selected_fy_years) > 1:
    #     if selected_fy_years != list(
    #         range(
    #             selected_fy_years[0],
    #             selected_fy_years[0] + len(selected_fy_years),
    #         )
    #     ):
    #         st.error("Please select consecutive financial years only.")
    #         st.stop()

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

    # metric_type = st.radio(
    #     "Choose Sales Type",
    #     [
    #         "Actual Sales",
    #         "Credit Note Sales",
    #         "Total Sales",
    #     ],
    #     horizontal=True,
    # )

    filtered_df = base_df[
        (base_df["MKTType"].isin(selected_categories))
        & (base_df["Month"].isin(selected_months))
    ]

    if filtered_df.empty:
        st.warning("No data available for selected filters.")
        st.stop()

    metric_type = "Actual Sales"
    value_col = "ActAmt"
    title_prefix = "Actual Sales"
    # elif metric_type == "Credit Note Sales":
    #     value_col = "CNAmt"
    #     title_prefix = "Credit Notes"
    # else:
    #     filtered_df = filtered_df.copy()
    #     filtered_df["TotalAmt"] = filtered_df["ActAmt"] + filtered_df["CNAmt"]
    #     value_col = "TotalAmt"
    #     title_prefix = "Total Sales"

    if analysis_level == "Month-wise Product Category Sales":
        agg_df = (
            filtered_df.groupby(["Year", "Month", "MKTType"])[value_col]
            .sum()
            .reset_index()
        )
        agg_df = remove_zero_values(agg_df, value_col)
        agg_df["FinancialYear"] = agg_df["Year"].map(year_to_label)
        x_col = "Month"
        color_col = "MKTType"
    else:
        agg_df = (
            filtered_df.groupby(["Year", "MKTType"])[value_col].sum().reset_index()
        )
        agg_df = remove_zero_values(agg_df, value_col)
        agg_df["FinancialYear"] = agg_df["Year"].map(year_to_label)
        x_col = "MKTType"
        color_col = "FinancialYear"

    if agg_df.empty:
        st.warning("No non-zero data for selected filters.")
    else:
        if cumulative_view:
            cum_df = agg_df.groupby(x_col)[value_col].sum().reset_index()
            cum_df = remove_zero_values(cum_df, value_col)

            fig = px.bar(
                cum_df,
                x=x_col,
                y=value_col,
                title=f"Cumulative {analysis_level} — {title_prefix}",
                color=x_col,
                color_discrete_sequence=COLOR_SEQ,
                template=TEMPLATE,
            )
            display_grid_with_export(
                cum_df, "Cumulative Product Data", "product_cumulative1"
            )
        else:
            fig = px.bar(
                agg_df,
                x=x_col,
                y=value_col,
                color=color_col,
                barmode="group",
                title=f"{analysis_level} — {title_prefix}",
                color_discrete_sequence=COLOR_SEQ,
                template=TEMPLATE,
            )
            display_grid_with_export(
                agg_df, "Product Category Data", "product_category_data1"
            )

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

    metric_type == "Credit Note Sales"
    value_col = "CNAmt"
    title_prefix = "Credit Notes"
    # else:
    #     filtered_df = filtered_df.copy()
    #     filtered_df["TotalAmt"] = filtered_df["ActAmt"] + filtered_df["CNAmt"]
    #     value_col = "TotalAmt"
    #     title_prefix = "Total Sales"

    if analysis_level == "Month-wise Product Category Sales":
        agg_df = (
            filtered_df.groupby(["Year", "Month", "MKTType"])[value_col]
            .sum()
            .reset_index()
        )
        agg_df = remove_zero_values(agg_df, value_col)
        agg_df["FinancialYear"] = agg_df["Year"].map(year_to_label)
        x_col = "Month"
        color_col = "MKTType"
    else:
        agg_df = (
            filtered_df.groupby(["Year", "MKTType"])[value_col].sum().reset_index()
        )
        agg_df = remove_zero_values(agg_df, value_col)
        agg_df["FinancialYear"] = agg_df["Year"].map(year_to_label)
        x_col = "MKTType"
        color_col = "FinancialYear"

    if agg_df.empty:
        st.warning("No non-zero data for selected filters.")
    else:
        if cumulative_view:
            cum_df = agg_df.groupby(x_col)[value_col].sum().reset_index()
            cum_df = remove_zero_values(cum_df, value_col)

            fig = px.bar(
                cum_df,
                x=x_col,
                y=value_col,
                title=f"Cumulative {analysis_level} — {title_prefix}",
                color=x_col,
                color_discrete_sequence=COLOR_SEQ,
                template=TEMPLATE,
            )
            display_grid_with_export(
                cum_df, "Cumulative Product Data", "product_cumulative2"
            )
        else:
            fig = px.bar(
                agg_df,
                x=x_col,
                y=value_col,
                color=color_col,
                barmode="group",
                title=f"{analysis_level} — {title_prefix}",
                color_discrete_sequence=COLOR_SEQ,
                template=TEMPLATE,
            )
            display_grid_with_export(
                agg_df, "Product Category Data", "product_category_data2"
            )

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
        agg_df = remove_zero_values(agg_df, value_col)
        agg_df["FinancialYear"] = agg_df["Year"].map(year_to_label)
        x_col = "Month"
        color_col = "MKTType"
    else:
        agg_df = (
            filtered_df.groupby(["Year", "MKTType"])[value_col].sum().reset_index()
        )
        agg_df = remove_zero_values(agg_df, value_col)
        agg_df["FinancialYear"] = agg_df["Year"].map(year_to_label)
        x_col = "MKTType"
        color_col = "FinancialYear"

    if agg_df.empty:
        st.warning("No non-zero data for selected filters.")
    else:
        if cumulative_view:
            cum_df = agg_df.groupby(x_col)[value_col].sum().reset_index()
            cum_df = remove_zero_values(cum_df, value_col)

            fig = px.bar(
                cum_df,
                x=x_col,
                y=value_col,
                title=f"Cumulative {analysis_level} — {title_prefix}",
                color=x_col,
                color_discrete_sequence=COLOR_SEQ,
                template=TEMPLATE,
            )
            display_grid_with_export(
                cum_df, "Cumulative Product Data", "product_cumulative3"
            )
        else:
            fig = px.bar(
                agg_df,
                x=x_col,
                y=value_col,
                color=color_col,
                barmode="group",
                title=f"{analysis_level} — {title_prefix}",
                color_discrete_sequence=COLOR_SEQ,
                template=TEMPLATE,
            )
            display_grid_with_export(
                agg_df, "Product Category Data", "product_category_data3"
            )

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

# =====================================================================
# PAGE 8: ARIMA FORECASTING (from arima.ipynb)
# =====================================================================
elif st.session_state.page == "arima":
    st.header("📈 ARIMA Sales Forecasting")
    
    st.markdown("### Overview")
    st.markdown("""
    This page uses **ARIMA (AutoRegressive Integrated Moving Average)** modeling to:
    - Analyze historical sales data for stationarity
    - Create in-sample forecasts (backtesting) on the last 30 periods
    - Generate out-of-sample forecasts for the next 48 weeks
    - Evaluate model performance with RMSE and MAE metrics
    """)
    
    st.divider()
    
    # Run ARIMA forecast
    st.markdown("### Running ARIMA Analysis...")
    forecast_results = run_arima_forecast(df, arima_order=(2, 1, 2), test_size=30, forecast_periods=48)
    
    if forecast_results:
        # ===== STATIONARITY TEST =====
        st.markdown("### 1️⃣ Stationarity Test (Augmented Dickey-Fuller)")
        stat_results = forecast_results['stationarity']
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Test Statistic", f"{stat_results['Test Statistic']:.4f}")
        with col2:
            st.metric("p-value", f"{stat_results['p-value']:.4f}")
        with col3:
            status = "✅ Stationary" if forecast_results['is_stationary'] else "❌ Non-Stationary"
            st.markdown(f"<p style='font-size:16px; color:orange;'>{status}</p>", 
                       unsafe_allow_html=True)
        
        st.info(f"**Critical Values**: {', '.join([f'{k}: {v:.4f}' for k, v in stat_results['Critical Values'].items()])}")
        
        st.divider()
        
        # ===== MODEL SUMMARY =====
        st.markdown("### 2️⃣ ARIMA Model Summary")
        model = forecast_results['model']
        st.text(model.summary())
        
        st.divider()
        
        # ===== DIAGNOSTIC PLOTS =====
        st.markdown("### 3️⃣ Time Series Diagnostics (ACF/PACF)")
        historical_series = forecast_results['historical'].set_index('Date')['Actual_Sales']
        
        try:
            fig_diag = plot_arima_diagnostics(historical_series)
            st.pyplot(fig_diag)
        except Exception as e:
            st.warning(f"Could not generate ACF/PACF plots: {str(e)}")
        
        st.divider()
        
        # ===== SEASONAL DECOMPOSITION =====
        st.markdown("### 4️⃣ Seasonal Decomposition")
        try:
            fig_decomp = plot_seasonal_decomposition(historical_series)
            st.pyplot(fig_decomp)
        except Exception as e:
            st.warning(f"Could not generate seasonal decomposition: {str(e)}")
        
        st.divider()
        
        # ===== PERFORMANCE METRICS =====
        st.markdown("### 5️⃣ In-Sample Forecast Performance (Backtesting)")
        metrics = forecast_results['metrics']
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("RMSE (Root Mean Squared Error)", f"₹{metrics['rmse']:,.2f}")
        with col2:
            st.metric("MAE (Mean Absolute Error)", f"₹{metrics['mae']:,.2f}")
        
        # Display backtest data
        backtest_df = forecast_results['backtest'].copy()
        backtest_df['Error'] = backtest_df['Actual_Sales'] - backtest_df['Predicted_Sales']
        backtest_df['Abs_Error'] = backtest_df['Error'].abs()
        backtest_df['MAPE'] = (backtest_df['Abs_Error'] / backtest_df['Actual_Sales'] * 100).round(2)
        
        st.markdown("**Backtest Results (Last 30 periods):**")
        display_grid_with_export(
            backtest_df.round(2), 
            "In-Sample Forecast Results", 
            "arima_backtest"
        )
        
        st.divider()
        
        # ===== FORECAST COMPARISON CHART =====
        st.markdown("### 6️⃣ Complete Forecast Visualization")
        fig_forecast = plot_forecast_comparison(
            forecast_results['historical'],
            forecast_results['backtest'],
            forecast_results['forecast']
        )
        st.plotly_chart(fig_forecast, use_container_width=True)
        
        st.divider()
        
        # ===== FUTURE FORECASTS =====
        st.markdown("### 7️⃣ Out-of-Sample Forecast (Next 48 Weeks)")
        forecast_df = forecast_results['forecast'].copy()
        forecast_df['Forecasted_Sales'] = forecast_df['Forecasted_Sales'].round(0)
        
        display_grid_with_export(
            forecast_df, 
            "48-Week Future Sales Forecast", 
            "arima_forecast"
        )
        
        st.info("""
        **Key Insights:**
        - This forecast extends 48 weeks into the future
        - Uses rolling forecast method (retrains model after each prediction)
        - ARIMA(2,1,2) parameters: p=2 (AR), d=1 (differencing), q=2 (MA)
        - Higher RMSE/MAE suggests more volatility in the time series
        """)
        
        st.divider()
        
        # ===== PROFIT/LOSS ANALYSIS =====
        st.markdown("### 💰 Profit & Loss Projection Analysis")
        st.markdown("**See if future years will be profitable or loss-making based on your sales forecast**")
        
        # Get user input for profit margin
        col1, col2 = st.columns(2)
        with col1:
            profit_margin = st.slider(
                "Expected Profit Margin (%)",
                min_value=0,
                max_value=100,
                value=20,
                step=5,
                help="Your expected profit margin on sales. e.g., 20% means ₹20 profit per ₹100 sales"
            )
        with col2:
            st.metric("Margin Used", f"{profit_margin}%")
        
        # Calculate profit/loss analysis
        pl_analysis = calculate_profit_loss_analysis(
            forecast_results['forecast'],
            forecast_results['historical'],
            profit_margin_pct=profit_margin
        )
        
        # Display KPI metrics
        st.markdown("**📊 Profit/Loss Comparison:**")
        metric_cols = st.columns(4)
        
        with metric_cols[0]:
            st.metric(
                "Historical Profit",
                f"₹{pl_analysis['historical_profit']:,.0f}",
                delta=None
            )
        
        with metric_cols[1]:
            st.metric(
                "Projected Profit",
                f"₹{pl_analysis['projected_profit']:,.0f}",
                delta=f"₹{pl_analysis['profit_change']:,.0f}",
                delta_color="off"
            )
        
        with metric_cols[2]:
            color = "🟢" if pl_analysis['growth_rate'] >= 0 else "🔴"
            st.metric(
                "Growth Rate",
                f"{pl_analysis['growth_rate']:.1f}%",
                delta="Positive" if pl_analysis['growth_rate'] >= 0 else "Negative",
                delta_color="normal" if pl_analysis['growth_rate'] >= 0 else "inverse"
            )
        
        with metric_cols[3]:
            health_color = "🟢" if pl_analysis['health_status'] == "Good" else "🟡" if pl_analysis['health_status'] == "Warning" else "🔴"
            st.markdown(f"<div style='text-align:center'><h4>{health_color} {pl_analysis['health_status']}</h4></div>", 
                       unsafe_allow_html=True)
        
        # Display interpretation
        st.markdown("**📌 What This Means:**")
        if pl_analysis['growth_rate'] > 10:
            st.success(f"""
            ✅ **EXCELLENT OUTLOOK**: Sales are forecasted to grow by {pl_analysis['growth_rate']:.1f}%!
            - Your projected profit will increase by ₹{pl_analysis['profit_change']:,.0f}
            - This translates to strong business momentum
            - Expected future profit: ₹{pl_analysis['projected_profit']:,.0f}
            """)
        elif pl_analysis['growth_rate'] > 0:
            st.success(f"""
            ✅ **POSITIVE OUTLOOK**: Sales are forecasted to grow by {pl_analysis['growth_rate']:.1f}%
            - Your projected profit will increase by ₹{pl_analysis['profit_change']:,.0f}
            - Steady growth indicates healthy business trajectory
            - Expected future profit: ₹{pl_analysis['projected_profit']:,.0f}
            """)
        elif pl_analysis['growth_rate'] > -10:
            st.warning(f"""
            ⚠️ **CAUTION**: Sales are forecasted to decline slightly by {abs(pl_analysis['growth_rate']):.1f}%
            - Profit may decrease by ₹{abs(pl_analysis['profit_change']):,.0f}
            - Monitor market trends and consider strategies to boost sales
            - Expected future profit: ₹{pl_analysis['projected_profit']:,.0f}
            """)
        else:
            st.error(f"""
            ❌ **CRITICAL ALERT**: Sales are forecasted to decline significantly by {abs(pl_analysis['growth_rate']):.1f}%!
            - Profit loss of ₹{abs(pl_analysis['profit_change']):,.0f} is projected
            - Immediate action required to reverse the trend
            - Expected future profit: ₹{pl_analysis['projected_profit']:,.0f}
            - Consider: cost reduction, market expansion, product innovation
            """)
        
        # Profit/Loss visualization
        st.markdown("**📈 Visual Comparison:**")
        fig_pl = plot_profit_loss_chart(
            forecast_results['forecast'],
            forecast_results['historical'],
            profit_margin_pct=profit_margin
        )
        st.plotly_chart(fig_pl, use_container_width=True)
        
        # Detailed profit/loss table
        st.markdown("**📋 Weekly Profit Projection Details:**")
        detailed_pl = forecast_results['forecast'].copy()
        detailed_pl['Forecasted_Profit'] = detailed_pl['Forecasted_Sales'] * (profit_margin / 100)
        detailed_pl['Weekly_Status'] = detailed_pl['Forecasted_Profit'].apply(
            lambda x: '✅ Profit' if x > 0 else '❌ Loss'
        )
        detailed_pl = detailed_pl[['Date', 'Forecasted_Sales', 'Forecasted_Profit', 'Weekly_Status']]
        detailed_pl.columns = ['Date', 'Sales (₹)', 'Profit (₹)', 'Status']
        detailed_pl['Sales (₹)'] = detailed_pl['Sales (₹)'].round(0)
        detailed_pl['Profit (₹)'] = detailed_pl['Profit (₹)'].round(0)
        
        display_grid_with_export(
            detailed_pl,
            "Weekly Profit/Loss Projection",
            "arima_profit_loss"
        )
        
        st.divider()
        
        # ===== INTERPRETATION GUIDE =====
        st.markdown("### 📚 How to Interpret Results")
        
        with st.expander("📖 Understanding ACF/PACF Plots"):
            st.markdown("""
            - **ACF (Autocorrelation)**: Shows correlation between observations at different lags
              - Slow decay = likely non-stationary
              - Sharp cutoff = indicates MA order
            
            - **PACF (Partial Autocorrelation)**: Shows correlation with specific lags
              - Sharp cutoff = indicates AR order
              - Number of significant spikes = suggests p or q parameters
            """)
        
        with st.expander("📊 Understanding Seasonal Decomposition"):
            st.markdown("""
            The decomposition breaks down the time series into:
            - **Trend**: Long-term direction (upward/downward)
            - **Seasonal**: Repeating patterns (12-month cycles for monthly data)
            - **Residual**: Random noise/unexplained variation
            """)
        
        with st.expander("⚙️ ARIMA Model Parameters"):
            st.markdown("""
            **ARIMA(p, d, q) = (2, 1, 2)**:
            - **p=2**: Uses up to 2 past values to predict future (AutoRegressive)
            - **d=1**: Differencing applied once to make series stationary
            - **q=2**: Moving average smooths error terms using 2 past residuals
            
            These parameters were optimized from notebook analysis.
            """)
        
        with st.expander("💰 Understanding Profit/Loss Projections"):
            st.markdown("""
            ### How to Interpret Your Profit/Loss Analysis:
            
            **Growth Rate:**
            - **Positive (>0%)**: Sales are growing → More profit likely
            - **Flat (0%)**: Sales stable → Profit remains same
            - **Negative (<0%)**: Sales declining → Profit decreases
            
            **Profit Margin:**
            - Set based on your industry/costs
            - Medicine typically has 15-30% margins
            - Formula: **Profit = Sales × (Margin % / 100)**
            
            **Health Status:**
            - 🟢 **Good**: Growth > 0% (expanding business)
            - 🟡 **Warning**: -10% < Growth < 0% (slight decline, monitor)
            - 🔴 **Critical**: Growth < -10% (significant decline, action needed)
            
            **What to Do Based on Outlook:**
            - ✅ **Growth**: Expand capacity, invest more, increase inventory
            - ⚠️ **Decline**: Cut costs, improve marketing, find new markets
            - ❌ **Crisis**: Urgent action - restructure, pivot, or consider partnerships
            
            **Key Metrics:**
            - **Historical Profit**: What you earned in the past period
            - **Projected Profit**: Expected future earnings
            - **Profit Change**: Difference (positive/negative)
            """)
    else:
        st.error("Failed to run ARIMA forecast. Check your data and try again.")
