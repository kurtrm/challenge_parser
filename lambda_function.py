import json
import requests

import boto3

from bs4 import BeautifulSoup as BS

def parse_herox_challenges():
    """
    Function designed to parse the HeroX website.
    """
    herox_url = 'https://www.herox.com/' 
    search_url = 'crowdsourcing-projects?page={}'  # Have to request each page for parsing
    challenges = []
    for i in range(1, 100):  # Iterate over arbitrary set interval, typically around 39 pages.
        page_url = herox_url + search_url.format(i)
        res = requests.get(page_url)
        if res.status_code == 200:
            soup = BS(res.content)
            page_data = soup.find(id='page-data').string  # This is a strange format for the data, but it's in a JSON string within this HTML element
            page_json = json.loads(page_data)
            packaged_data = BS(page_json['view']['initial']['html'])  # We then have to pull MORE HTML from within the JSON string
            page_content = packaged_data.find_all(class_='card-challenge')  # And the real data we need is in this class element
            for challenge in page_content:  # This loop grabs the data from these elements and puts them into a dictionary
                challenge_dict = {}
                challenge_dict['Title'] = challenge.find(class_='title').text
                challenge_dict['Creator'] = challenge.find(class_='creator-title').text.strip()
                challenge_dict['Description'] = challenge.find(class_='description').text
                try:
                    challenge_dict['Award'] = challenge.find(class_='award').text.strip()  # Sometimes an award is listed, sometimes not. If not we set this value as an empty string
                except AttributeError:
                    challenge_dict['Award'] = ''
                remaining = challenge.find_all('span')[-1].text.strip()  # HeroX doesn't "purge" old challenges right away. We check for the below conditions to exclude expired challenges.
                if 'Won' in remaining or 'Closed' in remaining or 'Submission Deadline' in remaining:
                    continue
                challenge_dict['Days Remaining'] = challenge.find_all('span')[-1].text.strip()
                challenge_dict['Contest URL'] = challenge['href']
                challenge_dict['Parent Website'] = 'HeroX'
                challenges.append(challenge_dict)
        else:
            break  # The for loop breaks when our requests return anything other than 200 status c
    
    return challenges

def parse_gov_challenges():
    """
    Function to parse challenge.gov website. Easiest parse of the three core sites.
    """
    url = 'https://www.challenge.gov/'
    challenges = []
    res = requests.get(url)
    if res.status_code == 200:
        soup = BS(res.content, 'html.parser')
        page_content = soup.find_all(class_='card')  # Each challenge's data is neatly contained in a card class element. 
        for challenge in page_content:  # We just parse through each card and put its data in a dictionary
            challenge_dict = {}
            challenge_dict['Title'] = challenge.find('h3').text
            challenge_dict['Creator'] = challenge.find(class_='text-gray-50').text
            challenge_dict['Description'] = challenge.find(class_='text-thin').text
            challenge_dict['Days Remaining'] = challenge.find(class_='card__body').text.strip()
            challenge_dict['Contest URL'] = challenge.find('a')['href']
            challenge_dict['Parent Website'] = 'challenge.gov'
            challenges.append(challenge_dict)
    
    return challenges

def lambda_handler(event, context):
    """
    This handler is what AWS calls. It calls the above parsing functions.

    If the parsing errors encounter an error or the result is abnormal, the user is made aware. via a 500 error.
    """
    try:
        gov_challenges = parse_gov_challenges()
        herox_challenges = parse_herox_challenges()  # Call parsing functions
    except Exception as e:
        return {
            'statusCode': 500,
            'body': f'Parser encountered error: {e}'  # If the parser encounters an error, it will return a 500 error and the body of the error message
        }
    # If for whatever reason the parser returns something abnormal, it will save the abnormal parse as something else so the results aren't displayed on the webpage
    # It will continue to leave the original data as the display data for the webpage
    if len(gov_challenges) < 5 or len(herox_challenges) < 5:  # Sort of an arbitrary condition to determine if something is wrong
        s3 = boto3.resource('s3')  # This is Amazon library stuff. 
        ob = s3.Object('challengeparses', 'abnormal_parse.txt')  # Saves the abnormal parse in this location with this file name
        ob.put(Body=json.dumps(gov_challenges.extend(herox_challenges)))
        return {
            'statusCode': 500,
            'body': f'Parser returned abnormal results. Saved parses as "abnormal_parse.txt".'
        }
    s3 = boto3.resource('s3')
    ob = s3.Object('challengeparses', 'parses.json')  # If no issues, the parses are saved as parses.json in the challengeparses S3 bucket
    gov_challenges.extend(herox_challenges)  # This just combines the two website dictionaries into one
    ob.put(Body=json.dumps(gov_challenges))
    
    return {
        'statusCode': 200,
        'body': "Parse successful."
    }