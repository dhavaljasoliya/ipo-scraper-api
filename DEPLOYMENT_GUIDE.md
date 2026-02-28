# 🚀 IPO Scraper API - Deployment Guide

## What This Does

This API scrapes Chittorgarh.com for live IPO data and provides a clean JSON API for your iOS app.

**Endpoints:**
- `GET /api/ipos` - All IPOs (current + upcoming)
- `GET /api/ipos/current` - Only open IPOs
- `GET /api/ipos/upcoming` - Only upcoming IPOs

---

## 📦 Files Included

```
ipo_scraper_api/
├── app.py              # Flask API with scraping logic
├── requirements.txt    # Python dependencies
├── Procfile           # For Heroku/Railway deployment
└── README.md          # This file
```

---

## 🚀 Deploy to Railway (FREE - Recommended)

Railway gives you **500 hours/month FREE** (enough for hobby projects).

### Step 1: Create Railway Account
1. Go to https://railway.app
2. Sign up with GitHub (free)

### Step 2: Deploy
1. Click **"New Project"**
2. Select **"Deploy from GitHub repo"**
3. Upload these files to a new GitHub repo
4. Connect the repo to Railway
5. Railway will auto-detect Flask and deploy!

### Step 3: Get Your API URL
After deployment, Railway gives you a URL like:
```
https://your-app.railway.app
```

**Test it:**
```
https://your-app.railway.app/api/ipos
```

You should see JSON with IPO data! 🎉

---

## 🚀 Alternative: Deploy to Render (FREE)

Render also has a free tier.

### Steps:
1. Go to https://render.com
2. Sign up (free)
3. Click **"New +"** → **"Web Service"**
4. Connect your GitHub repo
5. Settings:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app`
6. Click **"Create Web Service"**

Your API will be at:
```
https://your-app.onrender.com
```

---

## 🧪 Test Locally First

Before deploying, test on your computer:

### 1. Install Python 3.8+
```bash
python3 --version
```

### 2. Install dependencies
```bash
cd ipo_scraper_api
pip install -r requirements.txt
```

### 3. Run the API
```bash
python app.py
```

### 4. Test in browser
Open: http://localhost:5000/api/ipos

You should see JSON with IPO data!

---

## 📱 Update Your iOS App

Once deployed, update `NetworkService.swift`:

```swift
func fetchLiveIPOs() async -> (current: [IPO], upcoming: [IPO]) {
    // Replace with your Railway/Render URL
    guard let url = URL(string: "https://your-app.railway.app/api/ipos") else {
        return ([], [])
    }
    
    do {
        let (data, _) = try await URLSession.shared.data(from: url)
        let json = try JSONDecoder().decode(IPOResponse.self, from: data)
        
        // Parse JSON to IPO objects
        let current = json.data.current.map { parseAPIIPO($0, status: .open) }
        let upcoming = json.data.upcoming.map { parseAPIIPO($0, status: .upcoming) }
        
        return (current, upcoming)
    } catch {
        print("❌ IPO API error: \(error)")
        return ([], [])
    }
}
```

---

## 🔧 API Response Format

### GET /api/ipos
```json
{
  "success": true,
  "timestamp": "2026-02-22T16:30:00",
  "data": {
    "current": [
      {
        "company": "Hexaware Technologies",
        "priceLow": 650,
        "priceHigh": 700,
        "openDate": "19-Feb-2026",
        "closeDate": "21-Feb-2026",
        "lotSize": 20,
        "status": "open",
        "exchange": "NSE+BSE",
        "type": "Mainboard"
      }
    ],
    "upcoming": [
      {
        "company": "Go Digit Insurance",
        "priceLow": 280,
        "priceHigh": 295,
        "openDate": "27-Feb-2026",
        "closeDate": "01-Mar-2026",
        "lotSize": 50,
        "status": "upcoming",
        "exchange": "NSE+BSE",
        "type": "Mainboard"
      }
    ],
    "total": 2
  }
}
```

---

## 💰 Cost

**Railway:** 500 hours/month FREE (≈ 17 days)
**Render:** 750 hours/month FREE (≈ 31 days if not 24/7)

Both are **FREE** for hobby projects! 🎉

---

## 🛠️ Troubleshooting

### API returns empty array
- Check if Chittorgarh changed their HTML structure
- View the website manually to verify IPO data exists
- Check Railway/Render logs for errors

### "CORS error" in iOS app
- The API already has `flask-cors` enabled
- Make sure you're calling the correct URL

### API is slow
- First request might be slow (cold start)
- Subsequent requests are fast (~1-2 seconds)

---

## 📊 Monitoring

### Railway Dashboard
- See logs in real-time
- Monitor uptime
- Check API usage

### Test Endpoint
```bash
curl https://your-app.railway.app/api/ipos
```

---

## 🎯 Next Steps

1. **Deploy the API** to Railway/Render
2. **Get your API URL** from the dashboard
3. **Update your iOS app** with the URL
4. **Test** by pulling down on IPO tab
5. **Celebrate** 🎉 - You now have LIVE IPO data!

---

**Questions?** The API code is simple Python - you can modify the scraping logic if Chittorgarh changes their website.
