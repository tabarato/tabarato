using System.ComponentModel.DataAnnotations;
using Asp.Versioning;
using Microsoft.AspNetCore.Mvc;
using Tabarato.Application.Dtos;
using Tabarato.Application.Interfaces;

namespace Tabarato.Api.Controllers;

[ApiController]
[Route("api/v{version:apiVersion}/[controller]s")]
[ApiVersion("1.0")]
public class ProductController(IProductService productService) : ControllerBase
{
    [HttpGet("search")]
    public async Task<ActionResult<ProductResponse>> Search([FromQuery, Required] string query)
    {
        var products = await productService.SearchProducts(query);
        return Ok(products);
    }
}