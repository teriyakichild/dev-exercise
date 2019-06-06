import datetime
from mock import patch
import pytest
from generate_report import get_dept_name, generate_quarter_date_ranges, Daterange, generate_report, generate_data

def test_get_dept_name():
    # positive and negative tests for get_dept_name
    assert get_dept_name('d007') == 'Sales'
    assert get_dept_name('d000') != 'Bales'

def test_generate_quarter_date_ranges():
    ranges = generate_quarter_date_ranges()
    range1 = ranges[0]
    # test that the internal variables are set correctly according to the datetime format "%Y-%m-%d"
    assert range1.start == datetime.datetime.strptime(range1.start_string, '%Y-%m-%d').date()

@patch('generate_report.get_oldest_record_date')
@patch('generate_report.get_newest_record_date')
def test_generate_quarter_date_ranges_with_mocked_start_end_dates(mock_newest, mock_oldest):
    mock_oldest.return_value = datetime.datetime.strptime('1990-01-01', '%Y-%m-%d').date()
    mock_newest.return_value = datetime.datetime.strptime('2000-09-30', '%Y-%m-%d').date()
    ranges = generate_quarter_date_ranges()
    assert len(ranges) == 43

    mock_oldest.return_value = datetime.datetime.strptime('1990-01-01', '%Y-%m-%d').date()
    mock_newest.return_value = datetime.datetime.strptime('2000-10-01', '%Y-%m-%d').date()
    ranges = generate_quarter_date_ranges()
    assert len(ranges) == 44

    mock_oldest.return_value = datetime.datetime.strptime('1989-12-30', '%Y-%m-%d').date()
    mock_newest.return_value = datetime.datetime.strptime('2000-10-01', '%Y-%m-%d').date()
    ranges = generate_quarter_date_ranges()
    assert len(ranges) == 45


def test_generate_data():
    data = generate_data(Daterange('1990-01-01', '1990-03-31'))
    assert data['d008'] == 90293829.58426961

@patch('generate_report.generate_employee_salaries_for_date_range')
def test_generate_data_with_mocked_salaries(mock_salaries):
    # test with easy to calculate inputs
    mock_salaries.return_value = [
        (100000, u'd001', datetime.date(1990, 1, 1), datetime.date(1990, 12, 30)),
        (100000, u'd001', datetime.date(1990, 1, 1), datetime.date(1990, 12, 30)),
        (100000, u'd002', datetime.date(1990, 1, 1), datetime.date(1990, 12, 30)),
        (100000, u'd002', datetime.date(1990, 1, 1), datetime.date(1990, 12, 30)),
    ]
    data = generate_data(Daterange('1990-01-01','1990-03-31'))
    assert data['d001'] == 50000
    assert data['d002'] == 50000

    # test with the overlap starting at the beginning of the range and ending within it
    mock_salaries.return_value = [
        (100000, u'd001', datetime.date(1990, 1, 1), datetime.date(1990, 1, 31)),
        (100000, u'd002', datetime.date(1990, 1, 1), datetime.date(1990, 2, 28)),
    ]
    data2 = generate_data(Daterange('1990-01-01','1990-03-31'))
    assert data2['d001'] == 8426.966292134832
    assert data2['d002'] == 16292.134831460675

    # test with the overlap starting before the range and ending within it.  should be
    # equal to the last results
    mock_salaries.return_value = [
        (100000, u'd001', datetime.date(1989, 1, 1), datetime.date(1990, 1, 31)),
        (100000, u'd002', datetime.date(1989, 1, 1), datetime.date(1990, 2, 28)),
    ]
    data3 = generate_data(Daterange('1990-01-01','1990-03-31'))
    assert data3['d001'] == data2['d001']
    assert data3['d002'] == data2['d002']

    # test with the overlap starting within the range and ending with the range. should be
    # equal to the last results
    mock_salaries.return_value = [
        (100000, u'd001', datetime.date(1990, 3, 1), datetime.date(1990, 3, 31)),
        (100000, u'd002', datetime.date(1990, 2, 1), datetime.date(1990, 3, 31)),
    ]
    data4 = generate_data(Daterange('1990-01-01','1990-03-31'))
    assert data4['d001'] == data2['d001']
    assert data4['d002'] == data2['d002']
