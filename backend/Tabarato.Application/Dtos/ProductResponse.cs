using System.ComponentModel.DataAnnotations;
using Tabarato.Domain.Models;

namespace Tabarato.Application.Dtos;

public class ProductResponse
{
    [Required]
    public int Id { get; set; }
    
    [Required]
    public string Brand { get; set; }
    
    [Required]
    public string Name { get; set; }
    
    [Required]
    public VariationResponse[] Variations { get; set; }

    public ProductResponse(DocumentProduct document)
    {
        Id = document.Id;
        Brand = document.Brand;
        Name = document.Name;
        Variations = document.Variations.Select(v => new VariationResponse(v)).ToArray();
    }
}