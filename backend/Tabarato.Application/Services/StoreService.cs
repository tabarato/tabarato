using Tabarato.Application.Dtos;
using Tabarato.Application.Interfaces;
using Tabarato.Domain.Repositories;

namespace Tabarato.Application.Services;

public class StoreService(IStoreRepository storeRepository) : IStoreService
{
    public async Task<StoreResponse[]> GetStoresBySlugs(IEnumerable<string> slugs)
    {
        var stores = await storeRepository.GetStoresBySlugs(slugs);
        return stores.Select(StoreResponse.Create).ToArray();
    }
}