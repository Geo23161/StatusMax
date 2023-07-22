import requests
import json

url = "https://api.apilayer.com/ip_to_location/"

payload = {}
headers= {
  "apikey": "UwAwAWWwrJ6hz2upOxalNLPd4rmB34g4"
}

def get_quart(ip):
    response = requests.request("GET", url + f"{ip}", headers=headers, data = payload)
    status_code = response.status_code
    result = json.loads(response.text)
    return {
        'lat' : result['latitude'],
        'lng' : result['longitude'],
        'name' : result['city'],
        "formatted_address" : result['country_name'],
        "typ" : 'country'
    }