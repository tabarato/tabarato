namespace Tabarato.Domain.Models;

public class Brand
{
    public int Id { get; set; }
    public string Slug { get; set; }
    public string Name { get; set; }
    public ICollection<ProductFamily> ProductFamilies { get; set; } = new List<ProductFamily>();
}
