using Tabarato.Application.Dtos;

namespace Tabarato.Application.Interfaces;

public interface IStoreService
{
    Task<IEnumerable<StoreResponse>> GetStoresBySlugs(IEnumerable<string> slugs);
}