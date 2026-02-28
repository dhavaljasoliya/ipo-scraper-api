from flask import Flask, jsonify
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    return jsonify({
        "status": "running",
        "message": "StockBharat IPO Scraper API (Dashboard)",
        "endpoints": ["/api/ipos", "/api/ipos/current", "/api/ipos/upcoming"]
    })

@app.route('/api/ipos')
def get_all_ipos():
    try:
        ipos = scrape_dashboard_ipos()
        # Split roughly: assume first half recent/ongoing, rest upcoming
        mid = len(ipos) // 2
        current = ipos[:mid]
        upcoming = ipos[mid:]
        for ipo in upcoming: ipo["status"] = "upcoming"
        return jsonify({
            "success": True, "timestamp": datetime.now().isoformat(),
            "data": {"current": current, "upcoming": upcoming, "total": len(ipos)}
        })
    except Exception as e:
        logger.error(f"Error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/ipos/current')
def get_current_ipos():
    try:
        ipos = scrape_dashboard_ipos()
        return jsonify({
            "success": True, "timestamp": datetime.now().isoformat(),
            "data": ipos[:5],  # Top 5 as current/ongoing
            "count": len(ipos[:5])
        })
    except Exception as e:
        logger.error(f"Error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/ipos/upcoming')
def get_upcoming_ipos():
    try:
        ipos = scrape_dashboard_ipos()
        return jsonify({
            "success": True, "timestamp": datetime.now().isoformat(),
            "data": ipos[5:], "count": len(ipos[5:])
        })
    except Exception as e:
        logger.error(f"Error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

def scrape_dashboard_ipos():
    url = "https://www.chittorgarh.com"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
    }
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    
    soup = BeautifulSoup(response.text, 'html.parser')
    ipos = []
    
    # Find the main IPO table (under "Current mainboard IPOs")
    tables = soup.find_all('table')
    logger.info(f"Found {len(tables)} tables")
    
    for i, table in enumerate(tables):
        rows = table.find_all('tr')
        if len(rows) > 1 and 'Company' in rows[0].get_text():  # Header row check
            logger.info(f"Using table {i} as main IPO table")
            for row in rows[1:10]:  # First 10 rows
                cols = row.find_all(['td', 'th'])
                if len(cols) >= 2:
                    company_text = cols[0].get_text(strip=True)
                    dates_text = cols[1].get_text(strip=True)
                    
                    # Parse dates like "SEDEMAC Mechatronics 04 - 06 Mar P"
                    date_match = re.search(r'(\d{2}\s*-\s*\d{2}\s*[A-Za-z]{3})', dates_text)
                    issue_dates = date_match.group(1) if date_match else dates_text
                    
                    # Clean company (remove dates if appended)
                    company = re.sub(r'\s*\d{2}\s*-\s*\d{2}\s*[A-Za-z]{3}.*', '', company_text)
                    
                    ipo = {
                        "company": company.strip(),
                        "issueDates": issue_dates,
                        "priceLow": 0,  # Not on page, fetch separately if needed
                        "priceHigh": 0,
                        "openDate": issue_dates.split('-')[0].strip() if '-' in issue_dates else issue_dates,
                        "closeDate": issue_dates.split('-')[1].strip() if '-' in issue_dates else "TBA",
                        "lotSize": 0,
                        "status": "open",  # All listed as current/ongoing
                        "exchange": "NSE+BSE",
                        "type": "Mainboard"
                    }
                    ipos.append(ipo)
                    logger.info(f"Parsed: {company} - {issue_dates}")
            break  # Use first matching table
    
    logger.info(f"Total IPOs scraped: {len(ipos)}")
    return ipos

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
