using System.ComponentModel.DataAnnotations;
using System.Text.Json.Serialization;
using Tabarato.Domain.Models;

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
    
    [JsonIgnore]
    public int ProductId { get; set; }
    
    [JsonIgnore]
    public StoreResponse Store { get; set; }

    private CartItemResponse(string name, decimal price, string cartLink, int quantity, int productId, StoreResponse store)
    {
        Name = name;
        Price = price;
        CartLink = cartLink;
        Quantity = quantity;
        TotalPrice = quantity * price;
        ProductId = productId;
        Store = store;
    }

    public static CartItemResponse Create(StoreProduct storeProduct, int quantity)
    {
        return new CartItemResponse(
            storeProduct.Name, storeProduct.Price, storeProduct.CartLink, quantity,
            storeProduct.ProductId, StoreResponse.Create(storeProduct.Store));
    }
}