import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import date
import plotly.express as px
import plotly.graph_objects as go
from utils.finance import amortization_schedule, monthly_payment, human_currency

st.set_page_config(page_title="Loan Calculator", layout="wide")

# ---------------- Sidebar Navigation ----------------
st.sidebar.title("Navigation")
page = st.sidebar.radio(
    "Go to:",
    ["Overview", "Amortization Table", "Graphs", "What-If Analysis"]
)

# ---------------- Input Form ----------------
st.title("📊 Interactive Loan Calculator")

with st.form("loan_form"):
    st.subheader("Enter Loan Details")

    name = st.text_input("Name")
    age = st.number_input("Age", min_value=18, max_value=100, value=25)
    principal = st.number_input("Loan Amount", min_value=1000, step=1000, value=500000)
    rate = st.number_input("Annual Interest Rate (%)", min_value=0.0, value=7.5, step=0.1)
    years = st.slider("Duration (Years)", 1, 40, 20)

    # ✅ Added start date picker
    start_date = st.date_input("Loan Start Date", value=date.today())

    extra_payment = st.number_input("Extra Monthly Payment", min_value=0.0, value=0.0, step=100.0)
    lump_sum = st.number_input("One-time Lump Sum Payment", min_value=0.0, value=0.0, step=1000.0)
    insurance = st.checkbox("Add Insurance (0.5% annually)?", value=False)

    submitted = st.form_submit_button("Calculate Loan")

if not submitted:
    st.info("Fill the form above and click **Calculate Loan** to see results.")
    st.stop()

# ---------------- Calculations ----------------
insurance_rate = 0.005 if insurance else 0.0
df = amortization_schedule(
    principal=principal,
    annual_rate=rate / 100.0,
    years=years,
    periods_per_year=12,  # monthly compounding
    start_date=start_date,
    extra_payment=extra_payment,
    lump_sum=lump_sum,
    insurance_rate_annual=insurance_rate,
)

emi = monthly_payment(principal, rate / 100.0, years)
total_paid = df["total_payment"].sum()
total_interest = df["interest"].sum()

# ---------------- Page Content ----------------
if page == "Overview":
    st.header("Overview")
    col1, col2, col3 = st.columns(3)
    col1.metric("Monthly EMI", human_currency(emi))
    col2.metric("Total Payment", human_currency(total_paid))
    col3.metric("Total Interest", human_currency(total_interest))

elif page == "Amortization Table":
    st.header("Amortization Schedule")
    st.dataframe(df, use_container_width=True)
    st.download_button(
        "Download CSV",
        df.to_csv(index=False).encode(),
        "amortization_schedule.csv",
        "text/csv"
    )

elif page == "Graphs":
    st.header("📊 Interactive Loan Visualizations")

    # --- 1. Balance Over Time ---
    fig1 = px.line(df, x="date", y="balance", 
                   title="Outstanding Balance Over Time",
                   labels={"date": "Date", "balance": "Balance Amount"},
                   markers=True)
    fig1.update_traces(line=dict(color="royalblue", width=3))
    st.plotly_chart(fig1, use_container_width=True)

    # --- 2. Cumulative Principal vs Interest (Stacked Area) ---
    df_cum = df.copy()
    df_cum["principal_cum"] = df_cum["principal"].cumsum()
    df_cum["interest_cum"] = df_cum["interest"].cumsum()

    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=df_cum["date"], y=df_cum["principal_cum"],
                              mode='lines', name="Principal Paid", stackgroup="one",
                              line=dict(width=0.5), fillcolor="seagreen"))
    fig2.add_trace(go.Scatter(x=df_cum["date"], y=df_cum["interest_cum"],
                              mode='lines', name="Interest Paid", stackgroup="one",
                              line=dict(width=0.5), fillcolor="tomato"))
    fig2.update_layout(title="Cumulative Principal vs Interest",
                       xaxis_title="Date", yaxis_title="Amount")
    st.plotly_chart(fig2, use_container_width=True)

    # --- 3. Yearly Interest Payments (Bar Chart) ---
    df_yearly = df.groupby(df["date"].dt.year).agg({"interest": "sum"}).reset_index()
    fig3 = px.bar(df_yearly, x="date", y="interest", 
                  title="Yearly Interest Payments",
                  labels={"date": "Year", "interest": "Interest Paid"},
                  text_auto=".2s",
                  color="interest",
                  color_continuous_scale="Oranges")
    st.plotly_chart(fig3, use_container_width=True)


elif page == "What-If Analysis":
    st.header("What-If Analysis")
    st.write("Compare scenarios with vs. without extra payments.")

    # ✅ Pass periods_per_year & start_date here as well
    base_df = amortization_schedule(
        principal=principal,
        annual_rate=rate / 100.0,
        years=years,
        periods_per_year=12,
        start_date=start_date
    )

    months_saved = len(base_df) - len(df)
    interest_saved = base_df["interest"].sum() - df["interest"].sum()

    st.success(f"✅ Loan will be paid off **{months_saved} months earlier**")
    st.success(f"✅ Interest saved: {human_currency(interest_saved)}")
