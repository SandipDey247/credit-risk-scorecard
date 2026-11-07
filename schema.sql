-- ====================================================================
-- Retail Credit Risk Database Schema & Analytical Modeling Pipeline
-- Database: MySQL 8.0+
-- Project: Credit Risk Scorecard & Underwriting Engine
-- ====================================================================

-- 1. Database Initialization
CREATE DATABASE IF NOT EXISTS credit_risk_db;
USE credit_risk_db;

-- Drop dependent tables first to respect foreign key constraints
DROP VIEW IF EXISTS v_credit_risk_modeling;
DROP TABLE IF EXISTS repayment_history;
DROP TABLE IF EXISTS loans;
DROP TABLE IF EXISTS borrowers;

-- ====================================================================
-- 2. Relational Table Definitions
-- ====================================================================

-- Dimension Table: Borrower Demographics and Financial Profile
CREATE TABLE borrowers (
    Borrower_ID INT PRIMARY KEY,
    Borrower_Name VARCHAR(100) NOT NULL,
    Age INT NOT NULL,
    Gender VARCHAR(20) NOT NULL,
    Annual_Income DECIMAL(12, 2) NOT NULL,
    Employment_Type VARCHAR(50) NOT NULL,
    Credit_Score INT NOT NULL,
    City VARCHAR(50) NOT NULL,
    Marital_Status VARCHAR(30) NOT NULL,
    INDEX idx_credit_score (Credit_Score),
    INDEX idx_income (Annual_Income)
);

-- Fact Table: Loan Origination Details & Risk-Based Pricing
CREATE TABLE loans (
    Loan_ID INT PRIMARY KEY,
    Borrower_ID INT NOT NULL,
    Loan_Amount DECIMAL(10, 2) NOT NULL,
    Interest_Rate DECIMAL(5, 2) NOT NULL,
    Loan_Term_Months INT NOT NULL,
    Loan_Purpose VARCHAR(50) NOT NULL,
    Issue_Date DATE NOT NULL,
    CONSTRAINT fk_loans_borrower 
        FOREIGN KEY (Borrower_ID) REFERENCES borrowers(Borrower_ID) 
        ON DELETE CASCADE,
    INDEX idx_borrower (Borrower_ID),
    INDEX idx_issue_date (Issue_Date)
);

-- Performance & Target Table: Repayment Behavior & Default Tracking
CREATE TABLE repayment_history (
    Repayment_ID INT PRIMARY KEY,
    Loan_ID INT NOT NULL,
    Months_On_Book INT NOT NULL,
    Max_Days_Past_Due INT NOT NULL,     -- 0: On-time; >90: Basel Default / Charge-off
    Default_Flag TINYINT NOT NULL,       -- 1 = Defaulted, 0 = Non-Default
    Total_Principal_Paid DECIMAL(10, 2) NOT NULL,
    Total_Interest_Paid DECIMAL(10, 2) NOT NULL,
    CONSTRAINT fk_repayment_loan 
        FOREIGN KEY (Loan_ID) REFERENCES loans(Loan_ID) 
        ON DELETE CASCADE,
    INDEX idx_default_flag (Default_Flag),
    INDEX idx_loan_id (Loan_ID)
);

-- ====================================================================
-- 3. Feature Extraction View (Analytical Modeling Layer)
-- ====================================================================

CREATE OR REPLACE VIEW v_credit_risk_modeling AS
SELECT 
    b.Borrower_ID,
    l.Loan_ID,
    
    -- Demographics
    b.Age,
    b.Gender,
    b.Annual_Income,
    b.Employment_Type,
    b.Marital_Status,
    b.City,
    
    -- Credit Profile & Pricing
    b.Credit_Score,
    l.Loan_Amount,
    l.Interest_Rate,
    l.Loan_Term_Months,
    l.Loan_Purpose,
    l.Issue_Date,
    
    -- Financial Leverage & Debt Burden Ratios
    ROUND(l.Loan_Amount / b.Annual_Income, 4) AS Loan_to_Income_Ratio,
    ROUND((l.Loan_Amount / l.Loan_Term_Months) / (b.Annual_Income / 12), 4) AS Est_Monthly_Debt_Burden,
    
    -- Post-Disbursal Performance Metrics
    r.Months_On_Book,
    r.Max_Days_Past_Due,
    r.Total_Principal_Paid,
    r.Total_Interest_Paid,
    ROUND(r.Total_Principal_Paid / l.Loan_Amount, 4) AS Principal_Paid_Ratio,
    
    -- Target Variable
    r.Default_Flag
FROM borrowers b
JOIN loans l ON b.Borrower_ID = l.Borrower_ID
JOIN repayment_history r ON l.Loan_ID = r.Loan_ID;

-- ====================================================================
-- 4. Analytical & Verification Queries
-- ====================================================================

-- Portfolio Risk Tier Distribution
-- SELECT 
--     CASE 
--         WHEN b.Credit_Score >= 750 THEN '1. Super Prime (750-850)'
--         WHEN b.Credit_Score >= 670 THEN '2. Prime (670-749)'
--         WHEN b.Credit_Score >= 580 THEN '3. Near Prime (580-669)'
--         ELSE '4. Subprime (<580)'
--     END AS credit_tier,
--     COUNT(l.Loan_ID) AS total_loans,
--     ROUND(AVG(l.Loan_Amount), 2) AS avg_loan_amount,
--     ROUND(AVG(l.Interest_Rate), 2) AS avg_interest_rate,
--     SUM(r.Default_Flag) AS total_defaults,
--     ROUND((SUM(r.Default_Flag) / COUNT(l.Loan_ID)) * 100, 2) AS default_rate_pct
-- FROM borrowers b
-- JOIN loans l ON b.Borrower_ID = l.Borrower_ID
-- JOIN repayment_history r ON l.Loan_ID = r.Loan_ID
-- GROUP BY credit_tier
-- ORDER BY credit_tier ASC;

-- Quick Row Count Check
-- SELECT 'borrowers' AS table_name, COUNT(*) AS row_count FROM borrowers
-- UNION ALL
-- SELECT 'loans', COUNT(*) FROM loans
-- UNION ALL
-- SELECT 'repayment_history', COUNT(*) FROM repayment_history;