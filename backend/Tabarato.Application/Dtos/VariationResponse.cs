using Tabarato.Domain.Resources;

namespace Tabarato.Application.Dtos;

public class VariationResponse
{
    public int Id { get; set; }
    public decimal Weight { get; set; }
    public string Measure { get; set; }
    public string Name { get; set; }
    public string ImageUrl { get; set; }
    public decimal MinPrice { get; set; }
    public decimal MaxPrice { get; set; }
    public string[] Stores { get; set; }

    public VariationResponse(DocumentVariation document)
    {
        Id = document.Id;
        Weight = document.Weight;
        Measure = document.Measure;
        Name = document.Name;
        ImageUrl = document.ImageUrl;
        MinPrice = document.MinPrice;
        MaxPrice = document.MaxPrice;
        Stores = document.Stores;
    }
}