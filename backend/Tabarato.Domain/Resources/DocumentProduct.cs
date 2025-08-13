using Tabarato.Domain.Models;

namespace Tabarato.Domain.Resources;

public class DocumentProduct
{
    public int Id { get; set; }
    public string Brand { get; set; }
    public string Name { get; set; }
    public DocumentVariation[] Variations { get; set; }
}