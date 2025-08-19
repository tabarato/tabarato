using Tabarato.Domain.Resources;

namespace Tabarato.Application.Dtos;

public class VariationResponse
{
    public int Id { get; set; }
    public decimal Weight { get; set; }
    public string Measure { get; set; } = string.Empty;
    public string Name { get; set; } = string.Empty;
    public string ImageUrl { get; set; } = string.Empty;
    public decimal MinPrice { get; set; }
    public decimal MaxPrice { get; set; }
    public string[] Stores { get; set; } = [];

    public static implicit operator VariationResponse(DocumentVariation document)
    {
        return new VariationResponse
        {
            Id = document.Id,
            Weight = document.Weight,
            Measure = document.Measure,
            Name = document.Name,
            ImageUrl = document.ImageUrl,
            MinPrice = document.MinPrice,
            MaxPrice = document.MaxPrice,
            Stores = document.Stores
        };
    }
}