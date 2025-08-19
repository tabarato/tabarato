using Tabarato.Domain.Resources;

namespace Tabarato.Application.Dtos;

public class ProductResponse
{
    public int Id { get; set; }
    public string Brand { get; set; } = string.Empty;
    public string Name { get; set; } = string.Empty;
    public VariationResponse[] Variations { get; set; } = [];

    public static implicit operator ProductResponse(DocumentProduct document)
    {
        return new ProductResponse
        {
            Id = document.Id,
            Brand = document.Brand,
            Name = document.Name,
            Variations = document.Variations.Select(v => (VariationResponse)v).ToArray()
        };
    }
}