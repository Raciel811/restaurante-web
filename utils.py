from models import db, Order, Expense
from datetime import datetime, timedelta

def generate_daily_report():
    today = datetime.utcnow().date()
    sales = db.session.query(db.func.sum(Order.total)).filter(db.func.date(Order.date) == today).scalar() or 0
    expenses = db.session.query(db.func.sum(Expense.amount)).filter(db.func.date(Expense.date) == today).scalar() or 0
    profit = sales - expenses
    return {'sales': sales, 'expenses': expenses, 'profit': profit}

def generate_monthly_report():
    month_start = datetime.utcnow().replace(day=1)
    sales = db.session.query(db.func.sum(Order.total)).filter(Order.date >= month_start).scalar() or 0
    expenses = db.session.query(db.func.sum(Expense.amount)).filter(Expense.date >= month_start).scalar() or 0
    profit = sales - expenses
    return {'sales': sales, 'expenses': expenses, 'profit': profit}