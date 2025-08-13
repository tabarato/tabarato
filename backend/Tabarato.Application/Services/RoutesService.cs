using Tabarato.Application.Interfaces;
using Tabarato.Domain.Repositories;
using Tabarato.Domain.Resources;

namespace Tabarato.Application.Services;

public class RoutesService(IRoutesRepository routesRepository) : IRoutesService
{
    public async Task<DistanceInfo[]> GetSeparateIntermediateRoutesAsync(
        string origin,
        string destination,
        IEnumerable<string> intermediates,
        TravelMode travelMode)
    {
        return await routesRepository.GetSeparateIntermediateRoutesAsync(
            origin,
            destination,
            intermediates,
            travelMode);
    }
}
