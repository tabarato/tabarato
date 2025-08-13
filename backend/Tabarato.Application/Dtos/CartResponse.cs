namespace Tabarato.Application.Dtos;

public class CartResponse
{
    /// <summary>
    /// Best overall store for the entire cart (lowest total cost).
    /// </summary>
    public CartOfferResponse? BestSingleStore { get; set; }

    /// <summary>
    /// Best combination of stores by selecting the cheapest option for each item.
    /// </summary>
    public CartOfferResponse[] BestPerItemStores { get; set; }

    /// <summary>
    /// Best single store considering both cost and travel distance/time.
    /// </summary>
    public CartOfferWithDistanceResponse? BestSingleStoreWithDistance { get; set; }

    /// <summary>
    /// Best per-item store combination considering both cost and travel distance/time.
    /// </summary>
    public CartOfferWithDistanceResponse[] BestPerItemStoresWithDistance { get; set; }
    
    public CartResponse(
        CartOfferResponse? bestSingleStore,
        CartOfferResponse[] bestPerItemStores,
        CartOfferWithDistanceResponse? bestSingleStoreWithDistance,
        CartOfferWithDistanceResponse[] bestPerItemStoresWithDistance)
    {
        BestSingleStore = bestSingleStore;
        BestPerItemStores = bestPerItemStores;
        BestSingleStoreWithDistance = bestSingleStoreWithDistance;
        BestPerItemStoresWithDistance = bestPerItemStoresWithDistance;
    }
}