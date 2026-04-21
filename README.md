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
│   └── pipeline.spec.js          # Playwright UI automation test
├── api-tests/
│   └── api_tests.py              # Python API tests
├── data-validation/
│   ├── Messy_Employee_dataset.csv       # Original messy input
│   ├── cleaned_employee_dataset.csv     # Cleaned output from Rhombus AI
│   └── validate.py               # Data validation script
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

**Important before running:**
> ⚠️ Make sure there are no existing projects in your Rhombus AI account before running. The file attachment button uses a positional selector `nth(2)` which assumes zero existing projects. Each existing project shifts the button position by one. Use a fresh account or delete all existing projects first for a reliable run.

**Notes:**
- Runs in headed mode (browser is visible) by default
- The pipeline can take 1-3 minutes to run — the test waits automatically
- The tutorial popup only appears on first login — the test handles both cases

**Why email/password instead of Google login:**
I initially signed up with Google OAuth but ran into a problem — Google actively blocks sign-in attempts from automated browsers for security reasons. On top of that, Rhombus AI doesn't let you add a password to an account that was created with Google. So I created a separate test account with email and password specifically for automation. This is actually the standard industry approach anyway. Credentials go in `.env` so they never appear in the repo.

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

**How I found the endpoints:**
Rhombus AI doesn't have public API docs so I recorded a HAR file while using the app manually and identified all the real network calls being made. This is the black-box approach the exercise described.

**Interesting findings:**
- When I uploaded a plain text file, the server accepted it but correctly returned `content_type: text/plain` instead of `text/csv` — so text-based format validation happens downstream not at upload
- When I tested with a JPEG image (using real magic bytes `\xff\xd8\xff\xe0`), the server returned 500 with an explicit error: `"Unsupported content type: image/jpeg"` — meaning binary file validation IS enforced at the upload stage
- The negative test asserts on the txt file returning a non-CSV content type, which passes correctly

**⚠️ Important note on the download test:**
The download test relies on an existing pipeline output from a previously run project. During the demo video recording, existing projects had to be deleted to run the UI automation test cleanly due to the positional selector limitation described above. This caused the download test to fail in the video as the output no longer existed — I explained this at the end of the video.

To run all 3 API tests successfully:
1. First run the UI test to create a new project and pipeline
2. Open your Rhombus AI account and note the new project ID and node name from the network calls
3. Update the `PROJECT_ID` and `NODE_NAME` variables in `api_tests.py` with those values
4. Then run the API tests

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

🎥 [[Link to demo video](https://drive.google.com/file/d/1Iz5wpen64tQK2FpLIWxHYY1SWCRauQJB/view?usp=sharing)](#) ← *to be added*

---

## Design Decisions & Trade-offs

### UI Testing
- No `waitForTimeout` blind sleeps anywhere — everything uses Playwright's built-in auto-waiting
- Pipeline completion is detected by watching the run button switch from its red destructive state back to normal, rather than waiting a fixed amount of time
- The `nth(2)` selector for the attachment button is a known limitation — it depends on having zero existing projects. Documented above
- The `nth(4)` selector for the send button is also positional due to no accessible aria-label on the icon — noted as a limitation
- Google OAuth couldn't be automated so a separate email/password test account was created — this is the recommended industry approach

### API Testing
- Used Python `requests` instead of Playwright's built-in API testing because NextAuth.js login doesn't work cleanly in headless environments via direct API calls
- JWT token is grabbed manually from browser DevTools and stored in `.env` — this is explained clearly so reviewers can get their own
- All endpoints discovered through HAR file capture — pure black-box, no guessing about internals
- The download test has a known dependency on an existing project — documented above with steps to resolve

### Data Validation
- The script tests what the pipeline actually promised to do, not some ideal theoretical output
- All 30 checks pass on the real downloaded output
- Both age and salary imputation use the median which is deterministic, so results are consistent across runs
