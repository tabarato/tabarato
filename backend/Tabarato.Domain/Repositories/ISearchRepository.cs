using Tabarato.Domain.Models;
using Tabarato.Domain.Resources;

namespace Tabarato.Domain.Repositories;

public interface ISearchRepository
{ 
    Task<DocumentProduct[]> SearchProducts(string query);
}