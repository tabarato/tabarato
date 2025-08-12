using System.ComponentModel.DataAnnotations;

namespace Tabarato.Application.Dtos;

public class StoreCartResponse
{
    [Required]
    public string StoreName { get; set; }
    
    [Required]
    public List<CartItemResponse> Items { get; set; }
    
    [Required]
    public decimal TotalCost { get; set; }

    protected StoreCartResponse(string storeName, List<CartItemResponse> items)
    {
        StoreName = storeName;
        Items = items;
        TotalCost = items.Sum(i => i.TotalPrice);
    }

    public static StoreCartResponse Create(IGrouping<int, CartItemResponse> g)
    {
        return new StoreCartResponse(g.First().Store.Name, g.ToList());
    }
}