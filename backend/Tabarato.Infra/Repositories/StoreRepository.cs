using Microsoft.EntityFrameworkCore;
using Tabarato.Domain.Models;
using Tabarato.Domain.Repositories;
using Tabarato.Infra.Persistence;

namespace Tabarato.Infra.Repositories;

public class StoreRepository(TabaratoDbContext dbContext) : IStoreRepository
{
    public async Task<List<Store>> GetStoresBySlugs(IEnumerable<string> slugs)
    {
        return await dbContext.Stores
            .Where(s => slugs.Contains(s.Slug))
            .ToListAsync();
    }
}