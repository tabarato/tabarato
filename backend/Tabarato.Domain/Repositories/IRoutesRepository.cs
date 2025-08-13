using Tabarato.Domain.Resources;

namespace Tabarato.Domain.Repositories;

public interface IRoutesRepository
{
    Task<DistanceInfo[]> GetSeparateIntermediateRoutesAsync(
        string origin,
        string destination,
        IEnumerable<string> intermediates,
        TravelMode travelMode);
}