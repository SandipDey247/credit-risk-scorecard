# Credit Risk Scorecard & Underwriting Engine

A retail credit-risk project that generates synthetic lending data, stores it in MySQL, performs feature analysis, trains a Weight of Evidence (WoE)-based logistic-regression scorecard, and provides an interactive Streamlit application for applicant underwriting decisions.

The project uses a 30,000-record synthetic borrower/loan portfolio and produces a production-style scorecard based on credit score, interest rate, and loan-to-income ratio.

## Project Overview

This project simulates an end-to-end credit-risk modeling workflow:

1. Generate borrower, loan, and repayment datasets.
2. Create a relational MySQL database using schema.sql.
3. Load the generated data into MySQL.
4. Build an analytical modeling view with derived risk features.
5. Evaluate predictor strength using Information Value (IV).
6. Train a logistic-regression scorecard using WoE-transformed variables.
7. Export the final scorecard and score applicants through a Streamlit dashboard.

The target variable is Default_Flag, where 1 indicates a defaulted loan and 0 indicates a non-defaulted loan.

## Features

- Synthetic data generation: Creates 30,000 borrowers, loans, and repayment-history records with realistic Indian borrower names, cities, income ranges, loan purposes, and repayment behavior.
- MySQL database design: Uses normalized borrowers, loans, and repayment_history tables with foreign keys and indexes.
- Feature engineering: Calculates loan-to-income ratio, estimated monthly debt burden, principal-paid ratio, and other modeling variables through a SQL view.
- IV analysis: Ranks candidate features by Information Value and classifies them as weak, medium, strong, or suspicious predictors.
- WoE scorecard: Converts selected numeric features into five quantile bins, calculates Weight of Evidence, and trains a logistic-regression model.
- Model evaluation: Reports ROC-AUC, Gini coefficient, and Kolmogorov-Smirnov (KS) statistic on a stratified 80/20 train-test split.
- Scorecard scaling: Applies a standard retail-banking scaling approach using a base score of 600, good:bad odds of 50:1, and 20 Points to Double the Odds (PDO).
- Interactive underwriting app: Lets users enter applicant details and receive an automated approve, refer, or decline decision with a score breakdown.

## Project Structure

.
├── app.py                       # Streamlit underwriting dashboard
├── main.py                      # Generates synthetic data and loads it into MySQL
├── db.py                        # MySQL connection using environment variables
├── schema.sql                   # Database schema and analytical modeling view
├── model_prep.py                # IV analysis and feature evaluation
├── train_scorecard.py           # WoE binning, logistic regression, scorecard export
├── score_applicant.py           # Command-line applicant scoring
├── borrowers.csv                # Generated borrower data
├── loans.csv                    # Generated loan data
├── repayment_history.csv        # Generated repayment/default data
└── credit_scorecard_matrix.csv  # Exported production scorecard

## Technologies Used

| Category | Tools |
|---|---|
| Language | Python |
| Data processing | pandas, NumPy |
| Database | MySQL 8.0+ |
| Database connectivity | SQLAlchemy, PyMySQL |
| Machine learning | scikit-learn |
| Dashboard | Streamlit |
| Configuration | python-dotenv |

## Database Schema

The project contains three main tables:

| Table | Purpose |
|---|---|
| borrowers | Stores borrower demographics, income, employment type, credit score, city, and marital status. |
| loans | Stores loan amount, interest rate, term, purpose, issue date, and borrower reference. |
| repayment_history | Stores repayment tenure, maximum days past due, default flag, principal paid, and interest paid. |

A modeling view, v_credit_risk_modeling, joins all three tables and adds derived features such as Loan_to_Income_Ratio, Est_Monthly_Debt_Burden, and Principal_Paid_Ratio.

## Setup Instructions

### 1. Clone or download the project

Place all project files in one folder.

### 2. Install dependencies

pip install pandas numpy sqlalchemy pymysql python-dotenv scikit-learn streamlit

### 3. Create the MySQL database

Run the SQL schema file in MySQL Workbench or another MySQL client:

