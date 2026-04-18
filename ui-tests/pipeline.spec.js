

require('dotenv').config();
const { test, expect } = require('@playwright/test');
const path = require('path');

//Credentials from .env 
const EMAIL    = process.env.RHOMBUS_EMAIL;
const PASSWORD = process.env.RHOMBUS_PASSWORD;

//Path to the test CSV file 
const CSV_FILE = path.resolve(__dirname, '../data-validation/Messy_Employee_dataset.csv');


// TEST

test.describe('Rhombus AI – AI Pipeline Flow', () => {

  test('should login, upload CSV, run pipeline and download result', async ({ page }) => {

    // Step 1: Go to homepage 
    await page.goto('https://rhombusai.com/');
    console.log('Navigated to homepage');

    // Close welcome popup
    const closeButton = page.getByRole('button', { name: 'Close' });
    if (await closeButton.isVisible({ timeout: 5000 }).catch(() => false)) {
      await closeButton.click();
    }
    console.log('Closed welcome popup');

    // Step 2: Open login 
    await page.getByRole('button', { name: 'Log In' }).click();
    console.log('Opening login page');

    // Step 3: Fill credentials
    await page.getByRole('textbox', { name: 'Email address' }).fill(EMAIL);
    await page.getByRole('textbox', { name: 'Password' }).fill(PASSWORD);
    console.log('Filled login credentials');

    // Step 4: Submit login 
    await page.getByRole('button', { name: 'Log In' }).click();
    console.log('Submitted login credentials');

    // Step 5: Handle post-login popup
    await page.waitForURL('https://rhombusai.com/');

    console.log('Waiting for post-login popup');


    await page.getByRole('button', { name: 'Next: Ask Rhombo' }).click();
    await page.getByRole('button', { name: 'Next: Download Results' }).click();
    await page.getByRole('button', { name: 'Start Building' }).click();
    console.log('post-login popup dismissed');

    // Step 6: Verify logged in 
    await expect(await page.getByRole('textbox', { name: 'Attach or drop a file... Try' }))
    .toBeVisible({ timeout: 15000 });

    console.log('Logged in successfully');


    // Step 7: Upload CSV file
    // Click the file/attachment area
    await page.getByRole('button').filter({ hasText: /^$/ }).nth(2).click();

    // Wait for the Add New File modal to appear
    await page.getByText('Browse Here').waitFor({ state: 'visible' });
    console.log('Add New File modal opened');

    // Handling file selector
    await page.locator('input[type="file"]').setInputFiles(CSV_FILE, { force: true });
    console.log('CSV file selected');

    // Wait for file to appear on right side then click Attach
    await page.getByRole('button', { name: 'Attach' }).waitFor({ state: 'visible' });
    await page.getByRole('button', { name: 'Attach' }).click();
    console.log('File attached');

    // Step 8: Type the prompt
    const promptBox = page.getByRole('textbox', { name: 'What would you like to' });
    await promptBox.fill('Please clean and transform this dataset. Standardise column names to lowercase. Fill missing Age values with the column median. Fill missing Salary values with the median. Fix negative Phone numbers. Standardise Join_Date to YYYY-MM-DD format. Remove duplicates.');
    console.log('Prompt entered');

    //Step 9: Submit prompt
    // Use the send button (arrow button next to prompt box)
    await page.getByRole('button').filter({ hasText: /^$/ }).nth(4).click()
      .catch(async () => {
        // Fallback: press Enter if no Send button found
        await promptBox.press('Enter');
      });
    console.log('Prompt submitted');

    // Step 10: Handle any follow-up prompt if shown
    const missingDetail = page.getByRole('textbox', { name: 'Add the missing detail here...' });
    if (await missingDetail.isVisible({ timeout: 10000 }).catch(() => false)) {
      await missingDetail.fill('Fix null values, remove duplicates, standardise date formats and keep data readable');
      await page.getByRole('button', { name: 'Continue' }).click();
      console.log('Follow-up prompt answered');
    }
  
    // ── Step 11: Wait for canvas to load ────────────────────────────────────
    await page.getByRole('button', { name: 'Run Pipeline' })
      .waitFor({ state: 'visible', timeout: 60000 });
    console.log('Pipeline created, canvas loaded');

    // ── Step 13: Wait for pipeline to be created and run ──────────

    await page.locator('[data-testid="run-pipeline"].bg-destructive')
      .waitFor({ state: 'visible', timeout: 30000 });
    console.log('Pipeline started running...');

    // Wait for destructive class to disappear (pipeline finished)
    await page.locator('[data-testid="run-pipeline"].bg-destructive')
      .waitFor({ state: 'hidden', timeout: 120000 });
    console.log('Pipeline finished!');

    await page.getByTestId('rf__node-llm_node_1')
      .waitFor({ state: 'visible', timeout: 120000 });
    await page.getByTestId('rf__node-llm_node_1').click();
    console.log('Output node clicked');

    // ── Step 14: Click Preview tab ──────────────────────────────────────────
    await page.getByRole('tab', { name: 'Preview' }).waitFor({ state: 'visible' });
    await page.getByRole('tab', { name: 'Preview' }).click();
    console.log('Preview tab opened');

    // ── Step 15: Download result ────────────────────────────────────────────
    const downloadPromise = page.waitForEvent('download');
    await page.getByRole('button', { name: 'Download' }).click();
    await page.getByRole('menuitem', { name: 'Download as CSV' }).click();
    const download = await downloadPromise;

    expect(download.suggestedFilename()).toContain('.csv');
    console.log(`File downloaded: ${download.suggestedFilename()}`);
    console.log('Full pipeline flow completed!');
  });

});