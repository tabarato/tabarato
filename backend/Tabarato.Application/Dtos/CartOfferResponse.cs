namespace Tabarato.Application.Dtos;

public class CartOfferResponse(string storeName, List<CartOfferItemResponse> items, decimal totalCost)
{
    public string StoreName { get; set; } = storeName;
    public List<CartOfferItemResponse> Items { get; set; } = items;
    public decimal TotalCost { get; set; } = totalCost;

    public static CartOfferResponse Create(IGrouping<int, CartOfferItemResponse> g)
    {
        return new CartOfferResponse(g.First().Store.Name, g.ToList(), g.Sum(i => i.TotalPrice));
    }
}