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
        "message": "IPO Scraper API",
        "endpoints": {
            "/api/ipos": "Get all IPOs (current + upcoming)",
            "/api/ipos/current": "Get only current/open IPOs",
            "/api/ipos/upcoming": "Get only upcoming IPOs"
        }
    })

@app.route('/api/ipos')
def get_all_ipos():
    """Get all IPOs from multiple sources"""
    try:
        current = scrape_all_current()
        upcoming = scrape_all_upcoming()
        
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
        ipos = scrape_all_current()
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
        ipos = scrape_all_upcoming()
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
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
    })
    return session

def scrape_all_current():
    """Scrape current IPOs from all available sources"""
    ipos = []
    
    # Try Chittorgarh first
    try:
        logger.info("Trying Chittorgarh for current IPOs...")
        ipos = scrape_chittorgarh_current()
        if ipos:
            logger.info(f"Got {len(ipos)} current IPOs from Chittorgarh")
            return ipos
    except Exception as e:
        logger.warning(f"Chittorgarh failed: {e}")
    
    # Try Moneycontrol as fallback
    try:
        logger.info("Trying Moneycontrol for current IPOs...")
        ipos = scrape_moneycontrol_current()
        if ipos:
            logger.info(f"Got {len(ipos)} current IPOs from Moneycontrol")
            return ipos
    except Exception as e:
        logger.warning(f"Moneycontrol failed: {e}")
    
    # Try BSE India as final fallback
    try:
        logger.info("Trying BSE India for current IPOs...")
        ipos = scrape_bse_current()
        if ipos:
            logger.info(f"Got {len(ipos)} current IPOs from BSE India")
            return ipos
    except Exception as e:
        logger.warning(f"BSE India failed: {e}")
    
    return ipos

def scrape_all_upcoming():
    """Scrape upcoming IPOs from all available sources"""
    ipos = []
    
    # Try Chittorgarh first
    try:
        logger.info("Trying Chittorgarh for upcoming IPOs...")
        ipos = scrape_chittorgarh_upcoming()
        if ipos:
            logger.info(f"Got {len(ipos)} upcoming IPOs from Chittorgarh")
            return ipos
    except Exception as e:
        logger.warning(f"Chittorgarh failed: {e}")
    
    # Try Moneycontrol as fallback
    try:
        logger.info("Trying Moneycontrol for upcoming IPOs...")
        ipos = scrape_moneycontrol_upcoming()
        if ipos:
            logger.info(f"Got {len(ipos)} upcoming IPOs from Moneycontrol")
            return ipos
    except Exception as e:
        logger.warning(f"Moneycontrol failed: {e}")
    
    # Try BSE India as final fallback
    try:
        logger.info("Trying BSE India for upcoming IPOs...")
        ipos = scrape_bse_upcoming()
        if ipos:
            logger.info(f"Got {len(ipos)} upcoming IPOs from BSE India")
            return ipos
    except Exception as e:
        logger.warning(f"BSE India failed: {e}")
    
    return ipos

