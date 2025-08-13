using System.Text.Json;
using System.Text.Json.Serialization;
using Asp.Versioning;
using DotNetEnv;
using Elastic.Clients.Elasticsearch;
using Elastic.Transport;
using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using Scalar.AspNetCore;
using Tabarato.Application.Interfaces;
using Tabarato.Application.Services;
using Tabarato.Domain.Repositories;
using Tabarato.Infra.Persistence;
using Tabarato.Infra.Repositories;

var builder = WebApplication.CreateBuilder(args);

if (builder.Environment.IsDevelopment())
{
    Env.Load("../../");
    builder.Services.AddOpenApi();
}

builder.Configuration.AddEnvironmentVariables();

builder.Services.AddCors(options =>
{
    options.AddPolicy("AllowSpecificOrigin", policy =>
    {
        policy.WithOrigins(builder.Configuration["AllowedOrigin"]!)
            .AllowAnyHeader()
            .AllowAnyMethod();
    });
});

builder.Services
    .AddControllers()
    .AddJsonOptions(options =>
    {
        options.JsonSerializerOptions.Converters.Add(new JsonStringEnumConverter(JsonNamingPolicy.CamelCase));
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

builder.Services.AddRouting(options =>
{
    options.LowercaseUrls = true;
});
builder.Services.AddHealthChecks();
builder.Services
    .AddApiVersioning(options =>
    {
        options.DefaultApiVersion = new ApiVersion(1, 0);
        options.AssumeDefaultVersionWhenUnspecified = true;
        options.ReportApiVersions = true;
    })
    .AddApiExplorer(options =>
    {
        options.GroupNameFormat = "'v'VVV";
        options.SubstituteApiVersionInUrl = true;
    });

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
            builder.Configuration["ELASTICSEARCH_PASSWORD"]!));
    
    if (builder.Environment.IsDevelopment())
        settings = settings.ServerCertificateValidationCallback(CertificateValidations.AllowAll);
    
    return new ElasticsearchClient(settings);
});
builder.Services.AddHttpClient<IRoutesRepository, RoutesRepository>(client =>
{
    client.BaseAddress = new Uri(builder.Configuration["ROUTES_API_URL"]!);
    client.DefaultRequestHeaders.Add("X-Goog-Api-Key", builder.Configuration["ROUTES_API_KEY"]!);
});

builder.Services.AddScoped<IProductRepository, ProductRepository>();
builder.Services.AddScoped<ISearchRepository, SearchRepository>();
builder.Services.AddScoped<IStoreRepository, StoreRepository>();
builder.Services.AddScoped<IRoutesService, RoutesService>();
builder.Services.AddScoped<IProductService, ProductService>();
builder.Services.AddScoped<IStoreService, StoreService>();

var app = builder.Build();
if (app.Environment.IsDevelopment())
{
    var versions = new[] {"v1"};
    
    app.MapOpenApi();
    app.MapScalarApiReference(options =>
    {
        options.Servers = [];
        options
            .WithTitle("Tabarato API")
            .WithLayout(ScalarLayout.Modern)
            .WithTheme(ScalarTheme.Kepler)
            .WithDarkMode(false)
            .AddDocuments(versions);
    });

    using var scope = app.Services.CreateScope();
    var db = scope.ServiceProvider.GetRequiredService<TabaratoDbContext>();
    
    if (db.Database.CanConnect())
        db.Database.Migrate();
}
else
{
    app.UseHttpsRedirection();
}

app.UseCors("AllowSpecificOrigin");
app.UseAuthorization();
app.UseHealthChecks("/health");
app.UseExceptionHandler(exApp => 
{
    exApp.Run(async context => 
    {
        context.Response.StatusCode = 500;
        await context.Response.WriteAsJsonAsync(new {
            Error = "An unexpected error occurred"
        });
    });
});
app.UseAuthorization();
app.MapControllers();
app.Map("/", () => Results.Redirect("/scalar"));
app.Map("/error", () => Results.Problem("An unexpected error occurred."));
app.Run();
