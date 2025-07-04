# from flask import Flask, jsonify
# from flask_cors import CORS
# from pymongo import MongoClient
# from bson import ObjectId
# import pandas as pd
# from datetime import datetime, timedelta
# from dotenv import load_dotenv
# import os
# import logging

# # Set up logging
# logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
# logger = logging.getLogger(__name__)

# app = Flask(__name__)
# CORS(app)  # Enable CORS for Next.js frontend

# # Load environment variables
# load_dotenv()
# MONGO_URI = os.getenv('MONGO_URI')
# PORT = int(os.getenv('PORT', 5000))
# DB_NAME = 'Finance_Tracker'  # Matches your MONGO_URI

# # Connect to MongoDB
# try:
#     client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
#     db = client[DB_NAME]
#     expenses_collection = db['expenses']
#     budgets_collection = db['budgets']
#     client.server_info()  # Test connection
#     logger.info(f"Successfully connected to MongoDB database: {DB_NAME}")
# except Exception as e:
#     logger.error(f"Failed to connect to MongoDB: {str(e)}")
#     raise

# @app.route('/suggestions/<user_id>', methods=['GET'])
# def get_suggestions(user_id):
#     try:
#         logger.info(f"Processing suggestions for user_id: {user_id}")
        
#         # Validate user_id
#         if not ObjectId.is_valid(user_id):
#             logger.error(f"Invalid user ID: {user_id}")
#             return jsonify({"error": "Invalid user ID"}), 400

#         # Fetch expenses for the user from the last 30 days
#         thirty_days_ago = datetime.now().replace(tzinfo=None) - timedelta(days=30)
#         logger.debug(f"Querying expenses for user_id: {user_id}, date >= {thirty_days_ago}")
#         expenses = expenses_collection.find({
#             'userId': ObjectId(user_id),
#             'Date': {'$gte': thirty_days_ago}
#         })

#         # Convert to list for Pandas
#         expense_list = []
#         for expense in expenses:
#             try:
#                 expense_list.append({
#                     'Amount': float(expense.get('Amount', 0)),  # Handle missing/invalid Amount
#                     'Category': expense.get('Category', 'Unknown'),  # Handle missing Category
#                     'Date': expense['Date'],  # Assume Date is ISODate
#                     'Payment_Method': expense.get('Payment_Method', 'Unknown'),
#                     'Notes': expense.get('Notes', '')
#                 })
#             except (KeyError, TypeError) as e:
#                 logger.error(f"Error in expense document: {str(e)}, document: {expense}")
#                 continue
#         logger.debug(f"Found {len(expense_list)} expenses: {expense_list}")

#         if not expense_list:
#             logger.info("No expenses found for the last 30 days")
#             return jsonify({
#                 "user_id": user_id,
#                 "suggestions": ["No expenses found for the last 30 days. Start tracking to get suggestions!"]
#             }), 200

#         # Analyze expenses with Pandas
#         try:
#             df = pd.DataFrame(expense_list)
#             logger.debug(f"Pandas DataFrame created with {len(df)} rows")
#         except Exception as e:
#             logger.error(f"Failed to create Pandas DataFrame: {str(e)}")
#             return jsonify({"error": "Error processing expenses data"}), 500

#         suggestions = []

#         # Calculate total spending per category
#         try:
#             category_spending = df.groupby('Category')['Amount'].sum().sort_values(ascending=False)
#             total_spending = category_spending.sum()
#             logger.debug(f"Category spending: {category_spending.to_dict()}, Total: {total_spending}")
#         except Exception as e:
#             logger.error(f"Error calculating category spending: {str(e)}")
#             return jsonify({"error": "Error analyzing expenses"}), 500

#         # Suggestion 1: High spending category
#         if not category_spending.empty:
#             top_category = category_spending.index[0]
#             top_amount = category_spending.iloc[0]
#             if top_amount / total_spending > 0.4:  # If one category is >40% of total
#                 suggestions.append(f"You're spending a lot on {top_category} (₹{top_amount:.2f}). Try to reduce it by 15% next month.")

