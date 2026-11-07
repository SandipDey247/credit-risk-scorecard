import streamlit as st
import pandas as pd

# Page Configuration
st.set_page_config(
	page_title="Credit Risk Underwriting Engine",
	page_icon="💳",
	layout="wide"
)

BASE_SCORE = 579


@st.cache_data
def load_scorecard():
	"""Loads and parses the production scorecard matrix."""
	df = pd.read_csv("credit_scorecard_matrix.csv")
	parsed = []
	for _, row in df.iterrows():
		bin_str = row["Attribute_Bin"].strip("()[]")
		left_str, right_str = bin_str.split(",")
		parsed.append({
			"Feature": row["Feature"],
			"Bin_Range": row["Attribute_Bin"],
			"Left": float(left_str.strip()),
			"Right": float(right_str.strip()),
			"WoE": row["WoE"],
			"Score_Points": row["Score_Points"]
		})
	return pd.DataFrame(parsed)


parsed_scorecard = load_scorecard()


def get_feature_points(feature_name: str, val: float):
	feature_rules = parsed_scorecard[parsed_scorecard["Feature"] == feature_name]
	
	for _, rule in feature_rules.iterrows():
		if rule["Left"] < val <= rule["Right"]:
			return rule["Score_Points"], rule["Bin_Range"], rule["WoE"]
	
	# Fallback bounds
	if val <= feature_rules.iloc[0]["Left"]:
		return feature_rules.iloc[0]["Score_Points"], feature_rules.iloc[0]["Bin_Range"], feature_rules.iloc[0]["WoE"]
	return feature_rules.iloc[-1]["Score_Points"], feature_rules.iloc[-1]["Bin_Range"], feature_rules.iloc[-1]["WoE"]


# Header
st.title("💳 Retail Credit Risk Scorecard Engine")
st.markdown(
	"Automated applicant scoring and risk triage based on **Basel II/III WoE & Logistic Regression** calibration.")

st.divider()

# Layout: Inputs on the Left, Decisions & Breakdown on the Right
col_input, col_result = st.columns([1, 1.2], gap="large")

with col_input:
	st.subheader("📋 Applicant Information")
	
	credit_score = st.slider(
		"Credit Score (CIBIL / Experian)",
		min_value=300,
		max_value=850,
		value=720,
		step=1
	)
	
	annual_income = st.number_input(
		"Annual Gross Income (₹)",
		min_value=100000,
		max_value=10000000,
		value=1200000,
		step=50000
	)
	
	loan_amount = st.number_input(
		"Requested Loan Amount (₹)",
		min_value=10000,
		max_value=15000000,
		value=600000,
		step=25000
	)
	
	interest_rate = st.slider(
		"Offered Interest Rate (% p.a.)",
		min_value=6.0,
		max_value=25.0,
		value=10.5,
		step=0.05
	)
	
	# Derived Feature
	loan_to_income = round(loan_amount / annual_income, 4)
	st.info(f"**Calculated Loan-to-Income (LTI) Ratio:** `{loan_to_income:.4f}`")

# Calculations
rate_pts, rate_bin, rate_woe = get_feature_points("Interest_Rate", interest_rate)
score_pts, score_bin, score_woe = get_feature_points("Credit_Score", credit_score)
lti_pts, lti_bin, lti_woe = get_feature_points("Loan_to_Income_Ratio", loan_to_income)

total_variable_points = rate_pts + score_pts + lti_pts
final_score = BASE_SCORE + total_variable_points

# Underwriting Policy Thresholds
if final_score >= 595:
	decision = "AUTO-APPROVE"
	decision_color = "success"
	desc = "Low default probability. Profile clears prime automated underwriting thresholds."
elif final_score >= 575:
	decision = "MANUAL REVIEW / REFER"
	decision_color = "warning"
	desc = "Moderate risk exposure. Route to senior credit underwriter for collateral or guarantor verification."
else:
	decision = "DECLINE"
	decision_color = "error"
	desc = "High credit risk. Profile exceeds portfolio tolerance cut-offs."

with col_result:
	st.subheader("🎯 Underwriting Decision")
	
	m_col1, m_col2, m_col3 = st.columns(3)
	m_col1.metric("Base Baseline", f"{BASE_SCORE}")
	m_col2.metric("Net Attribute Points", f"{total_variable_points:+d}")
	m_col3.metric("Final Credit Score", f"{final_score}", delta=f"{total_variable_points} pts")
	
	if decision_color == "success":
		st.success(f"### Verdict: {decision}\n{desc}")
	elif decision_color == "warning":
		st.warning(f"### Verdict: {decision}\n{desc}")
	else:
		st.error(f"### Verdict: {decision}\n{desc}")
	
	st.subheader("📊 Point Allocation Breakdown")
	breakdown_df = pd.DataFrame([
		{
			"Risk Attribute": "Interest Rate",
			"Applicant Value": f"{interest_rate:.2f}%",
			"Matched Bin": rate_bin,
			"WoE": round(rate_woe, 4),
			"Points": rate_pts
		},
		{
			"Risk Attribute": "Credit Score",
			"Applicant Value": f"{credit_score}",
			"Matched Bin": score_bin,
			"WoE": round(score_woe, 4),
			"Points": score_pts
		},
		{
			"Risk Attribute": "Loan-to-Income",
			"Applicant Value": f"{loan_to_income:.4f}",
			"Matched Bin": lti_bin,
			"WoE": round(lti_woe, 4),
			"Points": lti_pts
		}
	])
	
	st.dataframe(breakdown_df, hide_index=True, use_container_width=True)
	
	# Bar chart for visual score contribution
	chart_data = pd.DataFrame({
		"Feature": ["Interest Rate", "Credit Score", "Loan-to-Income"],
		"Points": [rate_pts, score_pts, lti_pts]
	}).set_index("Feature")
	
	st.bar_chart(chart_data)

st.divider()
st.caption(
	"Credit Risk Modeling Engine • Trained on 30,000 synthetic loans • 20 PDO Scaling • MySQL + Scikit-Learn Pipeline")