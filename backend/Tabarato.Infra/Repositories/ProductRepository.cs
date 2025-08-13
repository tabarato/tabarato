using Microsoft.EntityFrameworkCore;
using Tabarato.Domain.Models;
using Tabarato.Domain.Repositories;
using Tabarato.Infra.Persistence;

namespace Tabarato.Infra.Repositories;

public class ProductRepository(TabaratoDbContext dbContext) : IProductRepository
{
    public async Task<List<StoreProduct>> GetStoreProductsByProductIds(IEnumerable<int> productIds)
    {
        return await dbContext.StoreProducts
            .Where(sp => productIds.Contains(sp.ProductId))
            .Include(sp => sp.Store)
            .ToListAsync();
    }
}