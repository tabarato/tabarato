using System.ComponentModel.DataAnnotations;

namespace Tabarato.Application.Dtos;

public class CartItemResponse
{
    [Required]
    public string Name { get; set; }
    
    [Required]
    public decimal Price { get; set; }
    
    [Required]
    public string CartLink { get; set; }
    
    [Required]
    public decimal TotalPrice { get; set; }
    
    [Required]
    public int Quantity { get; set; }

    private CartItemResponse(string name, decimal price, string cartLink, int quantity)
    {
        Name = name;
        Price = price;
        CartLink = cartLink;
        Quantity = quantity;
        TotalPrice = quantity * price;
    }

    public static CartItemResponse Create(StoreProductDto storeProduct)
    {
        return new CartItemResponse(storeProduct.Name, storeProduct.Price, storeProduct.CartLink, storeProduct.Quantity);
    }
}