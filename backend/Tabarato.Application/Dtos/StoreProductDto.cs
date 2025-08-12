using Tabarato.Domain.Models;

namespace Tabarato.Application.Dtos;

public class StoreProductDto
{
    public StoreDto Store { get; set; }
    public int IdProduct { get; set; } 
    public string Name { get; set; }
    public decimal Price { get; set; }
    public decimal OldPrice { get; set; }
    public string Link { get; set; }
    public string CartLink { get; set; }
    public string ImageUrl { get; set; }
    public int Quantity { get; set; }

    private StoreProductDto(
        StoreDto store,
        int idProduct,
        string name,
        decimal price,
        decimal oldPrice,
        string link,
        string cartLink,
        string imageUrl,
        int quantity)
    {
        Store = store;
        IdProduct = idProduct;
        Name = name;
        Price = price;
        OldPrice = oldPrice;
        Link = link;
        CartLink = cartLink;
        ImageUrl = imageUrl;
        Quantity = quantity;
    }

    public static StoreProductDto Create(StoreProduct storeProduct, int quantity)
    {
        return Create(
            storeProduct,
            StoreDto.Create(storeProduct.Store),
            quantity
        );
    }

    public static StoreProductDto Create(StoreProduct storeProduct, int quantity, DistanceInfo distanceInfo)
    {
        return Create(
            storeProduct,
            StoreDto.Create(storeProduct.Store, distanceInfo),
            quantity
        );
    }

    private static StoreProductDto Create(StoreProduct storeProduct, StoreDto store, int quantity)
    {
        return new StoreProductDto(
            store,
            storeProduct.ProductId,
            storeProduct.Name,
            storeProduct.Price,
            storeProduct.OldPrice,
            storeProduct.Link,
            storeProduct.CartLink,
            storeProduct.ImageUrl,
            quantity
        );
    }
}