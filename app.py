"""Run with: python -m streamlit run app.py"""

import calendar
from datetime import date
from decimal import Decimal

import altair as alt
import pandas as pd
import streamlit as st

from tracker import (category_totals, make_expense, merge_expenses, money,
                     monthly_expenses, parse_money, read_csv, write_csv)

st.set_page_config(page_title="Pocket | Expense tracker", page_icon="💸", layout="wide")
st.markdown("""
<style>
.block-container { max-width: 1280px; padding-top: 2rem; padding-bottom: 3rem; }
h1 { letter-spacing: -0.045em; }
h2, h3 { letter-spacing: -0.02em; }
[data-testid="stMetric"] { background: white; border: 1px solid #dce4ed;
    border-radius: 16px; padding: 1.1rem 1.3rem; }
[data-testid="stMetricValue"] { font-weight: 700; }
[data-testid="stSidebar"] { border-right: 1px solid #dce4ed; }
[data-testid="stForm"] { background: white; border-radius: 16px; }
.eyebrow { color: #087f6d; font-size: .8rem; letter-spacing: .14em; font-weight: 700; }
.quiet { color: #52657b; font-size: .95rem; }
@media (max-width: 640px) { .block-container { padding-top: 1rem; } }
</style>
""", unsafe_allow_html=True)

# Session state belongs to this visitor. No shared global expense list or server CSV.
if "expenses" not in st.session_state:
    st.session_state.expenses = []
    st.session_state.budgets = {}
    st.session_state.add_version = 0
    st.session_state.data_version = 0
    st.session_state.import_version = 0

today = date.today()


def notify(message):
    st.session_state.notice = message


def demo_expenses(month):
    """Fictional examples are loaded only when the visitor requests them."""
    examples = [(2, "Food", "25", "Lunch with friends"),
                (5, "Travel", "48", "Train pass"),
                (8, "Food", "86.50", "Weekly groceries"),
                (12, "Entertainment", "18", "Movie night"),
                (15, "Shopping", "64", "Running shoes")]
    return [make_expense(f"{month}-{day:02}", category, amount, description)
            for day, category, amount, description in examples]


with st.sidebar:
    st.markdown("### 💸 Pocket")
    st.caption("Your expenses. A clearer picture.")
    st.divider()
    st.markdown("#### Review a month")
    year = st.number_input("Year", min_value=1900, max_value=2100, value=today.year, step=1)
    month_number = st.selectbox("Month", list(range(1, 13)), index=today.month - 1,
                                format_func=lambda number: calendar.month_name[number])
    month = f"{year:04}-{month_number:02}"
    month_name = f"{calendar.month_name[month_number]} {year}"

    st.divider()
    st.markdown("#### Monthly budget")
    with st.form(f"budget-{month}"):
        saved_budget = st.session_state.budgets.get(month)
        budget_text = st.text_input("Budget ($)",
                                   value=str(Decimal(saved_budget) / 100) if saved_budget else "2000",
                                   help="Dollar signs and correctly grouped commas are accepted.")
        set_budget = st.form_submit_button("Set budget", width="stretch")
    if set_budget:
        try:
            st.session_state.budgets[month] = parse_money(budget_text)
            st.success(f"Budget set for {month_name}.")
        except ValueError as error:
            st.error(str(error))

    st.divider()
    st.markdown("#### Keep your expenses")
    st.caption("This is a session-based demo. Download your expenses before closing or refreshing. Upload the CSV to restore them. Budgets must be re-entered.")
    st.download_button("Download all expenses", data=write_csv(st.session_state.expenses),
                       file_name="expenses.csv", mime="text/csv", width="stretch",
                       on_click="ignore")
    st.caption("Includes every month, using the same CSV columns as your Python project.")

    if not st.session_state.expenses:
        st.divider()
        if st.button("Try sample expenses", width="stretch"):
            st.session_state.expenses = demo_expenses(month)
            st.session_state.budgets.setdefault(month, 200000)
            notify("Fictional sample expenses loaded. You can delete them or start over below.")
            st.rerun()

st.markdown('<div class="eyebrow">PERSONAL EXPENSE TRACKER</div>', unsafe_allow_html=True)
st.title("Make room for what matters.")
st.caption(f"{month_name} · Track everyday spending, one expense at a time.")
if "notice" in st.session_state:
    st.success(st.session_state.pop("notice"))

visible = monthly_expenses(st.session_state.expenses, month)
spent = sum(item["cents"] for item in visible)
budget = st.session_state.budgets.get(month)
first, second, third = st.columns(3)
first.metric("Monthly budget", money(budget) if budget else "Not set")
second.metric("Spent this month", money(spent))
third.metric("Over budget" if budget and spent > budget else "Left to spend",
             money(abs(budget - spent)) if budget else "—")
if budget:
    st.progress(min(spent / budget, 1.0), text=f"{spent / budget:.1%} of your budget used · {len(visible)} expenses")
    if spent > budget:
        st.warning(f"You have exceeded your {month_name} budget by {money(spent - budget)}.")
else:
    st.info("Set a monthly budget in the sidebar to see your remaining balance.")

