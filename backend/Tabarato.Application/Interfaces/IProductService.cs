using Tabarato.Application.Dtos;
using Tabarato.Domain.Resources;

namespace Tabarato.Application.Interfaces;

public interface IProductService
{
    Task<PagedResponse<ProductResponse>> SearchProducts(string query, int page);
    Task<CartOfferResponse?> CalculateCheapestStoreAsync(Dictionary<int, int> products);
    Task<CartOfferResponse[]> CalculateCheapestItemsAsync(Dictionary<int, int> products);
    Task<CartOfferWithDistanceResponse?> CalculateCheapestStoreWithDistanceAsync(Dictionary<int, int> products, Dictionary<int, DistanceInfo> distances);
    Task<CartOfferWithDistanceResponse[]> CalculateCheapestStoresRankingWithDistanceAsync(Dictionary<int, int> products, Dictionary<int, DistanceInfo> distances);
}