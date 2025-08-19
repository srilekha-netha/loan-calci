import pandas as pd
import numpy as np
from datetime import timedelta

def monthly_payment(principal, annual_rate, years, periods_per_year=12):
    """
    Calculate fixed periodic payment (EMI) for given loan.
    """
    n_periods = years * periods_per_year
    rate = annual_rate / periods_per_year
    if rate > 0:
        payment = principal * rate / (1 - (1 + rate) ** -n_periods)
    else:
        payment = principal / n_periods
    return payment

def amortization_schedule(principal, annual_rate, years, periods_per_year, start_date,
                          extra_payment=0.0, lump_sum=0.0,
                          insurance_rate_annual=0.0,
                          variable_after_months=None, variable_new_rate=None):
    schedule = []
    monthly_rate = annual_rate / periods_per_year
    n_periods = years * periods_per_year

    # use helper function here
    payment = monthly_payment(principal, annual_rate, years, periods_per_year)

    balance = principal - lump_sum
    current_date = pd.to_datetime(start_date)

    for i in range(1, n_periods + 1):
        if variable_after_months and i == variable_after_months + 1:
            annual_rate = variable_new_rate
            monthly_rate = annual_rate / periods_per_year
            payment = monthly_payment(balance, annual_rate, years - (i-1)/periods_per_year, periods_per_year)

        interest = balance * monthly_rate
        principal_component = payment - interest

        if extra_payment > 0:
            principal_component += extra_payment

        insurance = balance * (insurance_rate_annual / periods_per_year)
        total_payment = principal_component + interest + insurance

        balance -= principal_component
        if balance < 0:
            principal_component += balance
            total_payment += balance
            balance = 0

        schedule.append({
            "period": i,
            "date": current_date,
            "principal": round(principal_component, 2),
            "interest": round(interest, 2),
            "insurance": round(insurance, 2),
            "total_payment": round(total_payment, 2),
            "balance": round(balance, 2)
        })

        if balance <= 0:
            break

        # advance date
        if periods_per_year == 12:
            current_date += pd.DateOffset(months=1)
        elif periods_per_year == 4:
            current_date += pd.DateOffset(months=3)
        else:
            current_date += pd.DateOffset(years=1)

    return pd.DataFrame(schedule)

def human_currency(amount):
    return f"₹{amount:,.0f}"
