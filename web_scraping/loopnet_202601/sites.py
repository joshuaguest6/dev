from bs4 import BeautifulSoup

with open('sitemap_AllListings.xml', 'r') as f:
    xml_content = f.read()

soup = BeautifulSoup(xml_content, 'html.parser')
urls = [loc.text for loc in soup.find_all('loc')]

urls[:5]