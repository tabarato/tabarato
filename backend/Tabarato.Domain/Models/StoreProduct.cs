namespace Tabarato.Domain.Models;

public class StoreProduct
{
    public int Id { get; set; }
    public int StoreId { get; set; }
    public Store Store { get; set; }
    public int ProductId { get; set; }
    public Product Product { get; set; }
    public int RefId { get; set; }
    public string Name { get; set; }
    public decimal Price { get; set; }
    public decimal OldPrice { get; set; }
    public string Link { get; set; }
    public string CartLink { get; set; }
    public string ImageUrl { get; set; }
}
