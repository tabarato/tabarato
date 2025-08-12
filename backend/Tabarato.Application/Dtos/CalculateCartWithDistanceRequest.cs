using System.ComponentModel.DataAnnotations;

namespace Tabarato.Application.Dtos;

public class CalculateCartWithDistanceRequest : CalculateCartRequest
{
    [Required, MinLength(1)]
    public Dictionary<int, DistanceInfo> Distances { get; set; }
}