SOURCE schema.sql;

Or open schema.sql and execute it. This creates the credit_risk_db database, tables, indexes, and the v_credit_risk_modeling view.

### 4. Create a .env file

Create a .env file in the project root:

DB_USER=your_mysql_username
DB_PASSWORD=your_mysql_password
DB_HOST=localhost
DB_PORT=3306
DB_NAME=credit_risk_db

Do not commit the .env file to GitHub if it contains real database credentials.

### 5. Generate and load data

python main.py

This script generates 30,000 synthetic records for borrowers, loans, and repayment history, saves them as CSV files, and inserts them into MySQL.

## Running the Analysis

### Feature analysis

python model_prep.py

This loads the modeling view, calculates IV for candidate variables, and prints a ranked feature-importance table.

### Train the scorecard

python train_scorecard.py

This performs the following steps:

- Loads data from v_credit_risk_modeling
- Selects Interest_Rate, Credit_Score, and Loan_to_Income_Ratio
- Creates five quantile bins per feature
- Calculates WoE values
- Trains a logistic-regression model
- Computes AUC, Gini, and KS statistics
- Exports the scorecard to credit_scorecard_matrix.csv

### Score an applicant from the command line

python score_applicant.py

This script evaluates two sample applicants using the saved scorecard and returns their final score, point breakdown, and underwriting decision.

## Run the Streamlit App

streamlit run app.py

Then open the local URL shown in the terminal, usually:

http://localhost:8501

The dashboard allows the user to enter:

- Credit score
- Annual income
- Requested loan amount
- Offered interest rate

It automatically calculates the loan-to-income ratio, assigns scorecard points, displays the final credit score, and returns an underwriting decision.

## Underwriting Rules

| Final Score | Decision | Meaning |
|---:|---|---|
| 595 or above | Auto-approve | Low default probability |
| 575 to 594 | Manual review / refer | Moderate risk; requires underwriter review |
| Below 575 | Decline | High credit risk |

These thresholds are applied after adding the base score and feature-level scorecard points.

## Scorecard Methodology

The scorecard uses the following approach:

1. Binning: Numeric predictors are divided into five quantile-based bins.
2. WoE calculation: For each bin, Weight of Evidence is calculated as the natural log of the good distribution divided by the bad distribution.
3. Logistic regression: WoE-transformed features are used to estimate default probability.
4. Score scaling: Model coefficients and WoE values are converted into points using a 20-PDO scaling system.
5. Decisioning: The final score is compared with business risk cut-offs.

The base score used in the application is 579, and the final score is calculated as:

Final Score = Base Score + Total Attribute Points

The application currently uses three scorecard attributes: interest rate, credit score, and loan-to-income ratio.

## Example Applicant Input

| Field | Example Value |
|---|---:|
| Credit score | 720 |
| Annual income | Rs. 12,00,000 |
| Requested loan amount | Rs. 6,00,000 |
| Interest rate | 10.5% |
| Loan-to-income ratio | 0.50 |

The dashboard calculates the loan-to-income ratio as:

Loan-to-Income Ratio = Loan Amount / Annual Income

For the example above, the ratio is 0.50.

## Important Notes

- The dataset is synthetic and intended for learning, demonstration, and portfolio purposes.
- The model should not be used for real lending decisions without proper validation, fairness testing, regulatory review, and production monitoring.
- The current implementation uses only three selected features; future improvements could include employment type, loan purpose, marital status, age, and monthly debt burden.
- Add a requirements.txt file if you plan to deploy this project or share it on GitHub.

## Possible Improvements

- Add automated unit tests for binning and scoring logic.
- Include model calibration and confusion-matrix reporting.
- Add fairness and bias checks across gender, city, and employment type.
- Create a Power BI dashboard for portfolio-level default analysis.
- Deploy the Streamlit app using Streamlit Community Cloud, Render, or Docker.
- Replace synthetic data with anonymized, licensed real-world lending data for advanced practice.

## License

This project is intended for educational and portfolio use.
