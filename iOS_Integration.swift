// Add this to your NetworkService.swift

// MARK: - IPO API Response Models
struct IPOAPIResponse: Codable {
    let success: Bool
    let timestamp: String
    let data: IPOAPIData
}

struct IPOAPIData: Codable {
    let current: [IPOAPIItem]
    let upcoming: [IPOAPIItem]
    let total: Int
}

struct IPOAPIItem: Codable {
    let company: String
    let priceLow: Int
    let priceHigh: Int
    let openDate: String
    let closeDate: String
    let lotSize: Int
    let status: String
    let exchange: String
    let type: String
}

// MARK: - Fetch IPOs from Custom API
func fetchLiveIPOs() async -> (current: [IPO], upcoming: [IPO]) {
    print("📊 Fetching IPO data from custom API...")
    
    // TODO: Replace with your Railway/Render URL after deployment
    let apiURL = "https://your-app.railway.app/api/ipos"
    
    guard let url = URL(string: apiURL) else {
        print("❌ Invalid API URL")
        return ([], [])
    }
    
    do {
        let (data, response) = try await URLSession.shared.data(from: url)
        
        guard let httpResp = response as? HTTPURLResponse else {
            print("❌ No HTTP response")
            return ([], [])
        }
        
        print("📡 API HTTP \(httpResp.statusCode)")
        
        guard httpResp.statusCode == 200 else {
            print("❌ API returned HTTP \(httpResp.statusCode)")
            return ([], [])
        }
        
        let decoder = JSONDecoder()
        let apiResponse = try decoder.decode(IPOAPIResponse.self, from: data)
        
        guard apiResponse.success else {
            print("❌ API returned success=false")
            return ([], [])
        }
        
        // Convert API items to IPO objects
        let currentIPOs = apiResponse.data.current.map { item in
            IPO(
                id: item.company.replacingOccurrences(of: " ", with: "_"),
                company: item.company,
                exchange: item.exchange,
                ipoType: item.type,
                status: .open,
                openDate: item.openDate,
                closeDate: item.closeDate,
                listingDate: "--",
                priceLow: Double(item.priceLow),
                priceHigh: Double(item.priceHigh),
                lotSize: item.lotSize,
                issueSize: 0,
                gmp: 0,
                subsTimes: 0,
                category: "N/A"
            )
        }
        
        let upcomingIPOs = apiResponse.data.upcoming.map { item in
            IPO(
                id: item.company.replacingOccurrences(of: " ", with: "_"),
                company: item.company,
                exchange: item.exchange,
                ipoType: item.type,
                status: .upcoming,
                openDate: item.openDate,
                closeDate: item.closeDate,
                listingDate: "--",
                priceLow: Double(item.priceLow),
                priceHigh: Double(item.priceHigh),
                lotSize: item.lotSize,
                issueSize: 0,
                gmp: 0,
                subsTimes: 0,
                category: "N/A"
            )
        }
        
        print("✅ IPO API: \(currentIPOs.count) open, \(upcomingIPOs.count) upcoming (LIVE)")
        return (currentIPOs, upcomingIPOs)
        
    } catch let decodingError as DecodingError {
        print("❌ JSON decode error: \(decodingError)")
        return ([], [])
    } catch {
        print("❌ IPO API error: \(error.localizedDescription)")
        return ([], [])
    }
}

// MARK: - Alternative: Fetch from specific endpoint
func fetchCurrentIPOs() async -> [IPO] {
    guard let url = URL(string: "https://your-app.railway.app/api/ipos/current") else { return [] }
    
    do {
        let (data, _) = try await URLSession.shared.data(from: url)
        
        struct CurrentIPOResponse: Codable {
            let success: Bool
            let data: [IPOAPIItem]
            let count: Int
        }
        
        let response = try JSONDecoder().decode(CurrentIPOResponse.self, from: data)
        
        return response.data.map { item in
            IPO(
                id: item.company.replacingOccurrences(of: " ", with: "_"),
                company: item.company,
                exchange: item.exchange,
                ipoType: item.type,
                status: .open,
                openDate: item.openDate,
                closeDate: item.closeDate,
                listingDate: "--",
                priceLow: Double(item.priceLow),
                priceHigh: Double(item.priceHigh),
                lotSize: item.lotSize,
                issueSize: 0,
                gmp: 0,
                subsTimes: 0,
                category: "N/A"
            )
        }
    } catch {
        print("❌ Current IPOs error: \(error)")
        return []
    }
}
