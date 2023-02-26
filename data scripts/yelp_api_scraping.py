import json
from urllib.parse import quote
import requests

API_HOST = 'https://api.yelp.com'
SEARCH_PATH = '/v3/businesses/search'

api_key = 'x9KyWT6ieCt3GrdGOhRCKpwSxFp7G6aCmMWTZjUyS4Js45mrfzeDuYGl71a4O0cDc1pUwVMR7Rd2jmzr7sBzK0_YFxlZEu9q1VaudLWb6WkomPRG5YWEtxQFtz9jYXYx'
cuisine_list = ['chinese', 'indian', 'american', 'mexican', 'italian', 'french', 'thai']
restaurants_rows = []
for i in cuisine_list:
    for j in range(0, 20):
        url_params = {
            'term': i.replace(' ', '+'),
            'location': 'Manhattan, New York'.replace(' ', '+'),
            'limit': 50,
            'offset': j * 50 + 1
        }


        def request(host, path, api_key, url_params=None):
            url_params1 = url_params or {}
            url = '{0}{1}'.format(host, quote(path.encode('utf8')))
            headers = {
                'Authorization': 'Bearer %s' % api_key,
            }

            #print(u'Querying {0} ...'.format(url))

            response = requests.request('GET', url, headers=headers, params=url_params1)

            return response.json()


        response1 = request(API_HOST, SEARCH_PATH, api_key, url_params=url_params)

        if response1 and response1.get('businesses'):
            for d in response1['businesses']:
                row = {'business_id': d['id'],
                       'name': d['name'],
                       'review_count': d['review_count'],
                       'rating': d['rating'],
                       'address': ', '.join(d['location']['display_address']),
                       'cuisine': i,
                       'latitude': d['coordinates']['latitude'],
                       'longitude': d['coordinates']['longitude'],
                       'city': d['location']['city'],
                       'zip_code': d['location']['zip_code'],
                       'state': d['location']['state']
                       }
                restaurants_rows.append(row)

print(len(restaurants_rows))

with open('yelp.json', 'w') as f:
    f.write(json.dumps(restaurants_rows) + '\n')
