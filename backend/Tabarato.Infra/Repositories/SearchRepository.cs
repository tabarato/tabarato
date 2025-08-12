using Elastic.Clients.Elasticsearch;
using Elastic.Clients.Elasticsearch.QueryDsl;
using Tabarato.Domain.Models;
using Tabarato.Domain.Repositories;

namespace Tabarato.Infra.Repositories;

public class SearchRepository(ElasticsearchClient client) : ISearchRepository
{
    public async Task<DocumentProduct[]> SearchProducts(string query)
    {
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
        );

        return response.Documents.ToArray();
    }
}