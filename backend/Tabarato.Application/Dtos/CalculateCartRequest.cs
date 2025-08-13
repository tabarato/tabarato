using System.ComponentModel.DataAnnotations;
using System.Text.Json.Serialization;
using Tabarato.Domain.Resources;

namespace Tabarato.Application.Dtos;

public class CalculateCartRequest
{
    [MinLength(1)]
    public required Dictionary<int, int> Products { get; set; }
    public required string Origin { get; set; }
    public required string Destination { get; set; }
    
    [JsonConverter(typeof(JsonStringEnumConverter))]
    public required TravelMode TravelMode { get; set; }
    public required string[] Stores { get; set; }
}
