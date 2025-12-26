/**
 * Feature #578: Organization: Folders: create folder
 * Test Steps:
 * 1. Click 'New Folder'
 * 2. Name: 'Architecture'
 * 3. Create
 * 4. Verify folder created
 * 5. Verify appears in sidebar
 */

const puppeteer = require('puppeteer');
const crypto = require('crypto');

// Color codes
const GREEN = '\x1b[92m';
const RED = '\x1b[91m';
const YELLOW = '\x1b[93m';
const BLUE = '\x1b[94m';
const RESET = '\x1b[0m';

async function testCreateFolder() {
    let browser;
    try {
        console.log(`${BLUE}Starting Feature #578 test: Create folder${RESET}`);

        browser = await puppeteer.launch({
            headless: true,
            args: [
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-web-security',
            ]
        });

        const page = await browser.newPage();
        await page.setViewport({ width: 1280, height: 720 });

        // Step 1: Register and login
        console.log(`${YELLOW}Step 1: Registering test user...${RESET}`);
        const testEmail = `folder_test_578_${crypto.randomBytes(4).toString('hex')}@example.com`;
        const testPassword = 'SecurePass123!';

        await page.goto('http://localhost:3000/auth/register', { waitUntil: 'networkidle0', timeout: 60000 });
        await page.waitForSelector('input[type="email"]', { timeout: 10000 });

        await page.type('input[type="email"]', testEmail);
        await page.type('input[type="password"]', testPassword);
        await page.type('input[placeholder*="Name"]', 'Folder Test User');

        await page.click('button[type="submit"]');
        await new Promise(resolve => setTimeout(resolve, 3000));

        // Navigate to dashboard
        console.log(`${YELLOW}Step 2: Navigating to dashboard...${RESET}`);
        await page.goto('http://localhost:3000/dashboard', { waitUntil: 'networkidle0', timeout: 60000 });
        await new Promise(resolve => setTimeout(resolve, 2000));

        // Step 3: Click 'New Folder' button
        console.log(`${YELLOW}Step 3: Looking for 'New Folder' button...${RESET}`);

        // Wait for the folder sidebar
        await page.waitForSelector('.w-64', { timeout: 10000 });

        // Look for the create new folder button
        const newFolderButton = await page.$('button[title="Create new folder"]');
        if (!newFolderButton) {
            console.log(`${RED}✗ Could not find 'New Folder' button${RESET}`);
            return false;
        }

        console.log(`${GREEN}✓ Found 'New Folder' button${RESET}`);
        await newFolderButton.click();
        await new Promise(resolve => setTimeout(resolve, 1000));

        // Step 4: Verify modal appeared
        console.log(`${YELLOW}Step 4: Verifying create folder modal...${RESET}`);
        const modal = await page.$('.fixed.inset-0');
        if (!modal) {
            console.log(`${RED}✗ Create folder modal did not appear${RESET}`);
            return false;
        }

        console.log(`${GREEN}✓ Create folder modal appeared${RESET}`);

        // Step 5: Enter folder name 'Architecture'
        console.log(`${YELLOW}Step 5: Entering folder name 'Architecture'...${RESET}`);
        const folderNameInput = await page.$('input[placeholder*="Folder"]');
        if (!folderNameInput) {
            console.log(`${RED}✗ Could not find folder name input${RESET}`);
            return false;
        }

        await folderNameInput.type('Architecture');
        await new Promise(resolve => setTimeout(resolve, 500));

        console.log(`${GREEN}✓ Entered folder name${RESET}`);

        // Step 6: Click Create button
        console.log(`${YELLOW}Step 6: Clicking Create button...${RESET}`);

        // Find the Create button
        const createButtons = await page.$$('button');
        let createButton = null;
        for (const btn of createButtons) {
            const text = await page.evaluate(el => el.textContent, btn);
            if (text.includes('Create') && !text.includes('Creating')) {
                createButton = btn;
                break;
            }
        }

        if (!createButton) {
            console.log(`${RED}✗ Could not find Create button${RESET}`);
            return false;
        }

        await createButton.click();
        await new Promise(resolve => setTimeout(resolve, 2000));

        console.log(`${GREEN}✓ Clicked Create button${RESET}`);

        // Step 7: Verify modal closed
        console.log(`${YELLOW}Step 7: Verifying modal closed...${RESET}`);
        const modalAfter = await page.$('.fixed.inset-0');
        if (modalAfter) {
            console.log(`${RED}✗ Modal did not close after creation${RESET}`);
            return false;
        }

        console.log(`${GREEN}✓ Modal closed successfully${RESET}`);

        // Step 8: Verify folder appears in sidebar
        console.log(`${YELLOW}Step 8: Verifying folder appears in sidebar...${RESET}`);
        await new Promise(resolve => setTimeout(resolve, 2000));

        // Check for the folder in the sidebar
        const pageContent = await page.content();
        if (!pageContent.includes('Architecture')) {
            console.log(`${RED}✗ Folder 'Architecture' not found in page${RESET}`);
            return false;
        }

        // More specific check
        const folderElements = await page.$$('.w-64 button');
        let folderFound = false;
        for (const elem of folderElements) {
            const text = await page.evaluate(el => el.textContent, elem);
            if (text.includes('Architecture')) {
                folderFound = true;
                break;
            }
        }

        if (!folderFound) {
            console.log(`${RED}✗ Folder 'Architecture' not visible in folder tree${RESET}`);
            return false;
        }

        console.log(`${GREEN}✓ Folder 'Architecture' appears in sidebar!${RESET}`);

        // Bonus: Verify folder is clickable
        console.log(`${YELLOW}Bonus: Testing folder is clickable...${RESET}`);
        for (const elem of folderElements) {
            const text = await page.evaluate(el => el.textContent, elem);
            if (text.includes('Architecture')) {
                await elem.click();
                await new Promise(resolve => setTimeout(resolve, 1000));
                console.log(`${GREEN}✓ Folder is clickable and interactive${RESET}`);
                break;
            }
        }

        console.log(`\n${GREEN}${'='.repeat(60)}${RESET}`);
        console.log(`${GREEN}✓ Feature #578 PASSED: Create folder functionality works!${RESET}`);
        console.log(`${GREEN}${'='.repeat(60)}${RESET}\n`);

        return true;

    } catch (error) {
        console.log(`\n${RED}✗ Test failed with error: ${error.message}${RESET}`);
        console.error(error);
        return false;

    } finally {
        if (browser) {
            await browser.close();
        }
    }
}

async function main() {
    const success = await testCreateFolder();
    process.exit(success ? 0 : 1);
}

main();
