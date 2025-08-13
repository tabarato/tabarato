using Tabarato.Domain.Resources;

namespace Tabarato.Application.Dtos;

public class ProductResponse
{
    public int Id { get; set; }
    public string Brand { get; set; }
    public string Name { get; set; }
    public VariationResponse[] Variations { get; set; }

    public ProductResponse(DocumentProduct document)
    {
        Id = document.Id;
        Brand = document.Brand;
        Name = document.Name;
        Variations = document.Variations.Select(v => new VariationResponse(v)).ToArray();
    }
}