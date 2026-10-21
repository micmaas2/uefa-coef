import Foundation

// 1-op-1 met stand.json uit de repo. Onbekende velden worden genegeerd.
struct Stand: Codable {
    let generatedAt: String
    let lastMatchDate: String
    let today: String
    let live: Bool
    let focus: Focus
    let window: [Row]
    let todayMatches: [MatchBrief]
    let nextMatches: [MatchBrief]
    let liveMatches: [LiveMatch]
    let ranking: [Row]

    struct Focus: Codable {
        let assoc: String
        let rank: Int
        let rankChange: Int
        let total: Double
        let projected: Double
        let season: Double
        let clubs: Int
        let todayDelta: Double
        let gapUp: Double?
        let gapUpTo: String?
        let gapDown: Double?
        let gapDownTo: String?
    }
    struct Row: Codable, Identifiable {
        var id: String { assoc }
        let assoc: String
        let name: String
        let clubs: Int
        let rank: Int
        let rankChange: Int
        let total: Double
        let projected: Double
        let todayDelta: Double
        let liveDelta: Double
        let playedToday: Bool
    }
    struct MatchBrief: Codable, Identifiable {
        var id: String { date + match }
        let date: String
        let time: String
        let competition: String
        let status: String
        let clock: String
        let match: String
        let club: String
        let delta: Double
    }
    struct LiveMatch: Codable {
        let competition: String
        let clock: String
        let match: String
        let assocs: [String]
    }
}

enum StandLoader {
    static let url = URL(string: "https://raw.githubusercontent.com/micmaas2/uefa-coef/main/stand.json")!
    private static let cacheURL = FileManager.default
        .containerURL(forSecurityApplicationGroupIdentifier: "group.nl.michelmaas.uefacoef")?
        .appendingPathComponent("stand.json")

    static func decoder() -> JSONDecoder {
        let d = JSONDecoder()
        d.keyDecodingStrategy = .convertFromSnakeCase
        return d
    }

    /// Haalt stand.json op; valt terug op de laatste cache (App Group, gedeeld met widget).
    static func load() async throws -> Stand {
        var req = URLRequest(url: url)
        req.cachePolicy = .reloadIgnoringLocalCacheData
        do {
            let (data, _) = try await URLSession.shared.data(for: req)
            let stand = try decoder().decode(Stand.self, from: data)
            if let c = cacheURL { try? data.write(to: c) }
            return stand
        } catch {
            if let c = cacheURL, let data = try? Data(contentsOf: c) {
                return try decoder().decode(Stand.self, from: data)
            }
            throw error
        }
    }
}

extension Double {
    /// 54,062 — Nederlandse notatie, 3 decimalen, met teken als gevraagd
    func coef(signed: Bool = false) -> String {
        let s = String(format: "%.3f", abs(self)).replacingOccurrences(of: ".", with: ",")
        if signed { return (self < 0 ? "−" : "+") + s }
        return (self < 0 ? "−" : "") + s
    }
}

extension String {
    /// "FC Porto 0-1 PSV Eindhoven" → "Porto 0-1 PSV"
    var shortMatch: String {
        let drop = ["FC", "SC", "SL", "RSC", "KAA", "KRC", "CP", "Eindhoven", "Amsterdam", "Rotterdam", "Alkmaar", "Nijmegen"]
        return split(separator: " ").filter { !drop.contains(String($0)) }.joined(separator: " ")
    }
}
