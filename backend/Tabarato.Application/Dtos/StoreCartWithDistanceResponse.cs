namespace Tabarato.Application.Dtos;

public class StoreCartWithDistanceResponse : StoreCartResponse
{
    public DistanceInfo DistanceInfo { get; set; }

    private StoreCartWithDistanceResponse(string storeName, List<CartItemResponse> items, DistanceInfo distanceInfo) : base(storeName, items)
    {
        DistanceInfo = distanceInfo;
    }

    public static StoreCartWithDistanceResponse Create(IGrouping<int, CartItemResponse> g, DistanceInfo distanceInfo)
    {
        return new StoreCartWithDistanceResponse(g.First().Store.Name, g.ToList(), distanceInfo);
    }
}