# ==================== CHITTORGARH ====================
def scrape_chittorgarh_current():
    """Scrape current/open IPOs from Chittorgarh"""
    url = "https://www.chittorgarh.com/ipo/ipo_calendar.asp"
    
    try:
        session = get_session()
        response = session.get(url, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        ipos = []
        
        tables = soup.find_all('table')
        logger.info(f"Found {len(tables)} tables in Chittorgarh")
        
        for table_idx, table in enumerate(tables):
            try:
                rows = table.find_all('tr')
                if len(rows) < 2:
                    continue
                
                table_text = table.get_text().lower()
                if not any(keyword in table_text for keyword in ['ipo', 'company', 'price', 'date']):
                    continue
                
                for row_idx, row in enumerate(rows[1:]):
                    if row_idx >= 15:
                        break
                    
                    cols = row.find_all(['td', 'th'])
                    if len(cols) >= 3:
                        try:
                            company = cols[0].get_text(strip=True)
                            price_text = cols[1].get_text(strip=True)
                            open_date = cols[2].get_text(strip=True)
                            close_date = cols[3].get_text(strip=True) if len(cols) > 3 else "TBA"
                            
                            if not company or len(company) < 2 or company.lower() in ['company', 'name']:
                                continue
                            
                            price_low, price_high = parse_price(price_text)
                            
                            ipo = {
                                "company": company,
                                "priceLow": price_low,
                                "priceHigh": price_high,
                                "openDate": open_date,
                                "closeDate": close_date,
                                "status": "open",
                                "source": "chittorgarh"
                            }
                            ipos.append(ipo)
                        except Exception as e:
                            logger.warning(f"Error parsing row: {e}")
                            continue
            except Exception as e:
                logger.warning(f"Error processing table: {e}")
                continue
        
        return ipos
    except Exception as e:
        logger.error(f"Error scraping Chittorgarh current: {e}")
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
        
        tables = soup.find_all('table')
        
        for table_idx, table in enumerate(tables):
            try:
                rows = table.find_all('tr')
                if len(rows) < 2:
                    continue
                
                table_text = table.get_text().lower()
                if not any(keyword in table_text for keyword in ['ipo', 'company', 'upcoming']):
                    continue
                
                for row_idx, row in enumerate(rows[1:]):
                    if row_idx >= 20:
                        break
                    
                    cols = row.find_all(['td', 'th'])
                    if len(cols) >= 3:
                        try:
                            company = cols[0].get_text(strip=True)
                            price_text = cols[1].get_text(strip=True)
                            open_date = cols[2].get_text(strip=True)
                            
                            if not company or len(company) < 2:
                                continue
                            
                            price_low, price_high = parse_price(price_text)
                            
                            ipo = {
                                "company": company,
                                "priceLow": price_low,
                                "priceHigh": price_high,
                                "openDate": open_date,
                                "status": "upcoming",
                                "source": "chittorgarh"
                            }
                            ipos.append(ipo)
                        except Exception as e:
                            logger.warning(f"Error parsing row: {e}")
                            continue
            except Exception as e:
                logger.warning(f"Error processing table: {e}")
                continue
        
        return ipos
    except Exception as e:
        logger.error(f"Error scraping Chittorgarh upcoming: {e}")
        raise

# ==================== MONEYCONTROL ====================
def scrape_moneycontrol_current():
    """Scrape current IPOs from Moneycontrol"""
    url = "https://www.moneycontrol.com/ipo/"
    
    try:
        session = get_session()
        response = session.get(url, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        ipos = []
        
        # Look for tables with IPO data
        tables = soup.find_all('table')
        
        for table in tables:
            try:
                rows = table.find_all('tr')
                if len(rows) < 2:
                    continue
                
                for row in rows[1:]:
                    cols = row.find_all(['td', 'th'])
                    if len(cols) >= 2:
                        try:
                            company = cols[0].get_text(strip=True)
                            
                            if not company or len(company) < 2:
                                continue
                            
                            # Try to extract price and date from other columns
                            price_text = cols[1].get_text(strip=True) if len(cols) > 1 else ""
                            date_text = cols[2].get_text(strip=True) if len(cols) > 2 else ""
                            
                            price_low, price_high = parse_price(price_text)
                            
                            ipo = {
                                "company": company,
                                "priceLow": price_low,
                                "priceHigh": price_high,
                                "openDate": date_text,
                                "status": "open",
                                "source": "moneycontrol"
                            }
                            ipos.append(ipo)
                        except Exception as e:
                            logger.warning(f"Error parsing Moneycontrol row: {e}")
                            continue
            except Exception as e:
                logger.warning(f"Error processing Moneycontrol table: {e}")
                continue
        
        return ipos
    except Exception as e:
        logger.error(f"Error scraping Moneycontrol current: {e}")
        raise

def scrape_moneycontrol_upcoming():
    """Scrape upcoming IPOs from Moneycontrol"""
    url = "https://www.moneycontrol.com/ipo/"
    
    try:
        session = get_session()
        response = session.get(url, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        ipos = []
        
        # Similar logic as current, just filtering for upcoming
        tables = soup.find_all('table')
        
        for table in tables:
            try:
                rows = table.find_all('tr')
                if len(rows) < 2:
                    continue
                
                table_text = table.get_text().lower()
                if 'upcoming' not in table_text:
                    continue
                
                for row in rows[1:]:
                    cols = row.find_all(['td', 'th'])
                    if len(cols) >= 2:
                        try:
                            company = cols[0].get_text(strip=True)
                            
                            if not company or len(company) < 2:
                                continue
                            
                            price_text = cols[1].get_text(strip=True) if len(cols) > 1 else ""
                            date_text = cols[2].get_text(strip=True) if len(cols) > 2 else ""
                            
                            price_low, price_high = parse_price(price_text)
                            
                            ipo = {
                                "company": company,
                                "priceLow": price_low,
                                "priceHigh": price_high,
                                "openDate": date_text,
                                "status": "upcoming",
                                "source": "moneycontrol"
                            }
                            ipos.append(ipo)
                        except Exception as e:
                            logger.warning(f"Error parsing Moneycontrol upcoming: {e}")
                            continue
            except Exception as e:
                logger.warning(f"Error processing Moneycontrol table: {e}")
                continue
        
        return ipos
    except Exception as e:
        logger.error(f"Error scraping Moneycontrol upcoming: {e}")
        raise

# ==================== BSE INDIA ====================
def scrape_bse_current():
    """Scrape current IPOs from BSE India"""
    url = "https://www.bseindia.com/markets/issuers/newipos.aspx"
    
    try:
        session = get_session()
        response = session.get(url, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        ipos = []
        
        tables = soup.find_all('table')
        
        for table in tables:
            try:
                rows = table.find_all('tr')
                if len(rows) < 2:
                    continue
                
                for row in rows[1:]:
                    cols = row.find_all(['td', 'th'])
                    if len(cols) >= 2:
                        try:
                            company = cols[0].get_text(strip=True)
                            
                            if not company or len(company) < 2:
                                continue
                            
                            price_text = cols[1].get_text(strip=True) if len(cols) > 1 else ""
                            date_text = cols[2].get_text(strip=True) if len(cols) > 2 else ""
                            
                            price_low, price_high = parse_price(price_text)
                            
                            ipo = {
                                "company": company,
                                "priceLow": price_low,
                                "priceHigh": price_high,
                                "openDate": date_text,
                                "status": "open",
                                "source": "bseindia"
                            }
                            ipos.append(ipo)
                        except Exception as e:
                            logger.warning(f"Error parsing BSE row: {e}")
                            continue
            except Exception as e:
                logger.warning(f"Error processing BSE table: {e}")
                continue
        
        return ipos
    except Exception as e:
        logger.error(f"Error scraping BSE current: {e}")
        raise

def scrape_bse_upcoming():
    """Scrape upcoming IPOs from BSE India"""
    url = "https://www.bseindia.com/markets/issuers/newipos.aspx"
    
    try:
        session = get_session()
        response = session.get(url, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        ipos = []
        
        tables = soup.find_all('table')
        
        for table in tables:
            try:
                rows = table.find_all('tr')
                if len(rows) < 2:
                    continue
                
                for row in rows[1:]:
                    cols = row.find_all(['td', 'th'])
                    if len(cols) >= 2:
                        try:
                            company = cols[0].get_text(strip=True)
                            
                            if not company or len(company) < 2:
                                continue
                            
                            price_text = cols[1].get_text(strip=True) if len(cols) > 1 else ""
                            date_text = cols[2].get_text(strip=True) if len(cols) > 2 else ""
                            
                            price_low, price_high = parse_price(price_text)
                            
                            ipo = {
                                "company": company,
                                "priceLow": price_low,
                                "priceHigh": price_high,
                                "openDate": date_text,
                                "status": "upcoming",
                                "source": "bseindia"
                            }
                            ipos.append(ipo)
                        except Exception as e:
                            logger.warning(f"Error parsing BSE upcoming: {e}")
                            continue
            except Exception as e:
                logger.warning(f"Error processing BSE table: {e}")
                continue
        
        return ipos
    except Exception as e:
        logger.error(f"Error scraping BSE upcoming: {e}")
        raise

# ==================== UTILITIES ====================
def parse_price(price_text):
    """Parse price range from text"""
    try:
        if not price_text:
            return 0, 0
        
        # Try to find range (e.g., "₹100 - ₹200" or "100-200")
        price_match = re.search(r'(\d+)\s*[-–to]\s*(\d+)', price_text)
        if price_match:
            return int(price_match.group(1)), int(price_match.group(2))
        
        # Single price
        single_price = re.search(r'(\d+)', price_text)
        if single_price:
            price = int(single_price.group(1))
            return price, price
        
        return 0, 0
    except Exception as e:
        logger.warning(f"Error parsing price '{price_text}': {e}")
        return 0, 0

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
