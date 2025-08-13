namespace Tabarato.Domain.Models;

public class Product
{
    public int Id { get; set; }
    public int ProductFamilyId { get; set; }
    public ProductFamily ProductFamily { get; set; }
    public string Name { get; set; }
    public int? Weight { get; set; }
    public string? Measure { get; set; }
    public ICollection<StoreProduct> StoreProducts { get; set; } = new List<StoreProduct>();
}