#         # Suggestion 2: Month-over-month increase
#         sixty_days_ago = datetime.now().replace(tzinfo=None) - timedelta(days=60)
#         prev_expenses = expenses_collection.find({
#             'userId': ObjectId(user_id),
#             'Date': {'$gte': sixty_days_ago, '$lt': thirty_days_ago}
#         })
#         prev_expense_list = [
#             {
#                 'Amount': float(expense.get('Amount', 0)),
#                 'Category': expense.get('Category', 'Unknown'),
#                 'Date': expense['Date']
#             }
#             for expense in prev_expenses
#         ]
#         try:
#             prev_df = pd.DataFrame(prev_expense_list)
#             logger.debug(f"Previous period DataFrame created with {len(prev_df)} rows")
#             if not prev_df.empty:
#                 for category in df['Category'].unique():
#                     current_spend = df[df['Category'] == category]['Amount'].sum()
#                     prev_spend = prev_df[prev_df['Category'] == category]['Amount'].sum()
#                     if prev_spend > 0 and current_spend / prev_spend > 1.5:  # 50% increase
#                         suggestions.append(f"Your {category} expenses increased significantly this month (₹{current_spend:.2f} vs ₹{prev_spend:.2f}). Consider reviewing these expenses.")
#             else:
#                 logger.debug("No previous expenses found, skipping month-over-month comparison")
#         except Exception as e:
#             logger.error(f"Error analyzing previous expenses: {str(e)}")
#             return jsonify({"error": "Error analyzing previous expenses"}), 500

#         # Suggestion 3: Budget exceed check
#         current_month = datetime.now().strftime('%Y-%m')
#         logger.debug(f"Querying budgets for user_id: {user_id}, month: {current_month}")
#         budgets = budgets_collection.find({
#             'userId': ObjectId(user_id),
#             'month': current_month
#         })
#         budget_list = list(budgets)
#         logger.debug(f"Found {len(budget_list)} budgets: {budget_list}")
#         for budget in budget_list:
#             try:
#                 category = budget.get('category', 'Unknown')
#                 budget_limit = float(budget.get('limit', 0))
#                 category_spent = df[df['Category'] == category]['Amount'].sum()
#                 if category_spent > budget_limit > 0:  # Check budget_limit > 0 to avoid false positives
#                     suggestions.append(f"You've exceeded your ₹{budget_limit:.2f} budget for {category} (spent ₹{category_spent:.2f}). Try to cut back next month.")
#             except (KeyError, TypeError) as e:
#                 logger.error(f"Error processing budget: {str(e)}, budget: {budget}")
#                 continue

#         # Suggestion 4: General high spending alert
#         if total_spending > 5000:  # Adjust threshold as needed
#             suggestions.append(f"Your total spending this month is ₹{total_spending:.2f}. Consider setting stricter budgets for next month.")

#         # Return suggestions
#         logger.info(f"Generated {len(suggestions)} suggestions for user_id: {user_id}")
#         return jsonify({
#             "user_id": user_id,
#             "suggestions": suggestions or ["No specific suggestions at this time. Keep tracking your expenses!"]
#         }), 200

#     except Exception as e:
#         logger.error(f"Error processing suggestions: {str(e)}")
#         return jsonify({"error": str(e)}), 500

# if __name__ == '__main__':
#     app.run(host='0.0.0.0', port=PORT, debug=True)



from flask import Flask, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from bson import ObjectId
import pandas as pd
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Suppress verbose logs from pymongo and urllib3
logging.getLogger("pymongo").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

app = Flask(__name__)
CORS(app)  # Enable CORS for Next.js frontend

# Load environment variables
load_dotenv()
MONGO_URI = os.getenv('MONGO_URI')
PORT = int(os.getenv('PORT', 5000))
DB_NAME = 'Finance_Tracker'

# Connect to MongoDB
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

@app.route('/suggestions/<user_id>', methods=['GET'])
def get_suggestions(user_id):
    try:
        logger.info(f"Processing suggestions for user_id: {user_id}")

        if not ObjectId.is_valid(user_id):
            return jsonify({"error": "Invalid user ID"}), 400

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

        try:
            df = pd.DataFrame(expense_list)
        except Exception:
            return jsonify({"error": "Error processing expenses data"}), 500

        suggestions = []

        # Suggestion 1: High spending category
        try:
            category_spending = df.groupby('Category')['Amount'].sum().sort_values(ascending=False)
            total_spending = category_spending.sum()
        except Exception:
            return jsonify({"error": "Error analyzing expenses"}), 500

        if not category_spending.empty:
            top_category = category_spending.index[0]
            top_amount = category_spending.iloc[0]
            if top_amount / total_spending > 0.4:
                suggestions.append(
                    f"You're spending a lot on {top_category} (₹{top_amount:.2f}). Try to reduce it by 15% next month."
                )

        # Suggestion 2: Month-over-month increase
        sixty_days_ago = datetime.now() - timedelta(days=60)
        prev_expenses = expenses_collection.find({
            'userId': ObjectId(user_id),
            'Date': {'$gte': sixty_days_ago, '$lt': thirty_days_ago}
        })
        prev_expense_list = [
            {
                'Amount': float(expense.get('Amount', 0)),
                'Category': expense.get('Category', 'Unknown'),
                'Date': expense['Date']
            }
            for expense in prev_expenses
        ]
        try:
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
        except Exception:
            return jsonify({"error": "Error analyzing previous expenses"}), 500

        # Suggestion 3: Budget exceed check
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

        # Suggestion 4: General high spending alert
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
