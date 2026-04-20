import requests
import os
import sys
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '../.env'))
API_BASE_URL = 'https://api.rhombusai.com'
TOKEN = os.getenv('RHOMBUS_TOKEN')
CSV_FILE = os.path.join(os.path.dirname(__file__), '../data-validation/Messy_Employee_dataset.csv')

# test trackers
passed = 0
failed = 0

def check(test_name, condition, detail=''):
    global passed, failed
    if condition:
        print(f' PASS  {test_name}')
        passed += 1
    else:
        print(f'  FAIL  {test_name}')
        if detail:
            print(f'          → {detail}')
        failed += 1

# Test 1: Dataset Upload (Positive Test)
def test_dataset_upload():
    print('\n' + '─' * 60)
    print('  Test 1 · Dataset Upload')
    print('─' * 60)

    # Send CSV as multipart form-data to the upload endpoint
    with open(CSV_FILE, 'rb') as f:
        response = requests.post(
            f'{API_BASE_URL}/api/dataset/datasets/temp/upload',
            files={
                'file': ('Messy_Employee_dataset.csv', f, 'text/csv')
            },
            data={
                'title': 'Messy_Employee_dataset.csv',
                'description': '',
                'column_header_row': 1
            }
        )

    # Check 1 - status code
    check(
        'Upload returns 200',
        response.status_code == 200,
        detail=f'Got {response.status_code}'
    )

    body = response.json()

    # Check 2 - response has correct filename
    check(
        'Response contains correct filename',
        body.get('title') == 'Messy_Employee_dataset.csv',
        detail=f'Got title: {body.get("title")}'
    )

    # Check 3 - file size is correct (117662 bytes)
    check(
        'Response contains correct file size',
        body.get('file_size') == 117662,
        detail=f'Got file_size: {body.get("file_size")}'
    )

    # Check 4 - content type is CSV
    check(
        'Response confirms CSV content type',
        body.get('content_type') == 'text/csv',
        detail=f'Got content_type: {body.get("content_type")}'
    )

    # Check 5 - response has an ID (needed for further processing)
    check(
        'Response contains dataset ID',
        isinstance(body.get('id'), int),
        detail=f'Got id: {body.get("id")}'
    )

    print(f'\n  Upload response: id={body.get("id")}, size={body.get("file_size")} bytes')

# Test 2: Upload Invalid File (Negative Test)
def test_dataset_upload_invalid_file():
    print('\n' + '─' * 60)
    print('  Test 2 · Upload Invalid File (Negative Test)')
    print('─' * 60)

    # Trying uploading a .txt file instead of a CSV
    response = requests.post(
        f'{API_BASE_URL}/api/dataset/datasets/temp/upload',
        files={
            'file': ('test.txt', b'this is not a csv file', 'text/plain')
        },
        data={
            'title': 'test.txt',
            'description': '',
            'column_header_row': 1
        }
    )

    # Server should either reject with 4xx OR return a response
    check(
        'Invalid file type is rejected or flagged',
        response.status_code in [400, 415, 422, 500] or
        response.json().get('content_type') != 'text/csv',
        detail=f'Got status {response.status_code}, body: {response.text}'
    )

    print(f'  Server response: {response.status_code} - {response.text[:100]}')

# Test 3: Download Pipeline Output
def test_download_output():
    print('\n' + '─' * 60)
    print('  Test 3 · Download Pipeline Output')
    print('─' * 60)

    # These values come from     existing project in Rhombus AI
    PROJECT_ID = '3489'
    NODE_NAME  = 'llm_c289075b97248ba723ce290ae1a220d5'

    headers = {'Authorization': f'Bearer {TOKEN}'}

    response = requests.get(
        f'{API_BASE_URL}/api/dataset/analyzer/v2/projects/{PROJECT_ID}/nodes/output-download',
        params={
            'node_name': NODE_NAME,
            'format': 'csv'
        },
        headers=headers
    )

    # Check 1 - status code
    check(
        'Download returns 200',
        response.status_code == 200,
        detail=f'Got {response.status_code}'
    )

    # Check 2 - response is not empty
    check(
        'Downloaded content is not empty',
        len(response.text) > 0,
        detail='Response body is empty'
    )

    # Check 3 - content looks like CSV (has commas and newlines)
    check(
        'Downloaded content is valid CSV format',
        ',' in response.text and '\n' in response.text,
        detail='Content does not look like CSV'
    )

    # Check 4 - first line is a header row
    first_line = response.text.split('\n')[0]
    check(
        'Downloaded CSV has a header row',
        len(first_line) > 0 and ',' in first_line,
        detail=f'First line: {first_line[:50]}'
    )

    print(f'\n  Downloaded {len(response.text)} bytes')
    print(f'  First line: {first_line[:80]}')


# Run tests
print('\nRhombus AI – API Test Report')
print('=' * 60)

test_dataset_upload()
test_dataset_upload_invalid_file()
test_download_output()

# Summary
total = passed + failed
print(f'\n{"═" * 60}')
print(f'  RESULTS:  {passed}/{total} checks passed')
if failed == 0:
    print('  All checks passed!')
else:
    print(f' {failed} check(s) failed.')
print(f'{"═" * 60}\n')

sys.exit(0 if failed == 0 else 1)
