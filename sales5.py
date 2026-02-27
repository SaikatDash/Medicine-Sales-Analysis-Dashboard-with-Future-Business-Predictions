import streamlit as st
import pandas as pd
import numpy as np
import pickle
import matplotlib.pyplot as plt

st.title("📊 Monthly Sales Forecasting App")

# Load model
@st.cache_resource
def load_model():
    with open("Model/prophet_model_yearly.pkl", "rb") as f:
        model = pickle.load(f)
    return model

model = load_model()

# Dropdown for years
years = st.selectbox(
    "Select number of years to forecast:",
    [1, 2, 3, 4, 5]
)

# Convert years → months
future_months = years * 12

if st.button("Generate Forecast"):

    # Create future dataframe
    future = model.make_future_dataframe(periods=future_months, freq='MS')
    future['cap']=100000000
    future['floor']=0
    forecast = model.predict(future)
    forecast_future = forecast.tail(future_months)
    # Total predicted sales
    # total_sales = forecast['yhat'].sum()

    # Month-wise prediction table
    forecast_table = forecast_future[['ds', 'yhat']]
    forecast_table.columns = ['Month', 'Predicted Sales']

    st.subheader("📅 Month-wise Sales Prediction")
    st.dataframe(forecast_table)

    # Total sales
    total_sales = forecast_table['Predicted Sales'].sum()

    st.subheader("💰 Total Predicted Sales")
    st.success(f"₹ {total_sales:,.2f}")

    # ---------- LINE GRAPH ----------
    st.subheader("📈 Line Chart")

    fig1, ax1 = plt.subplots()
    ax1.plot(forecast_table['Month'], forecast_table['Predicted Sales'])
    ax1.set_xlabel("Month")
    ax1.set_ylabel("Predicted Sales")
    plt.xticks(rotation=45)

    st.pyplot(fig1)

    # ---------- BAR GRAPH ----------
    st.subheader("📊 Bar Chart")

    fig2, ax2 = plt.subplots()
    ax2.bar(forecast_table['Month'].astype(str), forecast_table['Predicted Sales'])
    ax2.set_xlabel("Month")
    ax2.set_ylabel("Predicted Sales")
    plt.xticks(rotation=90)

    st.pyplot(fig2)

st.markdown("---")
st.write("Built with Prophet & Streamlit 🚀")