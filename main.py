"""
================================================================================
Project: Synthetic Data Generation & MySQL Bulk Loader
Description:
    This script generates realistic synthetic retail banking data for 30,000
    borrowers, loan originations, and repayment performance histories.
    It handles:
    1. Borrower demographic & financial profile generation.
    2. Risk-based loan pricing & customized loan term mapping by purpose.
    3. Default probability modeling based on credit score risk and leverage (LTI).
    4. Local CSV export and bulk insertion into the MySQL database via SQLAlchemy.
================================================================================
"""

import numpy as np
import pandas as pd
from db import engine

# Initialize random number generator with a fixed seed for reproducibility
rng = np.random.default_rng(seed=42)
n_samples = 30000

# ============================================================================
# 1. GENERATE SYNTHETIC BORROWERS DATA
# ============================================================================
print("=== Generating Borrower Profiles ===")

borrowers_df = pd.DataFrame({
	"Borrower_ID": np.arange(10001, 10001 + n_samples),
	
	"First_Name": rng.choice(
		["Aarav", "Arjun", "Aditya", "Amit", "Anil", "Akash", "Bhavin", "Bharat", "Chirag", "Deepak", "Dev", "Dhruv",
		 "Gaurav", "Hari", "Ishaan", "Jatin", "Kabir", "Karan", "Kunal", "Manish", "Nikhil", "Nitin", "Pankaj",
		 "Pranav", "Rahul", "Rohan", "Rohit", "Sachin", "Sanjay", "Siddharth", "Sumit", "Tarun", "Utkarsh", "Varun",
		 "Vijay", "Yash", "Aanya", "Ananya", "Aishwarya", "Bhavna", "Deepika", "Divya", "Esha", "Gauri", "Isha",
		 "Kavita", "Kiran", "Kriti", "Meera", "Neha", "Nisha", "Pooja", "Priya", "Riya", "Ridhi", "Sakshi", "Sneha",
		 "Swati", "Tanvi", "Vani"], n_samples
	),
	
	"Last_Name": rng.choice(
		["Sharma", "Verma", "Gupta", "Singh", "Kumar", "Joshi", "Patel", "Mehta", "Shah", "Reddy", "Nair", "Iyer",
		 "Iyengar", "Rao", "Choudhury", "Das", "Banerjee", "Chatterjee", "Mukherjee", "Sen", "Bose", "Mishra", "Pandey",
		 "Tiwari", "Dubey", "Yadav", "Prasad", "Naik", "Shetty", "Rai", "Kapoor", "Khan", "Malhotra", "Aggarwal",
		 "Bansal", "Garg", "Chawla", "Kaur", "Dhillon", "Gill", "Sandhu", "Grewal", "Sidhu", "Mani", "Pillai", "Menon",
		 "Kulkarni", "Deshmukh", "Gaikwad", "Shinde", "Patil", "Pawar", "Bhat", "Rathore", "Chauhan", "Solanki",
		 "Jadeja", "Grover", "Saxena", "Sinha"], size=n_samples
	),
	
	"Age": rng.integers(21, 66, size=n_samples),
	
	"Gender": rng.choice(
		["Male", "Female"], size=n_samples, p=[0.60, 0.40]
	),
	
	"Annual_Income": rng.integers(200000, 2000001, size=n_samples),
	
	"Employment_Type": rng.choice(
		["Salaried", "Self-Employed", "Business", "Other"],
		size=n_samples, p=[0.55, 0.20, 0.20, 0.05]
	),
	
	"Credit_Score": rng.integers(300, 851, size=n_samples),
	
	"City": rng.choice(
		["Mumbai", "Delhi", "Bengaluru", "Hyderabad", "Ahmedabad", "Chennai", "Kolkata", "Surat", "Pune", "Jaipur",
		 "Lucknow", "Kanpur", "Nagpur", "Indore", "Thane", "Bhopal", "Visakhapatnam", "Pimpri-Chinchwad", "Patna",
		 "Vadodara", "Ghaziabad", "Ludhiana", "Coimbatore", "Agra", "Madurai", "Nashik", "Vijayawada", "Faridabad",
		 "Meerut", "Rajkot", "Kalyan-Dombivli", "Vasai-Virar", "Varanasi", "Srinagar", "Aurangabad", "Dhanbad",
		 "Amritsar", "Navi Mumbai", "Prayagraj", "Howrah", "Ranchi", "Jabalpur", "Gwalior", "Jodhpur", "Trichy", "Kota",
		 "Mysore", "Bareilly", "Tiruppur", "Guwahati", "Solapur", "Hubli-Dharwar", "Salem", "Aligarh", "Gurgaon",
		 "Moradabad", "Bhubaneswar", "Jalandhar", "Warangal", "Mira-Bhayandar", "Jalgaon", "Guntur",
		 "Thiruvananthapuram", "Bhiwandi", "Saharanpur", "Amravati", "Noida", "Bikaner", "Bhilai", "Cuttack",
		 "Firozabad", "Kochi", "Nellore", "Bhavnagar", "Dehradun", "Durgapur", "Asansol", "Rourkela", "Nanded",
		 "Kolhapur", "Ajmer", "Akola", "Gulbarga", "Jamnagar", "Ujjain", "Loni", "Jhansi", "Ulhasnagar", "Jammu",
		 "Mangalore", "Nellore", "Belgaum", "Siliguri"], size=n_samples
	),
	
	"Marital_Status": rng.choice(
		["Single", "Married", "Divorced", "Widowed"],
		size=n_samples, p=[0.35, 0.55, 0.08, 0.02]
	)
})

