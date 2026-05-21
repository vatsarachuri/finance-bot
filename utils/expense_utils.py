import pandas as pd
import matplotlib.pyplot as plt
import os
import io


def convert_excel_to_csv(file_path):
    """Convert .xlsx or .xls file to .csv"""
    try:
        df = pd.read_excel(file_path)
        csv_path = file_path.replace(".xlsx", ".csv").replace(".xls", ".csv")
        df.to_csv(csv_path, index=False)
        return csv_path
    except Exception as e:
        raise ValueError(f"Excel conversion failed: {e}")


def analyze_expenses(file_path, income, target):
    """Read expenses CSV or Excel and analyze spending."""
    if file_path.endswith((".xlsx", ".xls")):
        file_path = convert_excel_to_csv(file_path)

    df = pd.read_csv(file_path)

    # Normalize column names
    df.columns = [col.strip().lower() for col in df.columns]

    total_expenses = df["amount"].sum()
    balance = income - total_expenses
    savings_gap = target - balance

    # Pie chart
    fig, ax = plt.subplots()
    category_sum = df.groupby("category")["amount"].sum()
    category_sum.plot(kind="pie", autopct="%1.1f%%", ax=ax)
    ax.set_ylabel("")
    plt.title("Expense Breakdown")
    chart_path = "data/expense_chart.png"
    plt.savefig(chart_path)
    plt.close(fig)

    summary = (
        f"**Expense Summary**\n"
        f"💸 Total Expenses: ₹{total_expenses:.2f}\n"
        f"💰 Income: ₹{income:.2f}\n"
        f"🎯 Target Savings: ₹{target:.2f}\n"
        f"📊 Actual Balance: ₹{balance:.2f}\n"
    )

    if savings_gap > 0:
        summary += f"⚠️ You need to reduce expenses by ₹{savings_gap:.2f} to hit your goal."
    else:
        summary += f"✅ Great! You’re saving ₹{abs(savings_gap):.2f} more than your target."

    return summary, chart_path, df.to_dict()
