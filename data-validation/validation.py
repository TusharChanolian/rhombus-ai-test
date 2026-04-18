import pandas as pd
import numpy as np
import sys
import re

INPUT_FILE = "Messy_Employee_dataset.csv"
OUTPUT_FILE = "cleaned_employee_dataset.csv"


passed = 0
failed = 0

def check(name, condition, detail=""):
    global passed, failed
    if condition:
        print(f" PASS  {name}")
        passed += 1
    else:
        print(f" FAIL  {name}")
        if detail:
            print(f"          → {detail}")
        failed += 1

def section(title):
    print(f"\n{'─' * 60}")
    print(f"  {title}")
    print(f"{'─' * 60}")

def is_valid_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, str(email)))

print("\n🔍  Rhombus AI – Data Validation Report")
print("=" * 60)

try:
    original = pd.read_csv(INPUT_FILE)
    print(f"  Loaded input  : {INPUT_FILE}  ({len(original)} rows)")
except FileNotFoundError:
    print(f"  ERROR: Could not find {INPUT_FILE}")
    sys.exit(1)

try:
    cleaned = pd.read_csv(OUTPUT_FILE)
    print(f"  Loaded output : {OUTPUT_FILE}  ({len(cleaned)} rows)")
except FileNotFoundError:
    print(f"  ERROR: Could not find {OUTPUT_FILE}")
    sys.exit(1)

# CHECK 1 – Schema

section("1 · Output Schema")

expected_columns = [
    'employee_id', 'first_name', 'last_name', 'age',
    'department_region', 'status', 'join_date', 'salary',
    'email', 'phone', 'performance_score', 'remote_work'
]

actual_columns = list(cleaned.columns)

check(
    "All expected columns present",
    all(col in actual_columns for col in expected_columns),
    detail=f"Missing: {[c for c in expected_columns if c not in actual_columns]}"
)

check(
    "Column names are lowercase snake_case",
    all(col == col.lower() for col in actual_columns),
    detail=f"Non-lowercase cols: {[c for c in actual_columns if c != c.lower()]}"
)

check(
    "No unexpected extra columns",
    set(actual_columns) == set(expected_columns),
    detail=f"Extra: {set(actual_columns) - set(expected_columns)}"
)


# CHECK 2 – Row Count

section("2 · Row Count")

check(
    "Row count matches original (no rows dropped or added)",
    len(cleaned) == len(original),
    detail=f"Original: {len(original)}, Cleaned: {len(cleaned)}"
)


# CHECK 3 – No Missing Values

section("3 · Missing Values")

for col in expected_columns:
    if col in cleaned.columns:
        null_count = cleaned[col].isnull().sum()
        check(
            f"No nulls in '{col}'",
            null_count == 0,
            detail=f"{null_count} nulls found"
        )


# CHECK 4 – Age Validation

section("4 · Age Column")

original_missing_ages = int(original['Age'].isna().sum())

check(
    f"Missing ages were imputed ({original_missing_ages} were missing)",
    cleaned['age'].isna().sum() == 0,
    detail="Some ages still missing after cleaning"
)

check(
    "All ages are realistic (18–100)",
    cleaned['age'].between(18, 100).all(),
    detail=f"Out-of-range ages: {cleaned[~cleaned['age'].between(18, 100)]['age'].tolist()}"
)

check(
    "Age column contains whole numbers",
    cleaned['age'].apply(lambda x: float(x).is_integer()).all(),
    detail="Some ages have decimals"
)


# CHECK 5 – Salary Validation

section("5 · Salary Column")

original_missing_salaries = int(original['Salary'].isna().sum())

check(
    f"Missing salaries were imputed ({original_missing_salaries} were missing)",
    cleaned['salary'].isna().sum() == 0,
    detail="Some salaries still missing"
)

check(
    "All salaries are positive",
    (cleaned['salary'] > 0).all(),
    detail=f"Non-positive salaries found: {cleaned[cleaned['salary'] <= 0]['salary'].tolist()}"
)

check(
    "Salary rounded to 2 decimal places",
    cleaned['salary'].apply(lambda x: round(x, 2) == x).all(),
    detail="Some salary values have more than 2 decimal places"
)


# CHECK 6 – Email Validation

section("6 · Email Column")

invalid_emails = cleaned[~cleaned['email'].apply(is_valid_email)]

check(
    "All emails are valid format",
    len(invalid_emails) == 0,
    detail=f"{len(invalid_emails)} invalid emails found"
)

check(
    "All emails are lowercase",
    cleaned['email'].apply(lambda x: x == x.lower()).all(),
    detail="Some emails have uppercase characters"
)


# CHECK 7 – Phone Validation

section("7 · Phone Column")

original_negative_phones = int((original['Phone'] < 0).sum())

check(
    f"Negative phone numbers fixed ({original_negative_phones} were negative)",
    (cleaned['phone'] >= 0).all(),
    detail="Some phones are still negative"
)


# CHECK 8 – Date Validation

section("8 · Join Date Column")

def is_valid_date_format(val):
    try:
        pd.to_datetime(val, format='%Y-%m-%d')
        return True
    except:
        return False

check(
    "All dates in YYYY-MM-DD format",
    cleaned['join_date'].apply(is_valid_date_format).all(),
    detail="Some dates are not in YYYY-MM-DD format"
)

check(
    "No future join dates",
    (pd.to_datetime(cleaned['join_date']) <= pd.Timestamp.now()).all(),
    detail="Some join dates are in the future"
)


# CHECK 9 – Status & Performance Score

section("9 · Categorical Columns")

valid_statuses = ['Active', 'Inactive', 'On Leave']
valid_scores   = ['Excellent', 'Good', 'Average', 'Poor']

check(
    "Status values are valid",
    cleaned['status'].isin(valid_statuses).all(),
    detail=f"Invalid statuses: {cleaned[~cleaned['status'].isin(valid_statuses)]['status'].unique().tolist()}"
)

check(
    "Performance scores are valid",
    cleaned['performance_score'].isin(valid_scores).all(),
    detail=f"Invalid scores: {cleaned[~cleaned['performance_score'].isin(valid_scores)]['performance_score'].unique().tolist()}"
)


# CHECK 10 – No Duplicates

section("10 · Duplicates")

check(
    "No duplicate employee_id values",
    cleaned['employee_id'].duplicated().sum() == 0,
    detail=f"{cleaned['employee_id'].duplicated().sum()} duplicates found"
)

check(
    "No duplicate name values (first_name + last_name)",
    cleaned.duplicated(subset=['first_name', 'last_name']).sum() == 0,
    detail=f"{cleaned.duplicated(subset=['first_name', 'last_name']).sum()} duplicates found"
)

check(
    "No duplicate email values",
    cleaned['email'].duplicated().sum() == 0,
    detail=f"{cleaned['email'].duplicated().sum()} duplicates found"
)


# SUMMARY

total = passed + failed
print(f"  RESULTS:  {passed}/{total} checks passed")
if failed == 0:
    print(" All checks passed! Data transformation is valid.")
else:
    print(f" {failed} check(s) failed. Review the details above.")
print(f"{'═' * 60}\n")

sys.exit(0 if failed == 0 else 1)