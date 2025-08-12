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

    public async Task<StoreCartResponse> CalculateCheapestStoreAsync(CalculateCartRequest request)
    {
        var storeProducts = await GetStoreProductDtos(request);
        
        return storeProducts
            .GroupBy(sp => sp.Store.Id)
            .Where(HasAllRequestedProducts(request.Products.Keys))
            .Select(StoreCartResponse.Create)
            .OrderBy(scr => scr.TotalCost)
            .First();
    }
    
    public async Task<IEnumerable<StoreCartResponse>> CalculateCheapestItemsAsync(CalculateCartRequest request)
    {
        var storeProducts = await GetStoreProductDtos(request);
        
        return storeProducts
            .GroupBy(sp => sp.IdProduct)
            .Select(g => g.MinBy(sp => sp.Price)!)
            .GroupBy(sp => sp.Store.Id)
            .Select(StoreCartResponse.Create)
            .ToList();
    }

    public async Task<StoreCartWithDistanceResponse> CalculateCheapestStoreWithDistanceAsync(CalculateCartWithDistanceRequest request)
    {
        var storeProducts = await GetStoreProductDtosWithDistance(request);
        
        return storeProducts
            .GroupBy(sp => sp.Store.Id)
            .Where(HasAllRequestedProducts(request.Products.Keys))
            .Select(StoreCartWithDistanceResponse.Create)
            .OrderBy(scr => scr.TotalCost)
            .ThenBy(scr => scr.DistanceInfo!.DistanceKm)
            .ThenBy(scr => scr.DistanceInfo!.DurationMin)
            .First();
    }

    public async Task<IEnumerable<StoreCartWithDistanceResponse>> CalculateCheapestStoresRankingWithDistanceAsync(CalculateCartWithDistanceRequest request)
    {
        var storeProducts = await GetStoreProductDtosWithDistance(request);

        return storeProducts
            .GroupBy(sp => sp.IdProduct)
            .Select(g => g.MinBy(sp => sp.Price)!)
            .GroupBy(sp => sp.Store.Id)
            .Select(StoreCartWithDistanceResponse.Create)
            .ToList();
    }
    
    private async Task<IEnumerable<StoreProductDto>> GetStoreProductDtos(CalculateCartRequest request)
    {
        var storeProducts = await productRepository.GetStoreProductsByProductIds(request.Products.Keys);
        return storeProducts.Select(sp => StoreProductDto.Create(sp, request.Products[sp.ProductId]));
    }

    private async Task<IEnumerable<StoreProductDto>> GetStoreProductDtosWithDistance(CalculateCartWithDistanceRequest request)
    {
        var storeProducts = await productRepository.GetStoreProductsByProductIds(request.Products.Keys);
        return storeProducts.Select(sp =>
            StoreProductDto.Create(sp, request.Products[sp.ProductId], request.Distances[sp.Store.Id])
        );
    }

    private static Func<IGrouping<int, StoreProductDto>, bool> HasAllRequestedProducts(IEnumerable<int> requiredProductIds)
    {
        var required = requiredProductIds.ToHashSet();
        return g =>
        {
            var storeProductIds = g.Select(p => p.IdProduct).Distinct().ToHashSet();
            return required.All(pid => storeProductIds.Contains(pid));
        };
    }
}