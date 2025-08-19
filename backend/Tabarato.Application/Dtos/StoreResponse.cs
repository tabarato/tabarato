using Tabarato.Domain.Models;

namespace Tabarato.Application.Dtos;

public class StoreResponse
{
    public int Id { get; set; }
    public string Slug { get; set; } = string.Empty;
    public string Name { get; set; } = string.Empty;
    public string Address { get; set; } = string.Empty;

    public static implicit operator StoreResponse(Store store)
    {
        return new StoreResponse
        {
            Id = store.Id,
            Slug = store.Slug,
            Name = store.Name,
            Address = store.Address
        };
    }
}