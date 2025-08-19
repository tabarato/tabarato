namespace Tabarato.Domain.Resources;

public class PagedResponse<T>(T[] data, long totalCount)
{
    public T[] Data { get; set; } = data;
    public long TotalCount { get; set; } = totalCount;
}