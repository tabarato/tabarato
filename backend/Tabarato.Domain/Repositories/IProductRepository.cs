using Tabarato.Domain.Models;

namespace Tabarato.Domain.Repositories;

public interface IProductRepository
{
    Task<List<StoreProduct>> GetStoreProductsByProductIds(IEnumerable<int> productIds);
}