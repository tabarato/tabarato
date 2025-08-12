using System.ComponentModel.DataAnnotations;

namespace Tabarato.Application.Dtos;

public class CalculateCartRequest
{
    [Required, MinLength(1)]
    public Dictionary<int, int> Products { get; set; }
}