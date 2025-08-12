using Microsoft.EntityFrameworkCore;
using Tabarato.Domain.Models;

namespace Tabarato.Infra.Persistence;

public class TabaratoDbContext(DbContextOptions<TabaratoDbContext> options) : DbContext(options)
{
    public DbSet<Brand> Brands => Set<Brand>();
    public DbSet<Store> Stores => Set<Store>();
    public DbSet<ProductFamily> ProductFamilies => Set<ProductFamily>();
    public DbSet<Product> Products => Set<Product>();
    public DbSet<StoreProduct> StoreProducts => Set<StoreProduct>();

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        base.OnModelCreating(modelBuilder);
        
        modelBuilder.HasPostgresExtension("vector");

        modelBuilder.Entity<Brand>(entity =>
        {
            entity.HasKey(b => b.Id);
            entity.HasIndex(b => b.Slug).IsUnique();
            entity.Property(b => b.Slug).HasMaxLength(255);
            entity.Property(b => b.Name).HasMaxLength(255);
        });

        modelBuilder.Entity<Store>(entity =>
        {
            entity.HasKey(s => s.Id);
            entity.HasIndex(s => s.Slug).IsUnique();
            entity.Property(s => s.Slug).HasMaxLength(255);
            entity.Property(s => s.Name).HasMaxLength(255);
            entity.HasData(
                new Store(1, "angeloni", "Angeloni", "Av. Centenário, 2699 - Centro, Criciúma - SC, 88802-000"),
                new Store(2, "bistek", "Bistek", "Av. Centenário, 3420 - Centro, Criciúma - SC, 88802-000"),
                new Store(3, "giassi", "Giassi", "R. Henrique Lage, 1251 - Santa Barbara, Criciúma - SC, 88804-010")
            );
        });

        modelBuilder.Entity<ProductFamily>(entity =>
        {
            entity.HasKey(pf => pf.Id);
            entity.Property(pf => pf.Name).HasMaxLength(255);
            entity.Property(pf => pf.EmbeddedName).HasColumnType("vector(768)");
            entity.HasOne(pf => pf.Brand)
                .WithMany(b => b.ProductFamilies)
                .HasForeignKey(pf => pf.BrandId);
        });

        modelBuilder.Entity<Product>(entity =>
        {
            entity.HasKey(p => p.Id);
            entity.Property(p => p.Name).HasMaxLength(255);
            entity.HasOne(p => p.ProductFamily)
                .WithMany(pf => pf.Products)
                .HasForeignKey(p => p.ProductFamilyId)
                .OnDelete(DeleteBehavior.Cascade);
        });

        modelBuilder.Entity<StoreProduct>(entity =>
        {
            entity.HasKey(sp => sp.Id);
            entity.Property(sp => sp.Name).HasMaxLength(255);
            entity.HasIndex(sp => new { sp.StoreId, sp.ProductId }).IsUnique();
            entity.HasOne(sp => sp.Store)
                .WithMany(s => s.StoreProducts)
                .HasForeignKey(sp => sp.StoreId);
            entity.HasOne(sp => sp.Product)
                .WithMany(p => p.StoreProducts)
                .HasForeignKey(sp => sp.ProductId)
                .OnDelete(DeleteBehavior.Cascade);
            entity.HasOne(sp => sp.Product)
                .WithMany(p => p.StoreProducts)
                .HasForeignKey(sp => sp.ProductId)
                .OnDelete(DeleteBehavior.Cascade);
        });
    }
}
