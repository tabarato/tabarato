using Asp.Versioning;
using Microsoft.AspNetCore.Mvc;
using Tabarato.Application.Dtos;
using Tabarato.Application.Interfaces;

namespace Tabarato.Api.Controllers;

[ApiController]
[Route("v{version:apiVersion}/[controller]s")]
[ApiVersion("1.0")]
public class CheckoutController(IProductService productService) : ControllerBase
{
    [HttpPost("cheapest-store")]
    public async Task<ActionResult<StoreCartResponse>> CalculateCheapestStore([FromBody] CalculateCartRequest request)
    {
        var result = await productService.CalculateCheapestStoreAsync(request);
        return Ok(result);
    }

    [HttpPost("cheapest-items")]
    public async Task<ActionResult<IEnumerable<StoreCartResponse>>> CalculateCheapestItems([FromBody] CalculateCartRequest request)
    {
        var result = await productService.CalculateCheapestItemsAsync(request);
        return Ok(result);
    }

    [HttpPost("cheapest-store-with-distance")]
    public async Task<ActionResult<StoreCartResponse>> CalculateCheapestStoreWithDistance([FromBody] CalculateCartWithDistanceRequest request)
    {
        var result = await productService.CalculateCheapestStoreWithDistanceAsync(request);
        return Ok(result);
    }

    [HttpPost("cheapest-stores-ranking-with-distance")]
    public async Task<ActionResult<IEnumerable<StoreCartResponse>>> CalculateCheapestStoresRankingWithDistance([FromBody] CalculateCartWithDistanceRequest request)
    {
        var result = await productService.CalculateCheapestStoresRankingWithDistanceAsync(request);
        return Ok(result);
    }
}