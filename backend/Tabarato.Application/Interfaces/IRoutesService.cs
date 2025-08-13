using Tabarato.Domain.Resources;

namespace Tabarato.Application.Interfaces;

public interface IRoutesService
{
    Task<DistanceInfo[]> GetSeparateIntermediateRoutesAsync(
        string origin,
        string destination,
        IEnumerable<string> intermediates,
        TravelMode travelMode);
}