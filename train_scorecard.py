import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, roc_curve
from db import engine
from typing import cast


# 1. Load Data
print("Fetching dataset for Scorecard Training...")
query = "SELECT * FROM v_credit_risk_modeling"
df = cast(pd.DataFrame, pd.read_sql_query(query, con=engine))

# 2. Selected Features Based on IV Analysis
selected_features = ["Interest_Rate", "Credit_Score", "Loan_to_Income_Ratio"]
target_col = "Default_Flag"


# 3. Binning & WoE Dictionary Generation
def create_woe_bins(data, feature, target, num_bins=5):
	df_temp = data[[feature, target]].copy()
	
	# Generate quantile bins
	df_temp["bin"], bin_edges = pd.qcut(
		df_temp[feature], q=num_bins, retbins=True, duplicates="drop"
	)
	
	agg = df_temp.groupby("bin", observed=False)[target].agg(
		Total="count", Bads="sum"
	).reset_index()
	agg["Goods"] = agg["Total"] - agg["Bads"]
	
	total_goods = agg["Goods"].sum()
	total_bads = agg["Bads"].sum()
	
	# Laplace smoothing
	dist_good = (agg["Goods"] + 0.5) / (total_goods + 0.5)
	dist_bad = (agg["Bads"] + 0.5) / (total_bads + 0.5)
	
	# WoE: ln(% Good / % Bad)
	agg["WoE"] = np.log(dist_good / dist_bad)
	
	# Save bin ranges and WoE mapping
	bin_map = []
	for idx, row in agg.iterrows():
		bin_map.append({
			"bin": row["bin"],
			"left": row["bin"].left,
			"right": row["bin"].right,
			"WoE": row["WoE"]
		})
	
	return pd.DataFrame(bin_map), bin_edges


# Build WoE maps for each feature
woe_lookup = {}
for feat in selected_features:
	woe_table, _ = create_woe_bins(df, feat, target_col)
	woe_lookup[feat] = woe_table


# Function to transform raw values to WoE
def apply_woe(val, woe_df):
	for _, row in woe_df.iterrows():
		if row["left"] < val <= row["right"]:
			return row["WoE"]
	# Fallback to nearest boundary if outside edge
	if val <= woe_df.iloc[0]["left"]:
		return woe_df.iloc[0]["WoE"]
	return woe_df.iloc[-1]["WoE"]


# 4. Transform Dataset to WoE
X_woe = pd.DataFrame()
for feat in selected_features:
	X_woe[feat + "_WoE"] = df[feat].apply(lambda x: apply_woe(x, woe_lookup[feat]))

y = df[target_col]

# 5. Train-Test Split (80/20)
X_train, X_test, y_train, y_test = train_test_split(
	X_woe, y, test_size=0.20, random_state=42, stratify=y
)

# 6. Fit Logistic Regression
model = LogisticRegression(solver="lbfgs", max_iter=1000)
model.fit(X_train, y_train)

# 7. Model Performance Metrics (AUC, Gini, KS)
y_pred_proba = model.predict_proba(X_test)[:, 1]

auc = roc_auc_score(y_test, y_pred_proba)
gini = 2 * auc - 1

# Calculate Kolmogorov-Smirnov (KS) Statistic
fpr, tpr, _ = roc_curve(y_test, y_pred_proba)
ks_stat = np.max(tpr - fpr)

print("\n=== Model Discrimination Metrics ===")
print(f"ROC-AUC:       {auc:.4f}")
print(f"Gini Index:    {gini:.4f}")
print(f"KS Statistic:  {ks_stat * 100:.2f}%")

# 8. Scorecard Scaling (Standard Retail Banking Parameters)
# Standard: 600 Score at 50:1 Good:Bad odds, 20 PDO (Points to Double the Odds)
target_score = 600
target_odds = 50.0
pdo = 20.0

factor = pdo / np.log(2)
offset = target_score - (factor * np.log(target_odds))

print(f"\nScaling Parameters: Factor = {factor:.4f}, Offset = {offset:.4f}")

# 9. Extract Production Scorecard Matrix
intercept = model.intercept_[0]
coefficients = model.coef_[0]
n_features = len(selected_features)

scorecard_rows = []

# Base points from intercept
base_points = round(offset - factor * intercept)

for i, feat in enumerate(selected_features):
	beta_i = coefficients[i]
	woe_df = woe_lookup[feat]
	
	for _, row in woe_df.iterrows():
		# Points = -(WoE * beta * Factor)
		# Note: Positive WoE means higher Good ratio, so it adds to credit score
		points = round(row["WoE"] * (-beta_i) * factor)
		scorecard_rows.append({
			"Feature": feat,
			"Attribute_Bin": str(row["bin"]),
			"WoE": round(row["WoE"], 4),
			"Score_Points": points
		})

scorecard_df = pd.DataFrame(scorecard_rows)

print("\n=== Final Credit Risk Scorecard Table ===")
print(f"Base Score Points (Baseline): {base_points}")
print(scorecard_df.to_string(index=False))

# Save scorecard matrix for reference
scorecard_df.to_csv("credit_scorecard_matrix.csv", index=False)
print("\nScorecard matrix successfully exported to 'credit_scorecard_matrix.csv'!")