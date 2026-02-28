from flask import Flask, jsonify
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import re
import logging

app = Flask(__name__)
CORS(app)

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
        logger.error(f"Error in get_all_ipos: {str(e)}")
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
        logger.error(f"Error in get_current_ipos: {str(e)}")
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
        logger.error(f"Error in get_upcoming_ipos: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

def get_session():
    """Create a session with proper headers"""
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    })
    return session

def scrape_chittorgarh_current():
    """Scrape current/open IPOs from Chittorgarh"""
    url = "https://www.chittorgarh.com/ipo/ipo_calendar.asp"
    
    try:
        session = get_session()
        response = session.get(url, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        ipos = []
        
        # Find all tables
        tables = soup.find_all('table', class_=re.compile('table'))
        logger.info(f"Found {len(tables)} tables")
        
        for table in tables:
            # Get the heading before this table
            prev_heading = table.find_previous(['h2', 'h3', 'h4', 'thead'])
            
            if prev_heading:
                heading_text = prev_heading.get_text(strip=True).lower()
                logger.info(f"Processing table with heading: {heading_text}")
                
                # Check if this is a current/open IPOs section
                if any(keyword in heading_text for keyword in ['current', 'open', 'active', 'live']):
                    rows = table.find_all('tr')[1:]  # Skip header row
                    
                    for row in rows[:15]:  # Max 15 IPOs
                        cols = row.find_all('td')
                        
                        if len(cols) >= 4:
                            try:
                                company = cols[0].get_text(strip=True)
                                price_text = cols[1].get_text(strip=True)
                                open_date = cols[2].get_text(strip=True)
                                close_date = cols[3].get_text(strip=True) if len(cols) > 3 else "TBA"
                                lot_size = cols[4].get_text(strip=True) if len(cols) > 4 else "0"
                                
                                # Skip empty rows
                                if not company or company == "":
                                    continue
                                
                                # Parse price range
                                price_low, price_high = parse_price(price_text)
                                
                                # Parse lot size
                                lot = parse_lot_size(lot_size)
                                
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
                                logger.info(f"Added IPO: {company}")
                            
                            except Exception as e:
                                logger.warning(f"Error parsing row: {e}")
                                continue
        
        logger.info(f"Total current IPOs found: {len(ipos)}")
        return ipos
    
    except Exception as e:
        logger.error(f"Error scraping current IPOs: {str(e)}")
        raise

def scrape_chittorgarh_upcoming():
    """Scrape upcoming IPOs from Chittorgarh"""
    url = "https://www.chittorgarh.com/ipo/ipo_calendar.asp"
    
    try:
        session = get_session()
        response = session.get(url, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        ipos = []
        
        tables = soup.find_all('table', class_=re.compile('table'))
        logger.info(f"Found {len(tables)} tables")
        
        for table in tables:
            # Get the heading before this table
            prev_heading = table.find_previous(['h2', 'h3', 'h4', 'thead'])
            
            if prev_heading:
                heading_text = prev_heading.get_text(strip=True).lower()
                logger.info(f"Processing table with heading: {heading_text}")
                
                # Check if this is an upcoming IPOs section
                if 'upcoming' in heading_text or 'scheduled' in heading_text:
                    rows = table.find_all('tr')[1:]  # Skip header row
                    
                    for row in rows[:20]:  # Max 20 upcoming
                        cols = row.find_all('td')
                        
                        if len(cols) >= 3:
                            try:
                                company = cols[0].get_text(strip=True)
                                price_text = cols[1].get_text(strip=True)
                                open_date = cols[2].get_text(strip=True)
                                close_date = cols[3].get_text(strip=True) if len(cols) > 3 else "TBA"
                                
                                # Skip empty rows
                                if not company or company == "":
                                    continue
                                
                                # Parse price range
                                price_low, price_high = parse_price(price_text)
                                
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
                                logger.info(f"Added upcoming IPO: {company}")
                            
                            except Exception as e:
                                logger.warning(f"Error parsing row: {e}")
                                continue
        
        logger.info(f"Total upcoming IPOs found: {len(ipos)}")
        return ipos
    
    except Exception as e:
        logger.error(f"Error scraping upcoming IPOs: {str(e)}")
        raise

def parse_price(price_text):
    """Parse price range from text"""
    try:
        # Try different price formats
        price_match = re.search(r'(\d+)\s*-\s*(\d+)', price_text)
        if price_match:
            return int(price_match.group(1)), int(price_match.group(2))
        
        # Single price
        single_price = re.search(r'(\d+)', price_text)
        if single_price:
            price = int(single_price.group(1))
            return price, price
        
        return 0, 0
    except Exception as e:
        logger.warning(f"Error parsing price: {e}")
        return 0, 0

def parse_lot_size(lot_text):
    """Parse lot size from text"""
    try:
        lot_match = re.search(r'(\d+)', lot_text)
        return int(lot_match.group(1)) if lot_match else 0
    except Exception as e:
        logger.warning(f"Error parsing lot size: {e}")
        return 0

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
