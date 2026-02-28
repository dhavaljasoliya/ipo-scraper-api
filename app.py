from flask import Flask, jsonify
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re
import logging

# Enable logging for Railway
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Allow requests from iOS app

@app.route('/')
def home():
    return jsonify({
        "status": "running",
        "message": "StockBharat IPO Scraper API",
        "endpoints": {
            "/api/ipos": "Get all IPOs (current + upcoming)",
            "/api/ipos/current": "Get only current/open IPOs",
            "/api/ipos/upcoming": "Get only upcoming IPOs"
        }
    })

@app.route('/api/ipos')
def get_all_ipos():
    """Get all IPOs from Chittorgarh"""
    try:
        current = scrape_chittorgarh_current()
        upcoming = scrape_chittorgarh_upcoming()
        return jsonify({
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "data": {
                "current": current,
                "upcoming": upcoming,
                "total": len(current) + len(upcoming)
            }
        })
    except Exception as e:
        logger.error(f"Error in get_all_ipos: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/ipos/current')
def get_current_ipos():
    """Get only current/open IPOs"""
    try:
        ipos = scrape_chittorgarh_current()
        return jsonify({
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "data": ipos,
            "count": len(ipos)
        })
    except Exception as e:
        logger.error(f"Error in get_current_ipos: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/ipos/upcoming')
def get_upcoming_ipos():
    """Get only upcoming IPOs"""
    try:
        ipos = scrape_chittorgarh_upcoming()
        return jsonify({
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "data": ipos,
            "count": len(ipos)
        })
    except Exception as e:
        logger.error(f"Error in get_upcoming_ipos: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

def scrape_chittorgarh_current():
    """Scrape current/open IPOs from Chittorgarh"""
    url = "https://www.chittorgarh.com/ipo/ipo_calendar.asp"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
    }
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, 'html.parser')
    ipos = []

    # Log all h2 headings for debugging
    headings = [h.get_text(strip=True) for h in soup.find_all('h2')]
    logger.info(f"All h2 headings: {headings}")

    tables = soup.find_all('table', class_='table')
    logger.info(f"Found {len(tables)} tables with class 'table'")

    for i, table in enumerate(tables):
        prev_heading = table.find_previous('h2')
        prev_text = prev_heading.get_text().lower() if prev_heading else "none"
        logger.info(f"Table {i}: previous h2='{prev_text}'")
        
        # Broader matching for current/open IPOs
        if prev_heading and any(word in prev_heading.get_text().lower() for word in ['current', 'open', 'ongoing', 'live']):
            logger.info(f"Processing CURRENT table after: {prev_heading.get_text()}")
            rows = table.find_all('tr')[1:]  # Skip header
            for j, row in enumerate(rows[:10]):  # Max 10 IPOs
                cols = row.find_all('td')
                if len(cols) >= 5:
                    try:
                        company = cols[0].get_text(strip=True)
                        price_text = cols[1].get_text(strip=True)
                        open_date = cols[2].get_text(strip=True)
                        close_date = cols[3].get_text(strip=True)
                        lot_size = cols[4].get_text(strip=True)

                        # Parse price range
                        price_match = re.search(r'(\d+)\s*-\s*(\d+)', price_text)
                        price_low = int(price_match.group(1)) if price_match else 0
                        price_high = int(price_match.group(2)) if price_match else 0

                        # Parse lot size
                        lot_match = re.search(r'(\d+)', lot_size)
                        lot = int(lot_match.group(1)) if lot_match else 0

                        ipo = {
                            "company": company,
                            "priceLow": price_low,
                            "priceHigh": price_high,
                            "openDate": open_date,
                            "closeDate": close_date,
                            "lotSize": lot,
                            "status": "open",
                            "exchange": "NSE+BSE",
                            "type": "Mainboard"
                        }
                        ipos.append(ipo)
                        logger.info(f"Parsed current IPO: {company}")
                    except Exception as e:
                        logger.error(f"Error parsing row {j}: {e}")
                        continue
                else:
                    logger.info(f"Skipping row {j}: only {len(cols)} cols (need >=5)")

    logger.info(f"Found {len(ipos)} current IPOs")
    return ipos

def scrape_chittorgarh_upcoming():
    """Scrape upcoming IPOs from Chittorgarh"""
    url = "https://www.chittorgarh.com/ipo/ipo_calendar.asp"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
    }
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, 'html.parser')
    ipos = []

    tables = soup.find_all('table', class_='table')

    for i, table in enumerate(tables):
        prev_heading = table.find_previous('h2')
        prev_text = prev_heading.get_text().lower() if prev_heading else "none"
        
        # Broader matching for upcoming
        if prev_heading and any(word in prev_heading.get_text().lower() for word in ['upcoming', 'forthcoming', 'next']):
            logger.info(f"Processing UPCOMING table after: {prev_heading.get_text()}")
            rows = table.find_all('tr')[1:]  # Skip header
            for j, row in enumerate(rows[:15]):  # Max 15 upcoming
                cols = row.find_all('td')
                if len(cols) >= 4:
                    try:
                        company = cols[0].get_text(strip=True)
                        price_text = cols[1].get_text(strip=True)
                        open_date = cols[2].get_text(strip=True)
                        close_date = cols[3].get_text(strip=True) if len(cols) > 3 else "TBA"

                        # Parse price range
                        price_match = re.search(r'(\d+)\s*-\s*(\d+)', price_text)
                        price_low = int(price_match.group(1)) if price_match else 0
                        price_high = int(price_match.group(2)) if price_match else 0

                        ipo = {
                            "company": company,
                            "priceLow": price_low,
                            "priceHigh": price_high,
                            "openDate": open_date,
                            "closeDate": close_date,
                            "lotSize": 0,
                            "status": "upcoming",
                            "exchange": "NSE+BSE",
                            "type": "Mainboard"
                        }
                        ipos.append(ipo)
                        logger.info(f"Parsed upcoming IPO: {company}")
                    except Exception as e:
                        logger.error(f"Error parsing row {j}: {e}")
                        continue

    logger.info(f"Found {len(ipos)} upcoming IPOs")
    return ipos

if __name__ == '__main__':
    # For local testing
    app.run(debug=True, host='0.0.0.0', port=5000)
