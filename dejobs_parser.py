# I. User should be able to provide number of pages to crawl and the crawler should go
# through each page. [Assume number of pages will not be more than 50].

# II. Crawler should output following attributes:
# a.Required: Job Title, Job Url, Company
# Name, Location, Job Description (Job Description should be cleaned from html tags and
# escape symbols)
# b. Optional: Country, Posted Date, Category (or Industry), salary

# IV. Output should be in one of formats: json OR csv. (With date and crawl time appended to the name)

# TASK 2. SAVE TO DATABASE (ADDITIONAL)
# Create a table database `dejobs.db` and a table "jobs" (in sqlite), schema as per required (and/or optional)
# attributes (as TASK 1-II), insert output from TASK 1-IV to sqlite database, handle duplicates here.

# TASK3. AUTOMATION (ADDITIONAL)
# Write another script (or documentation) about deploying the crawler on server so that it runs at 11:55pm each day.


import datetime
from bs4 import BeautifulSoup
import requests
import argparse
import sqlite3
import re
import json

actual_date_and_crawl_time = datetime.datetime.now().strftime("DATE-%m-%d-%Y-TIME-%H-%M")
file_name = f'{actual_date_and_crawl_time}_dejobs_parse_output.json'

url = 'https://dejobs.org/jobs/ajax/joblisting/'

params = {
    'num_items': 15,
    'offset': 0
}

jobs_urls = []
results_list = []


def json_results_saver(output_filename):
    with open(output_filename, 'w', encoding='utf-8') as json_file:
        for job in results_list:
            json.dump(job, json_file, indent=4)


def db_results_saver():
    connection = sqlite3.connect('dejobs.db')

    cursor = connection.cursor()

    # Job_Title TEXT PRIMARY KEY handle duplicates for DB.
    cursor.execute(
        'CREATE TABLE IF NOT EXISTS jobs (Job_Title TEXT PRIMARY KEY, Job_Url TEXT, Company_Name TEXT, Location TEXT, Country TEXT, Job_Description TEXT, Posted_Date TEXT)')
    connection.commit()
    for job in results_list:
        cursor.execute(
            'INSERT OR IGNORE INTO jobs (Job_Title, Job_Url, Company_Name, Location, Country, Job_Description, Posted_Date) VALUES (?, ?, ?, ?, ?, ?, ?)',
            [*job.values()])
        connection.commit()

    connection.close()


def jobs_urls_getter(pages_need_to_pharse):
    for page in range(0, pages_need_to_pharse):
        # Assume number of pages will not be more than 50
        if page + 1 > 50:
            break

        response = requests.get(url, params=params)

        soup = BeautifulSoup(response.text, 'lxml')

        for job in soup.find_all('li', class_='direct_joblisting'):
            jobs_urls.append(job.find('a', href=True)['href'])

        params['offset'] += 15

        print(f'Page number...........................{page + 1} - links collected')


def page_parser():
    for job in jobs_urls:
        results = {}

        job_page_url = 'https://dejobs.org' + job

        response = requests.get(job_page_url)

        soup = BeautifulSoup(response.text, 'lxml')

        # Job Title
        job_title = soup.find(itemprop='title')
        results['job_title'] = job_title.text

        # Job Url
        job_url = soup.find('link', rel='canonical', href=True)
        results['job_url'] = job_url['href']

        # Company Name
        company_name = soup.find('span', itemprop='name')
        results['company_name'] = company_name.text

        # Location
        job_location = soup.find('span', itemprop='address')
        try:
            location = job_location.find_next('span', itemprop='addressLocality').text
        except:
            location = None

        # Country
        try:
            country = job_location.find_next('meta', itemprop='addressCountry')['content']
        except:
            country = country = job_location.find_next('span', itemprop='addressCountry').text

        results['location'] = location
        results['country'] = country

        # Job Description
        job_desc = soup.find('div', itemprop='description').text
        # remove all escape characters
        job_desc = re.sub('[^A-Za-z0-9]+', ' ', job_desc)
        results['job_desc'] = job_desc.strip()

        # Posted Date
        posted_date = soup.find(itemprop='datePosted')['content']
        results['posted_date'] = posted_date

        results_list.append(results)


parser = argparse.ArgumentParser(description='dejobs_parse_script')
parser.add_argument('--pages_to_parse', dest="pages", required=True, type=int)
args = parser.parse_args()

jobs_urls_getter(args.pages)
page_parser()
json_results_saver(output_filename=file_name)
db_results_saver()
print('Done')
