import json
from decimal import Decimal

data = []
with open('yelp.json', 'r') as file1:
    for row in file1:
        print(row)
        temp = json.loads(row, parse_float=Decimal)
        data = temp

print(data)

with open('rest.json', 'w') as f:
    for row in data:
        f.write(json.dumps({'index': {'_index': 'restaurants', '_id':row['name']}}) + '\n')
        f.write(json.dumps({'cuisine': row['cuisine'], 'business_id': row['business_id']}) + '\n')