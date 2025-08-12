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

    public static StoreCartResponse Create(IGrouping<int, StoreProductDto> g)
    {
        var storeName = g.First().Store.Name;
        var items = g.Select(CartItemResponse.Create).ToList();
        
        return new StoreCartResponse(storeName, items);
    }
}