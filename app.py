from flask import Flask, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from bson import ObjectId
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os
import logging


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
logging.getLogger("pymongo").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

# Flask app initialization
app = Flask(__name__)
CORS(app, supports_credentials=True, origins=[
    "https://finance-tracker-ui-ten.vercel.app"
])

load_dotenv()
MONGO_URI = os.getenv('MONGO_URI')
PORT = int(os.environ.get("PORT", 5000))  
DB_NAME = 'Finance_Tracker'


try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    db = client[DB_NAME]
    expenses_collection = db['expenses']
    budgets_collection = db['budgets']
    client.server_info()
    logger.info(f"Connected to MongoDB database: {DB_NAME}")
except Exception as e:
    logger.error(f"Failed to connect to MongoDB: {str(e)}")
    raise

@app.route("/")
def home():
    return jsonify({"message": "🚀 Finance Tracker Python API is live!"})

@app.route('/suggestions/<user_id>', methods=['GET'])
def get_suggestions(user_id):
    try:
        logger.info(f"Processing suggestions for user_id: {user_id}")

        if not ObjectId.is_valid(user_id):
            return jsonify({"error": "Invalid user ID"}), 400

        # Current month expenses
        thirty_days_ago = datetime.now() - timedelta(days=30)
        expenses = expenses_collection.find({
            'userId': ObjectId(user_id),
            'Date': {'$gte': thirty_days_ago}
        })

        expense_list = []
        for expense in expenses:
            try:
                expense_list.append({
                    'Amount': float(expense.get('Amount', 0)),
                    'Category': expense.get('Category', 'Unknown'),
                    'Date': expense['Date'],
                    'Payment_Method': expense.get('Payment_Method', 'Unknown'),
                    'Notes': expense.get('Notes', '')
                })
            except (KeyError, TypeError):
                continue

        if not expense_list:
            return jsonify({
                "user_id": user_id,
                "suggestions": ["No expenses found for the last 30 days. Start tracking to get suggestions!"]
            }), 200

        df = pd.DataFrame(expense_list)

        suggestions = []

        category_spending = df.groupby('Category')['Amount'].sum().sort_values(ascending=False)
        total_spending = category_spending.sum()

        if not category_spending.empty:
            top_category = category_spending.index[0]
            top_amount = category_spending.iloc[0]
            if top_amount / total_spending > 0.4:
                suggestions.append(
                    f"You're spending a lot on {top_category} (₹{top_amount:.2f}). Try to reduce it by 15% next month."
                )

        sixty_days_ago = datetime.now() - timedelta(days=60)
        prev_expenses = expenses_collection.find({
            'userId': ObjectId(user_id),
            'Date': {'$gte': sixty_days_ago, '$lt': thirty_days_ago}
        })

        prev_expense_list = [
            {
                'Amount': float(exp.get('Amount', 0)),
                'Category': exp.get('Category', 'Unknown'),
                'Date': exp['Date']
            } for exp in prev_expenses
        ]

        prev_df = pd.DataFrame(prev_expense_list)
        if not prev_df.empty:
            for category in df['Category'].unique():
                current_spend = df[df['Category'] == category]['Amount'].sum()
                prev_spend = prev_df[prev_df['Category'] == category]['Amount'].sum()
                if prev_spend > 0 and current_spend / prev_spend > 1.5:
                    suggestions.append(
                        f"Your {category} expenses increased significantly this month "
                        f"(₹{current_spend:.2f} vs ₹{prev_spend:.2f}). Consider reviewing these expenses."
                    )

        current_month = datetime.now().strftime('%Y-%m')
        budgets = budgets_collection.find({
            'userId': ObjectId(user_id),
            'month': current_month
        })

        for budget in budgets:
            try:
                category = budget.get('category', 'Unknown')
                budget_limit = float(budget.get('limit', 0))
                category_spent = df[df['Category'] == category]['Amount'].sum()
                if category_spent > budget_limit > 0:
                    suggestions.append(
                        f"You've exceeded your ₹{budget_limit:.2f} budget for {category} "
                        f"(spent ₹{category_spent:.2f}). Try to cut back next month."
                    )
            except (KeyError, TypeError):
                continue

        if total_spending > 5000:
            suggestions.append(
                f"Your total spending this month is ₹{total_spending:.2f}. "
                f"Consider setting stricter budgets for next month."
            )

        return jsonify({
            "user_id": user_id,
            "suggestions": suggestions or ["No specific suggestions at this time. Keep tracking your expenses!"]
        }), 200

    except Exception as e:
        logger.error(f"Error processing suggestions: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=PORT, debug=True)
