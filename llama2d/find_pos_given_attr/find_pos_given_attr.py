from datasets import load_dataset
from pprint import pprint

# Load the Mind2Web dataset
dataset = load_dataset("osunlp/Mind2Web")
example = dataset["train"][0]


attrs = example["actions"][0]["pos_candidates"][0]["attributes"]


import requests
from bs4 import BeautifulSoup
import json

# URL of the webpage you want to scrape
url = "http://example.com"

print(example["domain"])
print(example["subdomain"])

# We might be able to assume website we can append .com to it
print(example["website"])
print(len(dataset["train"]))

print("Attemping to find all tags that contains that contain the attrs:")
print(type(attrs))
print(attrs)

attributes = json.loads(attrs)


# Send a GET request to the webpage
response = requests.get(url)
soup = BeautifulSoup(response.content, "html.parser")

# Find all tags that match the attributes
matching_tags = soup.find_all(attrs=attributes)

# Check if there are matching tags
if matching_tags:
    print(f"Found {len(matching_tags)} matching tag(s)!")
    for tag in matching_tags:
        print(tag)
else:
    print("No matching tags found!")
