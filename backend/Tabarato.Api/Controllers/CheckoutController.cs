using Asp.Versioning;
using Microsoft.AspNetCore.Mvc;
using Tabarato.Application.Dtos;
using Tabarato.Application.Interfaces;

namespace Tabarato.Api.Controllers;

[ApiController]
[Route("api/v{version:apiVersion}/[controller]")]
[ApiVersion("1.0")]
public class CheckoutController(IProductService productService, IRoutesService routesService, IStoreService storeService) : ControllerBase
{
    [HttpPost]
    public async Task<ActionResult<CartResponse>> CalculateCart([FromBody] CalculateCartRequest request)
    {
        var stores = await storeService.GetStoresBySlugs(request.Stores);
        var routes = await routesService.GetSeparateIntermediateRoutesAsync(
            request.Origin,
            request.Destination,
            stores.Select(s => s.Address),
            request.TravelMode);
        
        var distances = Enumerable.Range(0, routes.Length)
            .ToDictionary(i => stores[i].Id, i => routes[i]);

        var cheapestStore = await productService.CalculateCheapestStoreAsync(request.Products);
        var cheapestItems = await productService.CalculateCheapestItemsAsync(request.Products);
        var cheapestStoreWithDistance = await productService.CalculateCheapestStoreWithDistanceAsync(request.Products, distances);
        var cheapestItemsWithDistance = await productService.CalculateCheapestStoresRankingWithDistanceAsync(request.Products, distances);

        var result = new CartResponse(
            cheapestStore,
            cheapestItems,
            cheapestStoreWithDistance,
            cheapestItemsWithDistance);

        return Ok(result);
    }
}