# Combine first and last names into a single borrower name column
borrowers_df["Borrower_Name"] = (
		borrowers_df["First_Name"] + " " + borrowers_df["Last_Name"]
)

borrowers_df.drop(
	columns=["First_Name", "Last_Name"], inplace=True
)

print(borrowers_df.head())
print(borrowers_df.shape)

borrowers_df.to_csv("borrowers.csv", index=False)

# ============================================================================
# 2. GENERATE SYNTHETIC LOANS DATA (Risk-Based Pricing & Terms)
# ============================================================================
print("\n=== Generating Loan Origination Records ===")

loan_ids = np.arange(100001, 100001 + n_samples)

# Randomly link loans to valid borrower IDs
borrower_ids = rng.choice(
	borrowers_df["Borrower_ID"],
	size=n_samples
)

loan_borrowers = (
	borrowers_df.set_index("Borrower_ID")
	.loc[borrower_ids]
)

income = loan_borrowers["Annual_Income"].to_numpy()

# Loan amounts scaled as a proportion of annual income
loan_amounts = np.round(
	income * rng.uniform(0.1, 1.5, n_samples),
	2
)

credit_scores = loan_borrowers["Credit_Score"].to_numpy()

# Risk-based interest rate pricing inversely proportional to credit score
interest_rates = np.round(6.0 + (850.0 - credit_scores) * 0.025 + rng.uniform(0, 2, size=n_samples),2)

loan_purposes = rng.choice(
	[
		"Home Purchase",
		"Home Renovation",
		"Plot Purchase",
		"Home Construction",
		"Higher Education in India",
		"Higher Education Abroad",
		"Vehicle Purchase - Car",
		"Vehicle Purchase - Two Wheeler",
		"Commercial Vehicle Purchase",
		"Medical Emergency",
		"Wedding and Marriage Expenses",
		"Debt Consolidation",
		"Travel and Vacation",
		"Business Expansion",
		"Working Capital Requirement",
		"MSME Business Loan",
		"Purchase of Machinery and Equipment",
		"Agricultural Expenses",
		"Purchase of Land for Agriculture",
		"Gold Loan for Personal Needs",
		"Loan Against Property for Business",
		"Consumer Durables Purchase",
		"Festival Expenses",
		"Skill Development Training"
	],
	size=n_samples
)


# Map loan terms (in months) appropriately based on the loan purpose category
loan_terms = []

