using Tabarato.Application.Dtos;
using Tabarato.Application.Interfaces;
using Tabarato.Domain.Repositories;

namespace Tabarato.Application.Services;

public class ProductService(IProductRepository productRepository, ISearchRepository searchRepository) : IProductService
{
    public async Task<ProductResponse[]> SearchProducts(string query)
    {
        var documents = await searchRepository.SearchProducts(query);

        return documents.Select(d => new ProductResponse(d)).ToArray();
    }

    public async Task<StoreCartResponse?> CalculateCheapestStoreAsync(CalculateCartRequest request)
    {
        var storeProducts = await GetCartItemsResponse(request);
        
        return storeProducts
            .GroupBy(cir => cir.Store.Id)
            .Where(HasAllRequestedProducts(request.Products.Keys))
            .Select(StoreCartResponse.Create)
            .MinBy(scr => scr.TotalCost);
    }
    
    public async Task<IEnumerable<StoreCartResponse>> CalculateCheapestItemsAsync(CalculateCartRequest request)
    {
        var storeProducts = await GetCartItemsResponse(request);
        
        return storeProducts
            .GroupBy(cir => cir.ProductId)
            .Select(g => g.MinBy(sp => sp.Price)!)
            .GroupBy(cir => cir.Store.Id)
            .Select(StoreCartResponse.Create)
            .ToList();
    }

    public async Task<StoreCartWithDistanceResponse?> CalculateCheapestStoreWithDistanceAsync(CalculateCartWithDistanceRequest request)
    {
        var storeProducts = await GetCartItemsResponse(request);
        
        return storeProducts
            .GroupBy(cir => cir.Store.Id)
            .Where(HasAllRequestedProducts(request.Products.Keys))
            .Select(g => StoreCartWithDistanceResponse.Create(g, request.Distances[g.First().Store.Id]))
            .OrderBy(scr => scr.TotalCost)
            .ThenBy(scr => scr.DistanceInfo.DistanceKm)
            .ThenBy(scr => scr.DistanceInfo.DurationMin)
            .FirstOrDefault();
    }

    public async Task<IEnumerable<StoreCartWithDistanceResponse>> CalculateCheapestStoresRankingWithDistanceAsync(CalculateCartWithDistanceRequest request)
    {
        var storeProducts = await GetCartItemsResponse(request);

        return storeProducts
            .GroupBy(cir => cir.ProductId)
            .Select(g => g.MinBy(sp => sp.Price)!)
            .GroupBy(cir => cir.Store.Id)
            .Select(g => StoreCartWithDistanceResponse.Create(g, request.Distances[g.First().Store.Id]))
            .ToList();
    }
    
    private async Task<IEnumerable<CartItemResponse>> GetCartItemsResponse(CalculateCartRequest request)
    {
        var storeProducts = await productRepository.GetStoreProductsByProductIds(request.Products.Keys);
        return storeProducts.Select(sp => CartItemResponse.Create(sp, request.Products[sp.ProductId]));
    }

    private static Func<IGrouping<int, CartItemResponse>, bool> HasAllRequestedProducts(IEnumerable<int> requiredProductIds)
    {
        var required = requiredProductIds.ToHashSet();
        return g =>
        {
            var storeProductIds = g.Select(p => p.ProductId).Distinct().ToHashSet();
            return required.All(pid => storeProductIds.Contains(pid));
        };
    }
}