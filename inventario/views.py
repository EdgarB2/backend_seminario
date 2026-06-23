from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import transaction
from .models import Producto, Cliente, Reserva, DetalleReserva
from datetime import datetime

def catalogo_tenant(request):
    """Lógica para mostrar el catálogo al cliente."""
    # Solo traemos productos activos
    productos = Producto.objects.filter(activo=True)
    
    # Pasamos los productos a la plantilla HTML 
    return render(request, 'inventario/catalogo.html', {'productos': productos})

@transaction.atomic
def procesar_reserva(request):
    """Lógica crítica para registrar un cliente y crear su reserva segura."""
    if request.method == 'POST':
        try:
            # Capturar datos del formulario del cliente (Frontend)
            nombre = request.POST.get('nombre')
            cedula = request.POST.get('cedula')
            correo = request.POST.get('correo')
            producto_id = request.POST.get('producto_id')
            cantidad = int(request.POST.get('cantidad', 1))
            fecha_retiro = request.POST.get('fecha_retiro')

            # Buscar o crear al cliente
            cliente, creado = Cliente.objects.get_or_create(
                documento_identidad=cedula,
                defaults={'nombre': nombre, 'correo': correo}
            )

            # Verificar el Producto y el Stock Disponible
            producto = Producto.objects.get(id=producto_id)
            
            if cantidad > producto.stock_disponible:
                messages.error(request, f"¡Error! Solo quedan {producto.stock_disponible} unidades disponibles de {producto.nombre}.")
                return redirect('catalogo') # Devuelve al usuario al catálogo

            # Crear la Reserva Maestra
            nueva_reserva = Reserva.objects.create(
                cliente=cliente,
                fecha_retiro_estimada=fecha_retiro,
                estado='PEN' # Se crea como Pendiente
            )

            # Crear el Detalle de la Reserva (Lo que aparta el producto)
            DetalleReserva.objects.create(
                reserva=nueva_reserva,
                producto=producto,
                cantidad=cantidad
            )

            messages.success(request, f"¡Reserva #{nueva_reserva.id} creada con éxito! Te esperamos el {fecha_retiro}.")
            return redirect('catalogo')

        except Exception as e:
            # Si algo falla (ej. base de datos caída), deshace todo para no dejar datos corruptos
            messages.error(request, f"Ocurrió un error al procesar la reserva: {str(e)}")
            return redirect('catalogo')