for purpose in loan_purposes:

	if purpose in [
        "Home Purchase",
        "Home Construction",
        "Plot Purchase"
    ]:
		term = rng.choice([120, 180, 240, 300, 360])

	elif purpose in [
        "Business Expansion",
        "MSME Business Loan",
        "Loan Against Property for Business"
    ]:
		term = rng.choice([36, 60, 84, 120, 180])

	elif purpose in [
        "Higher Education in India",
        "Higher Education Abroad"
    ]:
		term = rng.choice([36, 60, 84, 120])

	else:
		term = rng.choice([12, 24, 36, 48, 60])

	loan_terms.append(term)

loan_terms = np.array(loan_terms)

# Generate uniform distribution of loan issue dates between 2022 and 2025
start_date = pd.Timestamp("2022-01-01")
end_date = pd.Timestamp("2025-12-31")

issue_dates = (
    start_date
    + pd.to_timedelta(
        rng.integers(
            0, (end_date - start_date).days + 1, n_samples
        ),
        unit="D"
    )
)

loans_df = pd.DataFrame({
    "Loan_ID": loan_ids,
    "Borrower_ID": borrower_ids,
    "Loan_Amount": loan_amounts,
    "Interest_Rate": interest_rates,
    "Loan_Term_Months": loan_terms,
    "Loan_Purpose": loan_purposes,
    "Issue_Date": issue_dates
})

print(loans_df.head())
print(loans_df.shape)

loans_df.to_csv("loans.csv", index=False)

# ============================================================================
# 3. GENERATE REPAYMENT PERFORMANCE & DEFAULT TARGET LABELS
# ============================================================================
print("\n=== Generating Repayment History & Default Target Flags ===")

repayment_ids = np.arange(1000001, 1000001 + n_samples)
months_on_book = rng.integers(6, 37, size=n_samples)

# Calculate leverage (Loan-to-Income) and credit risk metrics for default modeling
loan_to_income = loan_amounts / income
score_risk = (850.0 - credit_scores) / 550.0

# Base default probability function driven by credit score risk and leverage
base_prob = 0.02 + (0.12 * score_risk) + (0.04 * np.clip(loan_to_income, 0, 2))
default_prob = np.clip(base_prob + rng.normal(0, 0.01, size=n_samples), 0.01, 0.85)

# Binary default flag indicator (1 = Defaulted, 0 = Non-Default)
default_flags = (rng.uniform(0, 1, size=n_samples) < (default_prob * 0.35)).astype(int)

# Maximum Days Past Due (DPD): >= 90 days past due indicates regulatory default
max_dpd = np.where(
    default_flags == 1,
    rng.integers(91, 181, size=n_samples),
    rng.choice([0, 15, 30], size=n_samples, p=[0.90, 0.07, 0.03])
)

# Calculate repayment financial aggregates (principal and interest paid)
principal_ratio = np.where(default_flags == 1, rng.uniform(0.10, 0.40, size=n_samples), 1.0)
total_principal_paid = np.round(loan_amounts * principal_ratio, 2)
total_interest_paid = np.round(
    total_principal_paid * (interest_rates / 100.0) * (months_on_book / 12.0),
    2
)

repayment_df = pd.DataFrame({
    "Repayment_ID": repayment_ids,
    "Loan_ID": loan_ids,
    "Months_On_Book": months_on_book,
    "Max_Days_Past_Due": max_dpd,
    "Default_Flag": default_flags,
    "Total_Principal_Paid": total_principal_paid,
    "Total_Interest_Paid": total_interest_paid
})

print(repayment_df.head())
print(f"Repayment table shape: {repayment_df.shape}")
print(f"Portfolio Default Rate: {default_flags.mean() * 100:.2f}%")

repayment_df.to_csv("repayment_history.csv", index=False)

# ============================================================================
# 4. BULK INSERT DATA INTO MYSQL DATABASE
# ============================================================================
print("\nWriting DataFrames into MySQL...")
borrowers_df.to_sql("borrowers", con=engine, if_exists="append", index=False, chunksize=5000)
loans_df.to_sql("loans", con=engine, if_exists="append", index=False, chunksize=5000)
repayment_df.to_sql("repayment_history", con=engine, if_exists="append", index=False, chunksize=5000)
print("All 30,000 records successfully populated into MySQL!")
