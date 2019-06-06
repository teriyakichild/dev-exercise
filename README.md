# quarterly-salary-report

## Description
This is a script used to generate a report of how much each department spends on salaries per quarter.  The data comes from a test database that can be created following the instructions, [here](https://github.com/datacharmer/test_db)

## Usage
1. Clone repository and cd into directory
2. Create and import test_db following the instructions, [here](https://github.com/datacharmer/test_db).
3. Create db.json file with database credentials using the db.json.example file as a reference.
3. Ensure python requirements are met:
```bash
pip install -r requirements.txt
```
3. Run the tests to ensure the script will work as expected:
```bash
pytest
```
4. Run the script to generate the report:
```bash
python generate_report.py
```
