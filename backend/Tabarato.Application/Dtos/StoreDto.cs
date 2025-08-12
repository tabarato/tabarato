using Tabarato.Domain.Models;

namespace Tabarato.Application.Dtos;

public class StoreDto
{
    public int Id { get; set; }
    public string Name { get; set; }
    public DistanceInfo? DistanceInfo { get; set; }

    private StoreDto(int id, string name)
    {
        Id = id;
        Name = name;
    }

    private StoreDto(int id, string name, DistanceInfo distanceInfo) : this(id, name)
    {
        DistanceInfo = distanceInfo;
    }

    public static StoreDto Create(Store store)
    {
        return new StoreDto(store.Id, store.Name);
    }

    public static StoreDto Create(Store store, DistanceInfo distanceInfo)
    {
        return new StoreDto(store.Id, store.Name, distanceInfo);
    }
}