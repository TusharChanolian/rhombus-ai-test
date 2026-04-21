# Rhombus AI – Take-Home Exercise
**Role:** Software Engineer in Test Intern  
**Candidate:** Tushar Chanolian  
**System Under Test:** [Rhombus AI](https://rhombusai.com)

---

## Overview

This repository contains automated tests for the Rhombus AI web application, covering three areas:

- **Part 1** – UI Automation (Playwright)
- **Part 2** – API / Network-Level Tests (Python + Requests)
- **Part 3** – Data Validation (Python)

### Dataset
The test dataset used is the [Messy Employee Dataset](https://www.kaggle.com/datasets/desolution01/messy-employee-dataset) from Kaggle — a deliberately messy CSV with missing values, negative phone numbers, inconsistent date formats, and invalid emails. It was uploaded to Rhombus AI, processed through an AI-generated pipeline, and the cleaned output was downloaded for validation.

---

## Repository Structure

```
rhombus-ai-test/
├── ui-tests/
│   └── pipeline.spec.js       # Playwright UI automation test
├── api-tests/
│   └── api_tests.py           # Python API tests
├── data-validation/
│   ├── Messy_Employee_dataset.csv      # Original input
│   ├── cleaned_employee_dataset.csv    # Cleaned output from Rhombus AI
│   └── validate.py            # Data validation script
├── playwright.config.js
├── package.json
├── package-lock.json
├── .gitignore
├── .env.example
└── README.md
```

---

## Setup

### Prerequisites
- Python 3.x
- Node.js 18+
- pip
- npm

### 1. Clone the repository
```bash
git clone https://github.com/TusharChanolian/rhombus-ai-test.git
cd rhombus-ai-test
```

### 2. Install Node dependencies
```bash
npm install
npx playwright install chromium
```

### 3. Install Python dependencies
```bash
pip install requests python-dotenv pandas numpy
```

### 4. Set up environment variables
Create a `.env` file in the project root:
```
RHOMBUS_EMAIL=your_email@example.com
RHOMBUS_PASSWORD=your_password
RHOMBUS_TOKEN=your_jwt_token
```

**How to get your JWT token:**
1. Log in to rhombusai.com in your browser
2. Open DevTools (F12) → Network tab
3. Click any request to `api.rhombusai.com`
4. Copy the `Authorization: Bearer ...` token from the request headers
5. Paste it as `RHOMBUS_TOKEN` in your `.env` file

> Note: The token expires after 30 days. Generate a new one if tests fail with 401.

---

## Running the Tests

### Part 1 – UI Automation (Playwright)

```bash
npx playwright test ui-tests/pipeline.spec.js
```

**What it tests:**
- Full end-to-end AI pipeline flow
- Login with email and password
- Handles the 3-step tutorial popup on first login
- Uploads the messy CSV file
- Submits a prompt to the AI
- Waits for the pipeline to auto-run and complete
- Clicks the output node and opens the Preview tab
- Downloads the result as CSV
- Asserts the downloaded file is a valid CSV

**Notes:**
- Runs in headed mode (browser is visible) by default
- The pipeline can take 1-3 minutes to run — the test waits automatically
- The tutorial popup only appears on first login — the test handles both cases

---

### Part 2 – API Tests (Python)

```bash
python api-tests/api_tests.py
```

**What it tests:**

| Test | Type | Endpoint |
|------|------|----------|
| Upload valid CSV | Positive | `POST /api/dataset/datasets/temp/upload` |
| Upload txt file (invalid format) | Negative | `POST /api/dataset/datasets/temp/upload` |
| Download pipeline output | Positive | `GET /api/dataset/analyzer/v2/projects/{id}/nodes/output-download` |

**Coverage:**
- ✅ Dataset upload
- ✅ Download endpoints
- ✅ Error handling for invalid input (negative test)

**Key findings:**
- **Key findings:**
- The upload endpoint accepts text-based files but correctly identifies them via `content_type` — a txt file returns `text/plain` instead of `text/csv`, which our negative test asserts on
- When tested with a JPEG image (using real magic bytes `\xff\xd8\xff\xe0`), the server correctly returns 500 with an explicit error: `"Unsupported content type: image/jpeg"` — confirming binary file validation is enforced at the upload stage
- File type validation happens at the upload stage for binary formats (images) but not for text-based formats (txt) — an interesting architectural observation

---

### Part 3 – Data Validation (Python)

```bash
cd data-validation
python validate.py
```

**What it tests (30 checks across 10 categories):**

| Category | Checks |
|----------|--------|
| Output Schema | Column names, lowercase snake_case, no extra columns |
| Row Count | No rows dropped or added (1020 → 1020) |
| Missing Values | Zero nulls in all 12 columns |
| Age Column | Imputed 211 missing values, realistic range 18-100, whole numbers |
| Salary Column | Imputed 24 missing values, all positive, 2 decimal places |
| Email Column | Valid format, all lowercase |
| Phone Column | All negative numbers fixed (1020 were negative) |
| Join Date | YYYY-MM-DD format, no future dates |
| Categorical Columns | Valid Status and Performance Score values only |
| Duplicates | No duplicate Employee IDs |

**Note:** During analysis, approximately 956 records were found with identical names, emails and departments — likely synthetic duplicates from the source Kaggle dataset. These were noted as a recommendation for improvement but do not affect the validation results since the pipeline correctly deduplicated based on `employee_id`.

**Note on prompt used:** A simple natural language prompt was used to create the pipeline: *"Analyse this file and clean and transform it."* The validation script is intentionally prompt-agnostic — it validates output quality regardless of how the pipeline was constructed. For more deterministic results, a specific prompt like *"standardise column names to lowercase, fill missing Age with median, fix negative Phone numbers, standardise Join_Date to YYYY-MM-DD"* is recommended in production.

---

## Demo Video

🎥 [Link to demo video](#) ← *to be added*

---

## Design Decisions & Trade-offs

### UI Testing
- Used Playwright's built-in auto-waiting instead of fixed sleeps throughout
- The send button selector uses `nth(4)` due to no accessible `aria-label` on the icon button — this is noted as a known fragility
- The pipeline auto-runs after creation so no manual "Run Pipeline" click is needed
- Session is handled via email/password login stored in `.env` to avoid Google OAuth restrictions in automated browsers

### API Testing
- Used Python `requests` library rather than Playwright's API testing due to NextAuth.js login restrictions in headless environments
- JWT token is stored in `.env` and obtained manually from browser DevTools — this is documented clearly for reviewers
- All endpoints were identified through HAR file capture during manual UI testing (black-box approach)
- Negative test uses JPEG magic bytes (`\xff\xd8\xff\xe0`) for a realistic file simulation

### Data Validation
- Script validates what the pipeline actually promised to do, not what could theoretically be done
- All 30 checks pass against the actual pipeline output
- Tolerance for non-deterministic behaviour: age imputation uses median (deterministic), salary imputation uses median (deterministic)