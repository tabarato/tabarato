namespace Tabarato.Application.Dtos;

public class StoreCartWithDistanceResponse : StoreCartResponse
{
    public DistanceInfo? DistanceInfo { get; set; }

    private StoreCartWithDistanceResponse(string storeName, List<CartItemResponse> items, DistanceInfo? distanceInfo) : base(storeName, items)
    {
        DistanceInfo = distanceInfo;
    }

    public new static StoreCartWithDistanceResponse Create(IGrouping<int, StoreProductDto> g)
    {
        var store = g.First().Store;
        var storeName = store.Name;
        var distanceInfo = store.DistanceInfo;
        var items = g.Select(CartItemResponse.Create).ToList();
        
        return new StoreCartWithDistanceResponse(storeName, items, distanceInfo);
    }
}