using Asp.Versioning;
using DotNetEnv;
using Elastic.Clients.Elasticsearch;
using Elastic.Transport;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using Microsoft.OpenApi.Models;
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
builder.Services.AddSwaggerGen(options =>
{
    options.SwaggerDoc("v1", new OpenApiInfo
    {
        Version = "v1",
        Title = "Tabarato API v1",
        Description = "API documentation for Tabarato v1"
    });
});
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
    app.MapOpenApi();
    app.UseSwagger();
    app.UseSwaggerUI(c =>
    {
        c.SwaggerEndpoint("/swagger/v1/swagger.json", "Tabarato API v1");
    });
}
else
{
    app.UseHttpsRedirection();
}

app.UseCors("AllowLocalhost5173");
app.UseExceptionHandler("/error");
app.MapControllers();
app.Map("/", () => Results.Redirect("/swagger"));
app.Map("/error", () => Results.Problem("An unexpected error occurred."));
app.Run();
