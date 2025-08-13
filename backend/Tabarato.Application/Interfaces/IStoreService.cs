using Tabarato.Application.Dtos;

namespace Tabarato.Application.Interfaces;

public interface IStoreService
{
    Task<StoreResponse[]> GetStoresBySlugs(IEnumerable<string> slugs);
}