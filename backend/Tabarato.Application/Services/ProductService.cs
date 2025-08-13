using Tabarato.Application.Dtos;
using Tabarato.Application.Interfaces;
using Tabarato.Domain.Repositories;
using Tabarato.Domain.Resources;

namespace Tabarato.Application.Services;

public class ProductService(IProductRepository productRepository, ISearchRepository searchRepository) : IProductService
{
    public async Task<ProductResponse[]> SearchProducts(string query)
    {
        var documents = await searchRepository.SearchProducts(query);

        return documents.Select(d => new ProductResponse(d)).ToArray();
    }

    public async Task<CartOfferResponse?> CalculateCheapestStoreAsync(Dictionary<int, int> products)
    {
        var storeProducts = await GetCartItemsResponse(products);
        
        return storeProducts
            .GroupBy(cir => cir.Store.Id)
            .Where(HasAllRequestedProducts(products.Keys))
            .Select(CartOfferResponse.Create)
            .MinBy(scr => scr.TotalCost);
    }
    
    public async Task<CartOfferResponse[]> CalculateCheapestItemsAsync(Dictionary<int, int> products)
    {
        var storeProducts = await GetCartItemsResponse(products);
        
        return storeProducts
            .GroupBy(cir => cir.ProductId)
            .Select(g => g.MinBy(sp => sp.Price)!)
            .GroupBy(cir => cir.Store.Id)
            .Select(CartOfferResponse.Create)
            .ToArray();
    }

    public async Task<CartOfferWithDistanceResponse?> CalculateCheapestStoreWithDistanceAsync(Dictionary<int, int> products, Dictionary<int, DistanceInfo> distances)
    {
        var storeProducts = await GetCartItemsResponse(products);
        
        return storeProducts
            .GroupBy(cir => cir.Store.Id)
            .Where(HasAllRequestedProducts(products.Keys))
            .Select(g => CartOfferWithDistanceResponse.Create(g, distances[g.First().Store.Id]))
            .OrderBy(scr => scr.TotalCost)
            .ThenBy(scr => scr.DistanceInfo.DistanceKm)
            .ThenBy(scr => scr.DistanceInfo.DurationMin)
            .FirstOrDefault();
    }

    public async Task<CartOfferWithDistanceResponse[]> CalculateCheapestStoresRankingWithDistanceAsync(Dictionary<int, int> products, Dictionary<int, DistanceInfo> distances)
    {
        var storeProducts = await GetCartItemsResponse(products);

        return storeProducts
            .GroupBy(cir => cir.ProductId)
            .Select(g => g.MinBy(sp => sp.Price)!)
            .GroupBy(cir => cir.Store.Id)
            .Select(g => CartOfferWithDistanceResponse.Create(g, distances[g.First().Store.Id]))
            .ToArray();
    }
    
    private async Task<IEnumerable<CartOfferItemResponse>> GetCartItemsResponse(Dictionary<int, int> products)
    {
        var storeProducts = await productRepository.GetStoreProductsByProductIds(products.Keys);
        return storeProducts.Select(sp => CartOfferItemResponse.Create(sp, products[sp.ProductId]));
    }

    private static Func<IGrouping<int, CartOfferItemResponse>, bool> HasAllRequestedProducts(IEnumerable<int> requiredProductIds)
    {
        var required = requiredProductIds.ToHashSet();
        return g =>
        {
            var storeProductIds = g.Select(p => p.ProductId).Distinct().ToHashSet();
            return required.All(pid => storeProductIds.Contains(pid));
        };
    }
}