st.write("")
form_column, chart_column = st.columns([1, 1.3], gap="large")
with form_column:
    st.subheader("Add an expense")
    # A fresh form key clears the fields only after a successful addition.
    with st.form(f"add-{st.session_state.add_version}"):
        default_date = today if month == today.strftime("%Y-%m") else date(year, month_number, 1)
        expense_date = st.date_input("Date", value=default_date,
                                    min_value=date(1900, 1, 1), max_value=date(2100, 12, 31))
        category = st.selectbox("Category", ["Food", "Travel", "Housing", "Shopping", "Health", "Entertainment", "Other"])
        custom_category = st.text_input("Custom category (optional)", max_chars=60,
                                        placeholder="Leave blank to use the category above")
        amount = st.text_input("Amount ($)", placeholder="25.00 or $1,250.00")
        description = st.text_input("Description", max_chars=300, placeholder="What was it for?")
        add = st.form_submit_button("Add expense", type="primary", width="stretch")
    if add:
        try:
            expense = make_expense(expense_date.isoformat(), custom_category or category, amount, description)
            st.session_state.expenses.append(expense)
            st.session_state.add_version += 1
            st.session_state.data_version += 1
            message = f"Added {money(expense['cents'])} for {expense['category']}."
            if not expense["date"].startswith(month):
                message += f" Switch to {expense['date'][:7]} to see it in the monthly totals."
            notify(message)
            st.rerun()
        except ValueError as error:
            st.error(str(error))

with chart_column:
    st.subheader("Where your money goes")
    totals = category_totals(visible)
    if totals:
        chart_data = pd.DataFrame([{"Category": key, "Amount": cents / 100} for key, cents in totals.items()])
        chart = (alt.Chart(chart_data).mark_bar(color="#087F6D", cornerRadiusEnd=5)
                 .encode(x=alt.X("Amount:Q", title="Spent ($)", axis=alt.Axis(format="$,.0f")),
                         y=alt.Y("Category:N", sort="-x", title=None),
                         tooltip=["Category:N", alt.Tooltip("Amount:Q", format="$,.2f")])
                 .properties(height=240).configure_view(strokeWidth=0)
                 .configure_axis(labelFontSize=13, titleFontSize=13))
        st.altair_chart(chart, width="stretch")
        largest = next(iter(totals))
        st.caption(f"Largest category: {largest} · {money(totals[largest])} · {totals[largest] / spent:.0%} of spending")
    else:
        with st.container(border=True):
            st.markdown("#### A fresh start")
            st.write("Add your first expense to see your spending by category.")
            st.caption("Already have expenses? Import your CSV below, or try the sample expenses in the sidebar.")

st.subheader("Your expenses")
show_all = st.checkbox("Show every month", value=False)
table_items = sorted(st.session_state.expenses if show_all else visible,
                     key=lambda item: item["date"], reverse=True)
if table_items:
    table = pd.DataFrame([{"Date": item["date"], "Category": item["category"],
                           "Amount ($)": item["cents"] / 100, "Description": item["description"]}
                          for item in table_items])
    st.dataframe(table, hide_index=True, width="stretch",
                 column_config={"Amount ($)": st.column_config.NumberColumn(format="$%.2f")})
    st.caption(f"{len(table_items)} expenses shown · {money(sum(item['cents'] for item in table_items))} total")
    with st.expander("Delete an expense"):
        by_id = {item["id"]: item for item in table_items}
        def expense_label(identifier):
            item = by_id[identifier]
            return f"{item['date']} · {item['category']} · {money(item['cents'])} · {item['description']}"
        with st.form(f"delete-{month}-{show_all}-{st.session_state.data_version}"):
            selected = st.selectbox("Expense to delete", list(by_id), format_func=expense_label)
            confirmed = st.checkbox("Confirm deletion of the selected expense")
            delete = st.form_submit_button("Delete selected expense")
        if delete:
            if not confirmed:
                st.error("Check the confirmation box before deleting.")
            else:
                st.session_state.expenses = [item for item in st.session_state.expenses if item["id"] != selected]
                st.session_state.data_version += 1
                notify("Expense deleted. Download a new CSV to keep this change.")
                st.rerun()
else:
    st.info("No expenses to show for this selection.")

with st.expander("Import a CSV"):
    st.write("Bring in expenses from your terminal tracker or a previous download. Import adds to your current list.")
    uploaded = st.file_uploader("Choose an expense CSV", type=["csv"],
                                key=f"upload-{st.session_state.import_version}")
    skip_duplicates = st.checkbox("Skip exact duplicate expenses", value=True)
    if uploaded is not None:
        try:
            imported, errors = read_csv(uploaded.getvalue())
            st.caption(f"{len(imported)} valid expenses · {len(errors)} invalid rows skipped")
            if errors:
                st.warning("Some rows cannot be imported. Your current expenses have not changed.")
                for error in errors[:10]:
                    st.text(error)
                if len(errors) > 10:
                    st.caption(f"Plus {len(errors) - 10} additional invalid rows.")
            if st.button("Import valid expenses", disabled=not imported, type="primary"):
                before = len(st.session_state.expenses)
                combined, skipped = merge_expenses(st.session_state.expenses, imported, skip_duplicates)
                st.session_state.expenses = combined
                st.session_state.data_version += 1
                st.session_state.import_version += 1
                notify(f"Imported {len(combined) - before} expenses; skipped {skipped} duplicates. Choose their month or show every month to view them.")
                st.rerun()
        except ValueError as error:
            st.error(str(error))

with st.expander("Start over"):
    st.caption("Clears expenses and budgets from this browser session. Download your CSV first if you want to keep it.")
    with st.form(f"reset-{st.session_state.data_version}"):
        confirm_reset = st.checkbox("Clear all my session data")
        reset = st.form_submit_button("Start fresh")
    if reset:
        if not confirm_reset:
            st.error("Confirm that you want to clear your session data.")
        else:
            st.session_state.expenses = []
            st.session_state.budgets = {}
            st.session_state.data_version += 1
            st.session_state.import_version += 1
            st.session_state.add_version += 1
            notify("Your session is empty. Add an expense or import a CSV to begin.")
            st.rerun()

st.divider()
st.caption("Built in Python · Your browser session is separate from other visitors · Download a CSV to keep your expenses")
