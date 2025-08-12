using Asp.Versioning;
using Microsoft.AspNetCore.Mvc;
using Tabarato.Application.Dtos;
using Tabarato.Application.Interfaces;

namespace Tabarato.Api.Controllers;

[ApiController]
[Route("v{version:apiVersion}/[controller]s")]
[ApiVersion("1.0")]
public class StoreController(IStoreService storeService) : ControllerBase
{
    [HttpGet]
    public async Task<ActionResult<StoreResponse>> GetStoresByIds([FromQuery] string[] slugs)
    {
        var stores = await storeService.GetStoresBySlugs(slugs);
        return Ok(stores);
    }
}