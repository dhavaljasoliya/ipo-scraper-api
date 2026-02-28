import requests
from bs4 import BeautifulSoup

class IPOScraper:
    def __init__(self, base_url):
        self.base_url = base_url

    def fetch_data(self):
        try:
            response = requests.get(self.base_url)
            response.raise_for_status()
            return response.content
        except requests.exceptions.RequestException as e:
            print(f'Error fetching data: {e}')  # Improved error handling
            return None

    def parse_data(self, html):
        soup = BeautifulSoup(html, 'html.parser')
        ipo_data = []
        table = soup.find('table')  # Better table detection logic
        if table:
            headings = [header.text.strip() for header in table.find_all('th')]
            for row in table.find_all('tr')[1:]:  # Skip header row
                cells = row.find_all('td')
                if len(cells) == len(headings):  # Ensure equal number of cells and headings
                    ipo_data.append({headings[i]: cells[i].text.strip() for i in range(len(headings))})
        return ipo_data

    def get_ipo_data(self):
        html = self.fetch_data()
        if html:
            return self.parse_data(html)
        return []

if __name__ == '__main__':
    scraper = IPOScraper('https://www.chittorgarh.com/')
    ipo_data = scraper.get_ipo_data()
    if ipo_data:
        for ipo in ipo_data:
            print(ipo)
    else:
        print('No IPO data found.')