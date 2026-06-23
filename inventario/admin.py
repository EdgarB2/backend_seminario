from django.contrib import admin
from .models import Categoria, Producto, MovimientoInventario, Cliente, Reserva, DetalleReserva

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('codigo_sku', 'nombre', 'categoria', 'stock_fisico', 'ver_stock_disponible', 'activo')
    list_filter = ('categoria', 'activo')
    search_fields = ('nombre', 'codigo_sku')

    def ver_stock_disponible(self, obj):
        return obj.stock_disponible
    ver_stock_disponible.short_description = 'Stock Disponible'

# Registramos el resto de los modelos de forma sencilla
admin.site.register(Categoria)
admin.site.register(MovimientoInventario)
admin.site.register(Cliente)
admin.site.register(Reserva)
admin.site.register(DetalleReserva)