using Tabarato.Domain.Models;

namespace Tabarato.Application.Dtos;

public class StoreResponse(int id, string slug, string name, string address)
{
    public int Id { get; set; } = id;
    public string Slug { get; set; } = slug;
    public string Name { get; set; } = name;
    public string Address { get; set; } = address;

    public static StoreResponse Create(Store store)
    {
        return new StoreResponse(store.Id, store.Slug, store.Name, store.Address);
    }
}