using Tabarato.Domain.Models;

namespace Tabarato.Application.Dtos;

public class StoreResponse
{
    public int Id { get; set; }
    public string Slug { get; set; }
    public string Name { get; set; }
    public string Address { get; set; }

    private StoreResponse(int id, string slug, string name, string address)
    {
        Id = id;
        Slug = slug;
        Name = name;
        Address = address;
    }

    public static StoreResponse Create(Store store)
    {
        return new StoreResponse(store.Id, store.Slug, store.Name, store.Address);
    }
}