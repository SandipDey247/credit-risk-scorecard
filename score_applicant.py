import pandas as pd

# 1. Load the Trained Production Scorecard Matrix
scorecard_df = pd.read_csv("credit_scorecard_matrix.csv")
BASE_SCORE = 579


def parse_bins(scorecard):
	"""Parses interval strings back into numeric bounds."""
	parsed = []
	for _, row in scorecard.iterrows():
		bin_str = row["Attribute_Bin"].strip("()[]")
		left_str, right_str = bin_str.split(",")
		parsed.append({
			"Feature": row["Feature"],
			"Left": float(left_str.strip()),
			"Right": float(right_str.strip()),
			"Score_Points": row["Score_Points"]
		})
	return pd.DataFrame(parsed)


parsed_scorecard = parse_bins(scorecard_df)


def calculate_applicant_score(applicant_data: dict) -> dict:
	"""
	Computes points for an applicant across all score bands.
	"""
	total_score = BASE_SCORE
	breakdown = {}
	
	for feature, val in applicant_data.items():
		feature_rules = parsed_scorecard[parsed_scorecard["Feature"] == feature]
		points_assigned = 0
		
		for _, rule in feature_rules.iterrows():
			if rule["Left"] < val <= rule["Right"]:
				points_assigned = rule["Score_Points"]
				break
		else:
			# Boundary fallbacks
			if val <= feature_rules.iloc[0]["Left"]:
				points_assigned = feature_rules.iloc[0]["Score_Points"]
			else:
				points_assigned = feature_rules.iloc[-1]["Score_Points"]
		
		total_score += points_assigned
		breakdown[feature] = points_assigned
	
	# Credit Underwriting Decision Cut-offs
	if total_score >= 595:
		decision = "AUTO-APPROVE (Low Risk)"
	elif total_score >= 575:
		decision = "MANUAL REVIEW / REFER (Medium Risk)"
	else:
		decision = "DECLINE (High Risk)"
	
	return {
		"Base_Score": BASE_SCORE,
		"Points_Breakdown": breakdown,
		"Final_Credit_Score": total_score,
		"Underwriting_Decision": decision
	}


# 2. Test Real-World Applicant Scenarios
applicant_A = {
	"Interest_Rate": 8.25,  # Low rate
	"Credit_Score": 790,  # Super-prime
	"Loan_to_Income_Ratio": 0.28  # Low debt burden
}

applicant_B = {
	"Interest_Rate": 19.50,  # High subprime rate
	"Credit_Score": 380,  # Subprime
	"Loan_to_Income_Ratio": 1.45  # High leverage
}

print("=== Applicant A (Prime Profile) ===")
result_a = calculate_applicant_score(applicant_A)
for k, v in result_a.items():
	print(f"{k}: {v}")

print("\n=== Applicant B (Subprime Profile) ===")
result_b = calculate_applicant_score(applicant_B)
for k, v in result_b.items():
	print(f"{k}: {v}")