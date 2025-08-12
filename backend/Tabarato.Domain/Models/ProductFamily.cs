using Pgvector;

namespace Tabarato.Domain.Models;

public class ProductFamily
{
    public int Id { get; set; }
    public int BrandId { get; set; }
    public Brand Brand { get; set; }
    public string Name { get; set; }
    public Vector EmbeddedName { get; set; }
    public ICollection<Product> Products { get; set; } = new List<Product>();
}
