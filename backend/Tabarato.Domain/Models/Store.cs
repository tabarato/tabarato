namespace Tabarato.Domain.Models;

public class Store
{
    public int Id { get; set; }
    public string Slug { get; set; }
    public string Name { get; set; }
    public string Address { get; set; }
    public ICollection<StoreProduct> StoreProducts { get; set; } = new List<StoreProduct>();

    public Store(int id, string slug, string name, string address)
    {
        Id = id;
        Slug = slug;
        Name = name;
        Address = address;
    }
}
