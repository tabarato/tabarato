using System.Text.Json.Serialization;

namespace Tabarato.Domain.Resources;

public class DocumentVariation
{
    public int Id { get; set; }
    
    public decimal Weight { get; set; }
    public string Measure { get; set; }
    public string Name { get; set; }
    
    [JsonPropertyName("image_url")]
    public string ImageUrl { get; set; }
    
    [JsonPropertyName("min_price")]
    public decimal MinPrice { get; set; }
    
    [JsonPropertyName("max_price")]
    public decimal MaxPrice { get; set; }
    public string[] Stores { get; set; }
}