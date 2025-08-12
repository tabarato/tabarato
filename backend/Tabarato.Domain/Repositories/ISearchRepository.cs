using Tabarato.Domain.Models;

namespace Tabarato.Domain.Repositories;

public interface ISearchRepository
{ 
    Task<DocumentProduct[]> SearchProducts(string query);
}