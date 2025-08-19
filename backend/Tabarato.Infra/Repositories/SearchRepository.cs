using Elastic.Clients.Elasticsearch;
using Elastic.Clients.Elasticsearch.QueryDsl;
using Tabarato.Domain.Repositories;
using Tabarato.Domain.Resources;

namespace Tabarato.Infra.Repositories;

public class SearchRepository(ElasticsearchClient client) : ISearchRepository
{
    public async Task<PagedResponse<DocumentProduct>> SearchProducts(string query, int page)
    {
        const int PAGE_SIZE = 10;
        
        var response = await client.SearchAsync<DocumentProduct>("products", request => request
            .Query(q => q
                .Bool(b => b
                    .Must(m => m
                        .MultiMatch(mm => mm
                            .Query(query)
                            .Type(TextQueryType.MostFields)
                            .Fields(Fields.FromStrings([
                                "name^3",
                                "brand"
                            ]))
                        )
                    )
                )
            )
            .From((page - 1) * PAGE_SIZE)
            .Size(PAGE_SIZE)
        );

        return new PagedResponse<DocumentProduct>(response.Documents.ToArray(), response.Total);
    }
}