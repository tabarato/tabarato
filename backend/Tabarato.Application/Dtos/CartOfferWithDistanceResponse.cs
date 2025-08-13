using Tabarato.Domain.Resources;

namespace Tabarato.Application.Dtos;

public class CartOfferWithDistanceResponse(string storeName, List<CartOfferItemResponse> items, decimal totalCost, DistanceInfo distanceInfo) : CartOfferResponse(storeName, items, totalCost)
{
    public DistanceInfo DistanceInfo { get; set; } = distanceInfo;

    public static CartOfferWithDistanceResponse Create(IGrouping<int, CartOfferItemResponse> g, DistanceInfo distanceInfo)
    {
        return new CartOfferWithDistanceResponse(g.First().Store.Name, g.ToList(), g.Sum(i => i.TotalPrice), distanceInfo);
    }
}
