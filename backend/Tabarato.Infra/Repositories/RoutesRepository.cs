using System.Globalization;
using System.Net.Http.Json;
using Tabarato.Domain.Repositories;
using Tabarato.Domain.Resources;

namespace Tabarato.Infra.Repositories;

public class RoutesRepository(HttpClient httpClient) : IRoutesRepository
{
    public async Task<DistanceInfo[]> GetSeparateIntermediateRoutesAsync(
        string origin,
        string destination,
        IEnumerable<string> intermediates,
        TravelMode travelMode)
    {
        var results = new List<DistanceInfo>();

        foreach (var intermediate in intermediates)
        {
            var data = new
            {
                origin = new { address = origin },
                destination = new { address = destination },
                intermediates = new[] { new { address = intermediate } },
                travelMode = GetTravelMode(travelMode),
                optimizeWaypointOrder = false
            };

            var request = new HttpRequestMessage(HttpMethod.Post, "/directions/v2:computeRoutes")
            {
                Content = JsonContent.Create(data),
                Headers =
                {
                    { "X-Goog-FieldMask", "routes,geocodingResults.intermediates.intermediateWaypointRequestIndex" }
                }
            };
            var response = await httpClient.SendAsync(request);
            if (!response.IsSuccessStatusCode)
                throw new Exception($"Error {response.StatusCode}: {await response.Content.ReadAsStringAsync()}");

            var json = await response.Content.ReadFromJsonAsync<GoogleRoutesResponse>();
            var routeData = json?.Routes?.FirstOrDefault();

            if (routeData == null)
                throw new Exception($"Route not found for intermediate: {intermediate}");

            var distanceInfo = ExtractDistancesAndDurations(routeData)[0];

            results.Add(new DistanceInfo
            {
                DistanceKm = Convert.ToDecimal(distanceInfo.DistanceKm),
                DurationMin = Convert.ToInt32(distanceInfo.DurationMin)
            });
        }

        return results.ToArray();
    }

    private static string GetTravelMode(TravelMode travelMode)
    {
        switch (travelMode)
        {
            case TravelMode.Bicycle: return "BICYCLE";
            case TravelMode.Car: return "DRIVE";
            case TravelMode.Motorcycle: return "TWO_WHEELER";
            case TravelMode.Walking: return "WALK";
        }

        return string.Empty;
    }

    private static List<DistanceInfo> ExtractDistancesAndDurations(RouteData routeData)
    {
        if (routeData.Legs == null || routeData.Legs.Count == 0)
            throw new ArgumentException("Invalid or missing route data", nameof(routeData));

        return routeData.Legs.Select(leg =>
        {
            var distanceKm = (leg.DistanceMeters / 1000).ToString("0.00", CultureInfo.InvariantCulture);

            if (!leg.Duration.EndsWith('s') || !int.TryParse(leg.Duration.TrimEnd('s'), out var durationSeconds))
                throw new FormatException($"Invalid duration format: {leg.Duration}");

            var durationMin = Math.Round(durationSeconds / 60.0).ToString("0");

            return new DistanceInfo
            {
                DistanceKm = Convert.ToDecimal(distanceKm, CultureInfo.InvariantCulture),
                DurationMin = Convert.ToInt32(durationMin, CultureInfo.InvariantCulture)
            };
        }).ToList();
    }
}

public class GoogleRoutesResponse
{
    public List<RouteData>? Routes { get; set; }
}

public class RouteData
{
    public List<RouteLeg> Legs { get; set; } = [];
}

public class RouteLeg
{
    public double DistanceMeters { get; set; }
    public string Duration { get; set; } = string.Empty;
}
