using Tabarato.Domain.Resources;

namespace Tabarato.Domain.Repositories;

public interface ISearchRepository
{ 
    Task<PagedResponse<DocumentProduct>> SearchProducts(string query, int page);
}