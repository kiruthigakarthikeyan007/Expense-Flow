
import calendar
from datetime import date, timedelta

import pandas as pd
import plotly.express as px
import streamlit as st

from database import (
    create_table,
    add_expense,
    get_expenses,
    delete_expense,
)

# ---------- Page configuration ----------
st.set_page_config(
    page_title="ExpenseFlow",
    page_icon="💸",
    layout="wide",
)

st.markdown("""
<style>
    .block-container {
        padding-top: 2rem;
        padding-bottom: 3rem;
    }
    div[data-testid="stMetric"] {
        background: #f0f5ff;
        padding: 18px;
        border-radius: 12px;
        border: 1px solid #dbe5f5;
    }
</style>
""", unsafe_allow_html=True)

create_table()

CATEGORIES = [
    "Food", "Transport", "Shopping", "Bills",
    "Education", "Health", "Entertainment", "Other"
]

st.title("💸 ExpenseFlow")
st.caption("Track your spending. Understand your habits. Take control.")

# ---------- Load data ----------
expenses = get_expenses()
df = pd.DataFrame(expenses)

if not df.empty:
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
    df = df.dropna(subset=["date", "amount"])

# ---------- Sidebar ----------
st.sidebar.header("ExpenseFlow")
page = st.sidebar.radio(
    "Navigate",
    ["Dashboard", "Add Expense", "Transactions"]
)

st.sidebar.caption("Your expenses are stored locally in SQLite.")

# ---------- Add expense page ----------
if page == "Add Expense":
    st.header("Add a new expense")

    with st.form("expense_form", clear_on_submit=True):
        amount = st.number_input(
            "Amount (₹)",
            min_value=0.01,
            max_value=10_000_000.00,
            value=100.00,
            step=50.00,
        )

        category = st.selectbox("Category", CATEGORIES)
        description = st.text_input(
            "Description",
            placeholder="e.g. Lunch with friends",
            max_chars=150,
        )
        expense_date = st.date_input(
            "Date",
            value=date.today(),
            max_value=date.today(),
        )

        submitted = st.form_submit_button(
            "Save Expense",
            type="primary",
            use_container_width=True,
        )

        if submitted:
            add_expense(
                round(amount, 2),
                category,
                description.strip(),
                expense_date.isoformat(),
            )
            st.success("Expense saved successfully!")
            st.rerun()

# ---------- Dashboard page ----------
elif page == "Dashboard":
    st.header("Your financial overview")

    if df.empty:
        st.info(
            "No expenses yet. Open **Add Expense** in the sidebar "
            "to record your first transaction."
        )
    else:
        today = date.today()
        current_month = today.strftime("%Y-%m")

        month_df = df[
            df["date"].dt.strftime("%Y-%m") == current_month
        ]

        today_df = df[
            df["date"].dt.date == today
        ]

        total_spent = df["amount"].sum()
        monthly_spent = month_df["amount"].sum()
        today_spent = today_df["amount"].sum()
        transaction_count = len(df)

        col1, col2, col3, col4 = st.columns(4)

        col1.metric("Total Spent", f"₹{total_spent:,.2f}")
        col2.metric("This Month", f"₹{monthly_spent:,.2f}")
        col3.metric("Today", f"₹{today_spent:,.2f}")
        col4.metric("Transactions", transaction_count)

        st.divider()

        left, right = st.columns(2)

        with left:
            st.subheader("Spending by category")

            category_df = (
                df.groupby("category", as_index=False)["amount"]
                .sum()
                .sort_values("amount", ascending=False)
            )

            fig = px.pie(
                category_df,
                names="category",
                values="amount",
                hole=0.55,
                title="Where your money goes",
            )
            st.plotly_chart(fig, use_container_width=True)

        with right:
            st.subheader("Monthly spending")

            monthly_df = df.copy()
            monthly_df["month"] = (
                monthly_df["date"].dt.to_period("M").astype(str)
            )

            monthly_df = (
                monthly_df.groupby("month", as_index=False)["amount"]
                .sum()
                .sort_values("month")
            )

            fig = px.bar(
                monthly_df,
                x="month",
                y="amount",
                labels={
                    "month": "Month",
                    "amount": "Amount (₹)",
                },
                title="Spending over time",
            )
            st.plotly_chart(fig, use_container_width=True)

        st.subheader("Recent transactions")
        recent = df.sort_values(
            ["date"], ascending=False
        ).head(5).copy()

        recent["date"] = recent["date"].dt.strftime("%d %b %Y")
        recent["amount"] = recent["amount"].map(
            lambda value: f"₹{value:,.2f}"
        )

        st.dataframe(
            recent[["date", "category", "description", "amount"]],
            hide_index=True,
            use_container_width=True,
        )

# ---------- Transactions page ----------
elif page == "Transactions":
    st.header("All transactions")

    if df.empty:
        st.info("No transactions found. Add your first expense!")
    else:
        filter1, filter2 = st.columns(2)

        with filter1:
            selected_categories = st.multiselect(
                "Filter by category",
                CATEGORIES,
                default=CATEGORIES,
            )

        with filter2:
            min_date = df["date"].min().date()
            max_date = df["date"].max().date()

            date_range = st.date_input(
                "Filter by date range",
                value=(min_date, max_date),
                min_value=min_date,
                max_value=max_date,
            )

        filtered = df[
            df["category"].isin(selected_categories)
        ].copy()

        if isinstance(date_range, (tuple, list)) and len(date_range) == 2:
            start_date, end_date = date_range
            filtered = filtered[
                (filtered["date"].dt.date >= start_date)
                & (filtered["date"].dt.date <= end_date)
            ]

        st.write(f"**{len(filtered)} transaction(s) found**")

        display_df = filtered.copy()
        display_df["date"] = display_df["date"].dt.strftime("%Y-%m-%d")

        st.dataframe(
            display_df[
                ["id", "date", "category", "description", "amount"]
            ],
            hide_index=True,
            use_container_width=True,
        )

        csv_df = filtered.copy()
        csv_df["date"] = csv_df["date"].dt.strftime("%Y-%m-%d")

        csv_data = csv_df.to_csv(index=False).encode("utf-8")

        st.download_button(
            "⬇️ Export filtered transactions to CSV",
            data=csv_data,
            file_name="expenseflow_transactions.csv",
            mime="text/csv",
        )

        st.divider()
        st.subheader("Delete a transaction")

        transaction_ids = filtered["id"].tolist()

        if transaction_ids:
            selected_id = st.selectbox(
                "Choose transaction ID",
                transaction_ids,
            )

            if st.button("Delete selected transaction", type="secondary"):
                delete_expense(int(selected_id))
                st.success("Transaction deleted.")
                st.rerun()
