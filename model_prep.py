import numpy as np
import pandas as pd
from typing import cast
from db import engine

print("Extracting modeling dataset from MySQL view...")

# Extract clean analytical modeling view isolating application-time features[cite: 5]
query = "SELECT * FROM v_credit_risk_modeling"
df = cast(pd.DataFrame, pd.read_sql_query(query, con=engine))
print(f"Dataset successfully loaded. Shape: {df.shape}")

target_col = "Default_Flag"
candidate_features = [
	"Age",
	"Gender",
	"Annual_Income",
	"Employment_Type",
	"Marital_Status",
	"Credit_Score",
	"Loan_Amount",
	"Interest_Rate",
	"Loan_Term_Months",
	"Loan_Purpose",
	"Loan_to_Income_Ratio",
	"Est_Monthly_Debt_Burden"
]


def calculate_woe_iv(data, feature, target, num_bins=5):
	df_temp = data[[feature, target]].copy()
	
	# Handle continuous numeric features via quantile binning vs categorical features via string casting[cite: 5]
	if pd.api.types.is_numeric_dtype(df_temp[feature]) and df_temp[feature].nunique() > num_bins:
		df_temp["bin"] = pd.qcut(df_temp[feature], q=num_bins, duplicates="drop").astype(str)
	else:
		df_temp["bin"] = df_temp[feature].astype(str)
	
	# Aggregate total counts and bads (defaults) per bin[cite: 5]
	agg = df_temp.groupby("bin")[target].agg(Total="count", Bads="sum").reset_index()
	agg["Goods"] = agg["Total"] - agg["Bads"]
	
	total_goods = agg["Goods"].sum()
	total_bads = agg["Bads"].sum()
	
	# Laplace smoothing to prevent division by zero / log(0)
	agg["Dist_Good"] = (agg["Goods"] + 0.5) / (total_goods + 0.5)
	agg["Dist_Bad"] = (agg["Bads"] + 0.5) / (total_bads + 0.5)
	
	# Calculate WoE and bin-level Information Value contribution[cite: 5]
	agg["WoE"] = np.log(agg["Dist_Good"] / agg["Dist_Bad"])
	agg["IV_bin"] = (agg["Dist_Good"] - agg["Dist_Bad"]) * agg["WoE"]
	
	return agg["IV_bin"].sum(), agg

# Loop through all candidate features to compute respective Information Values[cite: 5]
iv_results = []
for feat in candidate_features:
	iv_value, _ = calculate_woe_iv(df, feat, target_col)
	iv_results.append({
		"Feature": feat,
		"Information_Value": round(iv_value, 4)
	})

iv_df = pd.DataFrame(iv_results).sort_values(by="Information_Value", ascending=False).reset_index(drop=True)


def iv_interpretation(iv):
	if iv < 0.02:
		return "Not Predictive (<0.02)"
	elif iv < 0.10:
		return "Weak (0.02 - 0.10)"
	elif iv < 0.30:
		return "Medium (0.10 - 0.30)"
	elif iv < 0.50:
		return "Strong (0.30 - 0.50)"
	else:
		return "Suspicious (>0.50)"

# Build summary dataframe sorted descending by predictive power (IV)[cite: 5]
iv_df["Predictive_Power"] = iv_df["Information_Value"].apply(iv_interpretation)

print("\n=== Feature Information Value (IV) Ranking ===")
print(iv_df.to_string(index=False))