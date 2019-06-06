import datetime
import json
import sys

import mysql.connector

credentials = json.load(open('db.json'))
cnx = mysql.connector.connect(host=credentials['host'], user=credentials['user'], database=credentials['database'], password=credentials['password'])
cursor = cnx.cursor()


class Daterange(object):
    def __init__(self, start, end):
        if isinstance(start, basestring):
            self.start_string = start
            self.start = datetime.datetime.strptime(start, '%Y-%m-%d').date()
        else:
            self.start = start
            self.start_string = start.strftime('%Y-%m-%d')

        if isinstance(end, basestring):
            self.end_string = end
            self.end = datetime.datetime.strptime(end, '%Y-%m-%d').date()
        else:
            self.end = end
            self.end_string = end.strftime('%Y-%m-%d')

def get_dept_name(dept_no):
    cursor.execute('select dept_name from departments where dept_no = %s;', (dept_no,))
    try:
        name = cursor.fetchone()[0]
    except TypeError:
        name = None
    return name

def get_oldest_record_date():
    oldest_record_query = 'select from_date from salaries order by from_date asc limit 1;'
    cursor.execute(oldest_record_query)
    return cursor.fetchone()[0]

def get_newest_record_date():
    newest_record_query = "select to_date from salaries where to_date <> '9999-01-01' order by to_date desc limit 1;"
    cursor.execute(newest_record_query)
    return cursor.fetchone()[0]

def generate_quarter_date_ranges():
    '''Function to generate a list of date ranges for all quarters for which salary data exists
    
    Returns:
        datarange(list): List of Daterange objects representing the quarters for which salary data exists
    '''
    oldest_record_date = get_oldest_record_date()
    newest_record_date = get_newest_record_date()
    
    current_year = oldest_record_date.year
    current_month = oldest_record_date.month
    dateranges = []
    while True:
        # if current_month isn't the start of a quarter, we should start at the beginning of that quarter
        # originally, I was setting the current_month to 1 if the current_month wasn't the start of a quarter,
        # but that included additional quarters at the beginning of a range if the oldest_record_date starts after Q1
        if current_month not in [1, 4, 7, 10]:
            if current_month in [2,3]:
                current_month = 1
            elif current_month in [5,6]:
                current_month = 4
            elif current_month in [8,9]:
                current_month = 7
            elif current_month in [11,12]:
                current_month = 10
            else:
                # if current_month is over 12, we need to also increment the year by 1
                current_month = 1
                current_year += 1
        # for each quarter, the ones starting in months 1 and 10 have 31 days and the others only have 30
        if current_month in [1,10]:
            end_day = 31
        else:
            end_day = 30
        # if current_year matches the year of the newest record and the current month is greater than the 
        # month of the newest record, we can exclude this quarter and end now 
        if (current_year == newest_record_date.year and current_month > newest_record_date.month) or current_year > newest_record_date.year:
            break
        dateranges.append(Daterange(
                    '{1}-{0}-01'.format(current_month, current_year),
                    '{0}-{1}-{2}'.format(current_year, current_month + 2, end_day)))
        current_month += 3
    return dateranges

def generate_employee_salaries_for_date_range(daterange):
    '''Function to generate list of salaries for which data exists during the given date range

    Parameters:
        daterange: Daterange object used to represent the date range used in the search

    Return:
        salaries(list): List of salaries for which data exists in the given date range
    '''
    #(from_date < date_range_start and to_date > date_range_start) or (from_date > date_range_start and from_date < date_range_end)
    query = 'select salary, dept_no, salaries.from_date, salaries.to_date from salaries join dept_emp on salaries.emp_no = dept_emp.emp_no where (salaries.from_date < %s and salaries.to_date > %s) or (salaries.from_date > %s and salaries.from_date < %s);'
    #import pdb;pdb.set_trace()
    cursor.execute(query, (daterange.start, daterange.start, daterange.start, daterange.end ))
    salaries = cursor.fetchall()
    return salaries

#def calculate_percent_overlap(from_date, to_date, date_range_start, date_range_end):
def calculate_percent_overlap(daterange1, daterange2):
    '''Function to calculate the percent overlap off date_range1 on date_range2

        Parameters:
            date_range1(Daterange): Daterange object
            date_range2(Daterange): Daterange object

        Returns:
            percent_overlap(float): The percentage of the second date range that overlaps with the first.

    '''
    daterange2_range = daterange2.end - daterange2.start
    # if the salary starts before the range, do the following
    if daterange1.start < daterange2.start:
        # if the salary ends after the date range ends, we have full coverage
        if daterange1.end > daterange2.end:
            overlap = daterange2.end - daterange2.start
        else:
            # if not, we know the salary was active at the beginning of the range and we know that the salary ends within the range
            # so we can easily determine the overlap
            overlap = daterange1.end - daterange2.start
    else:
        # if salary doesn't start before the range and salary extends past the range, we can easily determine the overlap
        if daterange1.end > daterange2.end:
            overlap = daterange2.end - daterange1.start
        else:
            # The rest will fall inside the daterange, so we can use the following method
            overlap = daterange1.end - daterange1.start
    return float(overlap.days) / float(daterange2_range.days)

def generate_data(daterange):
    '''Function to generate the report of salary costs per department for a given date range

    Parameters:
        datarange(Daterange): Daterange object used to generate salary data
    '''
    salaries = generate_employee_salaries_for_date_range(daterange)
    total_salary = {}
    #print 'From {0} to {1}'.format(daterange.start, daterange.end)
    for salary in salaries:
        # example salary: (53377, u'd001', datetime.date(1989, 4, 25), datetime.date(1990, 4, 25))
        dept_no = salary[1]
        daterange1 = Daterange(salary[2], salary[3])
        daterange2 = daterange
        percent_overlap = calculate_percent_overlap(daterange1, daterange2)
        salary_for_full_quarter = salary[0]/4
        try:
            total_salary[dept_no] += salary_for_full_quarter * percent_overlap
        except KeyError:
            total_salary[dept_no] = salary_for_full_quarter * percent_overlap

    ret = {}
    for department, salary in total_salary.iteritems():
        ret[department] = salary
    return ret

def generate_report():
    '''Function to generate a report showing how much each department is spending on employee salaries each quarter.
    '''
    reports = {}
    # generate salary data for each quarter
    for daterange in generate_quarter_date_ranges():
        print 'Generating data for {0} to {1}...'.format(daterange.start, daterange.end)
        reports[daterange.start] = generate_data(daterange)

    departments = {}
    # reformat data for outputting
    for date, data in reports.iteritems():
        for dept_no, salary_cost in data.iteritems():
            departments.setdefault(dept_no, {})[date] = salary_cost

    for dept_no, quarterly_salaries in departments.iteritems():
        print 'Department: {0}'.format(get_dept_name(dept_no))
        for date, salary in sorted(quarterly_salaries.iteritems()):
            print '\t{0}: {1}'.format(date, salary)

if __name__ == '__main__':
    generate_report()
