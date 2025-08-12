using Tabarato.Application.Dtos;

namespace Tabarato.Application.Interfaces;

public interface IProductService
{
    Task<ProductResponse[]> SearchProducts(string query);
    Task<StoreCartResponse> CalculateCheapestStoreAsync(CalculateCartRequest request);
    Task<IEnumerable<StoreCartResponse>> CalculateCheapestItemsAsync(CalculateCartRequest request);
    Task<StoreCartWithDistanceResponse> CalculateCheapestStoreWithDistanceAsync(CalculateCartWithDistanceRequest request);
    Task<IEnumerable<StoreCartWithDistanceResponse>> CalculateCheapestStoresRankingWithDistanceAsync(CalculateCartWithDistanceRequest request);
}