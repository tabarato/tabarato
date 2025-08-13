using System.Text.Json.Serialization;
using Tabarato.Domain.Models;

namespace Tabarato.Application.Dtos;

public class CartOfferItemResponse
{
    public string Name { get; set; }
    public decimal Price { get; set; }
    public string CartLink { get; set; }
    public decimal TotalPrice { get; set; }
    public int Quantity { get; set; }

    [JsonIgnore]
    public int ProductId { get; set; }

    [JsonIgnore]
    public StoreResponse Store { get; set; }
    
    private CartOfferItemResponse(
        string name,
        decimal price,
        string cartLink,
        int quantity,
        int productId,
        StoreResponse store)
    {
        Name = name;
        Price = price;
        CartLink = cartLink;
        TotalPrice = quantity * price;
        Quantity = quantity;
        ProductId = productId;
        Store = store;
    }

    public static CartOfferItemResponse Create(StoreProduct storeProduct, int quantity)
    {
        return new CartOfferItemResponse(
            storeProduct.Name, storeProduct.Price, storeProduct.CartLink, quantity,
            storeProduct.ProductId, StoreResponse.Create(storeProduct.Store));
    }
}