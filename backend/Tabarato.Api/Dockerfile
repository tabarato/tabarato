FROM mcr.microsoft.com/dotnet/aspnet:9.0 AS base
USER $APP_UID
WORKDIR /app

FROM mcr.microsoft.com/dotnet/sdk:9.0 AS build
ARG BUILD_CONFIGURATION=Release
WORKDIR /src

COPY ["Tabarato.Api/Tabarato.Api.csproj", "Tabarato.Api/"]
COPY ["Tabarato.Application/Tabarato.Application.csproj", "Tabarato.Application/"]
COPY ["Tabarato.Domain/Tabarato.Domain.csproj", "Tabarato.Domain/"]
COPY ["Tabarato.Infra/Tabarato.Infra.csproj", "Tabarato.Infra/"]

RUN dotnet restore "Tabarato.Api/Tabarato.Api.csproj"

COPY . .
WORKDIR "/src/Tabarato.Api"
RUN dotnet build "Tabarato.Api.csproj" -c $BUILD_CONFIGURATION -o /app/build

FROM build AS publish
ARG BUILD_CONFIGURATION=Release
RUN dotnet publish "Tabarato.Api.csproj" -c $BUILD_CONFIGURATION -o /app/publish /p:UseAppHost=false

FROM mcr.microsoft.com/dotnet/sdk:9.0 AS final
WORKDIR /app
COPY --from=publish /app/publish .

RUN dotnet dev-certs https --clean
RUN dotnet dev-certs https

ENTRYPOINT ["dotnet", "Tabarato.Api.dll"]
