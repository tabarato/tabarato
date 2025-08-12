using Tabarato.Domain.Models;

namespace Tabarato.Domain.Repositories;

public interface IStoreRepository
{
    Task<List<Store>> GetStoresBySlugs(IEnumerable<string> slugs);
}