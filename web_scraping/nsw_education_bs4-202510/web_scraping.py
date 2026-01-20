import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By

url = "https://www.nsw.gov.au/education-and-training/nesa/curriculum/mathematics/mathematics-extension-2-stage-6-2017"
resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
soup = BeautifulSoup(resp.text, "html.parser")

# Example: get the main title
title = soup.find("h1").get_text(strip=True)

about_header = soup.find(lambda tag: tag.name.startswith('h2') and 'About the course' in tag.get_text())
if about_header:
    about_paragraphs = []
    for sibling in about_header.find_next_siblings():
        if sibling.name and sibling.name.startswith('h2'):
            break
        if sibling.name == 'p' or sibling.name == 'ul' or sibling.name == 'div':
            about_paragraphs.append(sibling.get_text(strip=True))
about_text = '\n'.join(about_paragraphs)

topics={}
what_learn_header = soup.find(lambda tag: "What students learn" in tag.get_text())
if what_learn_header:
    for sibling in what_learn_header.find_next_siblings():
        if sibling.name == 'h3':
            current_topic = sibling.get_text(strip=True)
            topics[current_topic] = []
        elif sibling.name == 'ul' and current_topic:
            for li in sibling.find_all('li'):
                topics[current_topic].append(li.get_text(strip=True))
        if sibling.name and sibling.name.startswith('h2') and 'Topics' not in sibling.get_text():
            pass


# Check the parent & children
print("Parent tag:", what_learn_header.parent.name, what_learn_header.parent.get("class"))
print("Children of parent:")
for child in what_learn_header.parent.find_all(recursive=False):
    print(child.name, child.get("class"))