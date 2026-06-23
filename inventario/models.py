from django.db import models
from django.core.exceptions import ValidationError

class Categoria(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"

    def __str__(self):
        return self.nombre

class Producto(models.Model):
    categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT, related_name='productos')
    codigo_sku = models.CharField(max_length=50, unique=True)
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    imagen = models.URLField(blank=True, help_text="URL de la imagen para el catálogo web")
    stock_fisico = models.PositiveIntegerField(default=0, help_text="Stock real en almacén")
    activo = models.BooleanField(default=True)

    def __str__(self):
        return f"[{self.codigo_sku}] {self.nombre}"

    @property
    def stock_disponible(self):
        # Descuenta las cantidades comprometidas en reservas activas (Pendientes o Aprobadas)
        reservas_activas = DetalleReserva.objects.filter(
            producto=self, 
            reserva__estado__in=['PEN', 'APR']
        ).aggregate(total=models.Sum('cantidad'))['total'] or 0
        
        return max(0, self.stock_fisico - reservas_activas)

class MovimientoInventario(models.Model):
    TIPO_MOVIMIENTO = [
        ('ENT', 'Entrada (Abastecimiento/Devolución)'),
        ('SAL', 'Salida (Ajuste/Pérdida/Desincorporación)'),
        ('CON', 'Consumo por Reserva Completada'),
    ]
    
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE, related_name='movimientos')
    tipo = models.CharField(max_length=3, choices=TIPO_MOVIMIENTO)
    cantidad = models.PositiveIntegerField()
    motivo = models.TextField(help_text="Explicación del movimiento para auditoría")
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Movimiento de Inventario"
        verbose_name_plural = "Movimientos de Inventario"

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.cantidad} uds de {self.producto.nombre}"

class Cliente(models.Model):
    nombre = models.CharField(max_length=150)
    documento_identidad = models.CharField(max_length=20, unique=True)
    correo = models.EmailField(unique=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nombre} ({self.documento_identidad})"

class Reserva(models.Model):
    ESTADOS_RESERVA = [
        ('PEN', 'Pendiente por Evaluar'),
        ('APR', 'Aprobada / Apartada en Inventario'),
        ('RET', 'Retirada (Completada y Descontada)'),
        ('CAN', 'Cancelada (Libera Stock)'),
    ]

    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='reservas')
    fecha_solicitud = models.DateTimeField(auto_now_add=True)
    fecha_retiro_estimada = models.DateField()
    estado = models.CharField(max_length=3, choices=ESTADOS_RESERVA, default='PEN')
    observaciones = models.TextField(blank=True)

    def __str__(self):
        return f"Reserva #{self.id} - {self.cliente.nombre} ({self.get_estado_display()})"

class DetalleReserva(models.Model):
    reserva = models.ForeignKey(Reserva, on_delete=models.CASCADE, related_name='detalles')
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT)
    cantidad = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.cantidad} x {self.producto.nombre} (Reserva #{self.reserva.id})"

    def clean(self):
        # Validación en el entorno de Django para evitar reservar más de lo disponible
        if self.cantidad > self.producto.stock_disponible:
            raise ValidationError(
                f"No hay suficiente stock disponible para {self.producto.nombre}. "
                f"Disponible actual: {self.producto.stock_disponible} unidades."
            )