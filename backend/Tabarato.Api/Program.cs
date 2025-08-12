using Asp.Versioning;
using DotNetEnv;
using Elastic.Clients.Elasticsearch;
using Elastic.Transport;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using Scalar.AspNetCore;
using Tabarato.Application.Interfaces;
using Tabarato.Application.Services;
using Tabarato.Api.Config;
using Tabarato.Domain.Repositories;
using Tabarato.Infra.Persistence;
using Tabarato.Infra.Repositories;

var builder = WebApplication.CreateBuilder(args);

Env.Load("../../");

builder.Configuration.AddEnvironmentVariables();

builder.Services.AddCors(options =>
{
    options.AddPolicy("AllowLocalhost5173", policy =>
    {
        policy.WithOrigins("http://localhost:5173")
            .AllowAnyHeader()
            .AllowAnyMethod();
    });
});

builder.Services
    .AddControllers(options =>
    {
        options.Conventions.Insert(0, new RoutePrefixConvention(new RouteAttribute("api")));
    })
    .ConfigureApiBehaviorOptions(options =>
    {
        options.InvalidModelStateResponseFactory = context =>
        {
            var errors = context.ModelState.Values
                .SelectMany(v => v.Errors)
                .Select(e => e.ErrorMessage);

            return new BadRequestObjectResult(new
            {
                message = string.Join("\n", errors)
            });
        };
    });

builder.Services.AddOpenApi();
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddRouting(options =>
{
    options.LowercaseUrls = true;
});
builder.Services.AddApiVersioning(options =>
{
    options.DefaultApiVersion = new ApiVersion(1, 0);
    options.AssumeDefaultVersionWhenUnspecified = true;
    options.ReportApiVersions = true;
})
.AddApiExplorer(options =>
{
    options.GroupNameFormat = "'v'VVV";
    options.SubstituteApiVersionInUrl = true;
});;

builder.Services.AddDbContext<TabaratoDbContext>(options =>
    options
        .UseNpgsql(
            builder.Configuration["DEFAULT_CONNECTION_STRING"], 
            o => o.UseVector())
        .UseSnakeCaseNamingConvention()
);
builder.Services.AddSingleton(_ =>
{
    var settings = new ElasticsearchClientSettings(new Uri(builder.Configuration["ELASTICSEARCH_URL"]!))
        .Authentication(new BasicAuthentication(
            builder.Configuration["ELASTICSEARCH_USERNAME"]!,
            builder.Configuration["ELASTICSEARCH_PASSWORD"]!))
        .ServerCertificateValidationCallback(CertificateValidations.AllowAll);
    
    return new ElasticsearchClient(settings);
});
builder.Services.AddScoped<IProductRepository, ProductRepository>();
builder.Services.AddScoped<ISearchRepository, SearchRepository>();
builder.Services.AddScoped<IStoreRepository, StoreRepository>();
builder.Services.AddScoped<IProductService, ProductService>();
builder.Services.AddScoped<IStoreService, StoreService>();

var app = builder.Build();
if (app.Environment.IsDevelopment())
{
    var versions = new[] {"v1"};
    
    app.MapOpenApi();
    app.MapScalarApiReference(options =>
    {
        options
            .WithTitle("Tabarato API")
            .WithLayout(ScalarLayout.Classic)
            .WithTheme(ScalarTheme.Kepler)
            .AddDocuments(versions);
    });
}
else
{
    app.UseHttpsRedirection();
}

app.UseCors("AllowLocalhost5173");
app.UseExceptionHandler("/error");
app.MapControllers();
app.Map("/", () => Results.Redirect("/scalar"));
app.Map("/error", () => Results.Problem("An unexpected error occurred."));
app.Run();
