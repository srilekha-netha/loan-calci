import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
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

    extra_payment = st.number_input("Extra Monthly Payment", min_value=0.0, value=0.0, step=100.0)
    lump_sum = st.number_input("One-time Lump Sum Payment", min_value=0.0, value=0.0, step=1000.0)
    insurance = st.checkbox("Add Insurance (0.5% annually)?", value=False)

    submitted = st.form_submit_button("Calculate Loan")

if not submitted:
    st.info("Fill the form above and click **Calculate Loan** to see results.")
    st.stop()

# ---------------- Calculations ----------------
insurance_rate = 0.005 if insurance else 0.0
start_date = datetime.today()

df = amortization_schedule(
    principal=principal,
    annual_rate=rate / 100.0,
    years=years,
    periods_per_year=12,
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
    st.header("Interactive Graphs")

    # Balance over time
    fig1 = px.line(df, x="date", y="balance", title="Outstanding Balance Over Time")
    st.plotly_chart(fig1, use_container_width=True)

    # Cumulative Principal vs Interest
    df_cum = df.copy()
    df_cum["cumulative_principal"] = df_cum["principal"].cumsum()
    df_cum["cumulative_interest"] = df_cum["interest"].cumsum()
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=df_cum["date"], y=df_cum["cumulative_principal"], mode="lines", name="Principal"))
    fig2.add_trace(go.Scatter(x=df_cum["date"], y=df_cum["cumulative_interest"], mode="lines", name="Interest"))
    fig2.update_layout(title="Cumulative Principal vs Interest")
    st.plotly_chart(fig2, use_container_width=True)

    # Yearly Interest Payments
    df_yearly = df.copy()
    df_yearly["year"] = pd.to_datetime(df_yearly["date"]).dt.year
    yearly_interest = df_yearly.groupby("year")["interest"].sum().reset_index()
    fig3 = px.bar(yearly_interest, x="year", y="interest", title="Yearly Interest Payments")
    st.plotly_chart(fig3, use_container_width=True)

elif page == "What-If Analysis":
    st.header("What-If Analysis")
    st.write("Compare scenarios with vs. without extra payments.")

    base_df = amortization_schedule(principal, rate / 100.0, years, periods_per_year=12, start_date=start_date)

    months_saved = len(base_df) - len(df)
    interest_saved = base_df["interest"].sum() - df["interest"].sum()

    st.success(f"✅ Loan will be paid off **{months_saved} months earlier**")
    st.success(f"✅ Interest saved: {human_currency(interest_saved)}")
