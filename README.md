# Finance Tracker – Smart Suggestions API (Flask + Pandas)

This is a lightweight Python microservice that analyzes users' expense data and provides smart budget suggestions based on recent spending patterns.

This service is used as part of the [Personal Finance Tracker+](https://github.com/raghavarora01/FinanceTrackerUI) full-stack project.

---

##  Live Demo

Flask API deployed on Render:  
https://finance-tracker-python-api.onrender.com/suggestions

---

##  Features

- Accepts JSON expense data (last 30 days)
- Processes with Pandas
- Returns budget suggestions such as:
  - "You’re spending a lot on Food. Try to reduce it by 15%."
  - "Your travel expenses increased a lot this month."
- Integrated into Node.js backend for frontend consumption

---

##  Tech Stack

- Python 3.10+
- Flask (REST API)
- Pandas (Data analysis)

---

## 🛠 How to Run Locally

### 1. Clone the Repository


```bash
git clone https://github.com/raghavarora01/FinanceTrackerPyhtonAPI.git
cd FinanceTrackerPyhtonAPI


### 2. Install Dependencies

pip install -r requirements.txt

### 3. Run the Server

python app.py



