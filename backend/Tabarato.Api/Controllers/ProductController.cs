using System.ComponentModel.DataAnnotations;
using Asp.Versioning;
using Microsoft.AspNetCore.Mvc;
using Tabarato.Application.Dtos;
using Tabarato.Application.Interfaces;
using Tabarato.Domain.Resources;

namespace Tabarato.Api.Controllers;

[ApiController]
[Route("api/v{version:apiVersion}/[controller]s")]
[ApiVersion("1.0")]
public class ProductController(IProductService productService) : ControllerBase
{
    [HttpGet("search")]
    public async Task<ActionResult<PagedResponse<ProductResponse>>> Search([FromQuery, Required] string query, [FromQuery] int page = 1)
    {
        var products = await productService.SearchProducts(query, page);
        return Ok(products);
    }
}