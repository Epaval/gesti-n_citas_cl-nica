# core/management/commands/reset_pacientes.py
from django.core.management.base import BaseCommand
from core.models import Paciente
from datetime import date, timedelta
import random

class Command(BaseCommand):
    help = 'Elimina todos los pacientes existentes y crea nuevos datos de prueba'

    def add_arguments(self, parser):
        parser.add_argument(
            '--cantidad',
            type=int,
            default=20,
            help='Cantidad de pacientes a crear (default: 20)'
        )

    def handle(self, *args, **kwargs):
        cantidad = kwargs['cantidad']
        
        self.stdout.write(self.style.WARNING(f'\n🗑️  ELIMINANDO TODOS LOS PACIENTES EXISTENTES...'))
        
        # Contar pacientes actuales
        total_actual = Paciente.objects.count()
        
        if total_actual > 0:
            self.stdout.write(f'   Encontrados {total_actual} pacientes existentes')
            confirmacion = input(self.style.WARNING(f'   ¿Estás seguro de eliminarlos? (yes/no): '))
            
            if confirmacion.lower() != 'yes':
                self.stdout.write(self.style.ERROR('❌ Operación cancelada'))
                return
            
            # Eliminar todos los pacientes
            Paciente.objects.all().delete()
            self.stdout.write(self.style.SUCCESS(f'   ✓ {total_actual} pacientes eliminados'))
        else:
            self.stdout.write('   No hay pacientes existentes')
        
        self.stdout.write(self.style.SUCCESS('\n📝 CREANDO NUEVOS PACIENTES DE PRUEBA...\n'))
        
        # Datos de prueba realistas para Venezuela
        nombres_masculinos = [
            'Carlos', 'José', 'Luis', 'Miguel', 'Antonio', 'Manuel', 'Pedro', 
            'Juan', 'Rafael', 'Ángel', 'Fernando', 'Roberto', 'Jorge', 'Daniel',
            'Alejandro', 'Ricardo', 'Alberto', 'Eduardo', 'Francisco', 'David'
        ]
        
        apellidos = [
            'García', 'Rodríguez', 'López', 'Martínez', 'González', 'Hernández',
            'Pérez', 'Sánchez', 'Ramírez', 'Torres', 'Flores', 'Rivera', 'Gómez',
            'Díaz', 'Moreno', 'Muñoz', 'Álvarez', 'Romero', 'Alonso', 'Gutiérrez',
            'Vargas', 'Castro', 'Ortega', 'Delgado', 'Jiménez', 'Ruiz', 'Mendoza',
            'Silva', 'Contreras', 'Medina', 'Aguilar', 'Cortez', 'León', 'Reyes'
        ]
        
        nombres_femeninos = [
            'María', 'Carmen', 'Ana', 'Isabel', 'Laura', 'Sofía', 'Lucía', 
            'Paula', 'Andrea', 'Marta', 'Sara', 'Elena', 'Cristina', 'Beatriz',
            'Rosa', 'Dolores', 'Pilar', 'Javier', 'Silvia', 'Patricia'
        ]
        
        ciudades_venezuela = [
            'Caracas', 'Maracaibo', 'Valencia', 'Barquisimeto', 'Maracay',
            'Ciudad Guayana', 'Barcelona', 'Maturín', 'San Cristóbal', 'Cumaná',
            'Mérida', 'Cabimas', 'Turmero', 'Ciudad Bolívar', 'Punto Fijo',
            'Los Teques', 'Guanare', 'Coro', 'Acarigua', 'Carúpano'
        ]
        
        estados_venezuela = [
            'Distrito Capital', 'Zulia', 'Carabobo', 'Lara', 'Aragua',
            'Bolívar', 'Anzoátegui', 'Monagas', 'Táchira', 'Sucre',
            'Mérida', 'Miranda', 'Portuguesa', 'Falcón', 'Yaracuy'
        ]
        
        # Prefijos de cédula venezolanos
        prefijos_ci = ['V', 'V', 'V', 'V', 'E']  # 80% venezolanos, 20% extranjeros
        
        pacientes_creados = []
        
        for i in range(1, cantidad + 1):
            # Generar sexo aleatorio
            sexo = random.choice(['M', 'F'])
            
            # Generar nombre completo
            if sexo == 'M':
                nombre = f"{random.choice(nombres_masculinos)} {random.choice(apellidos)} {random.choice(apellidos)}"
            else:
                nombre = f"{random.choice(nombres_femeninos)} {random.choice(apellidos)} {random.choice(apellidos)}"
            
            # Generar CI única
            prefijo = random.choice(prefijos_ci)
            numero_ci = random.randint(1000000, 99999999)
            ci = f"{prefijo}-{numero_ci}"
            
            # Verificar que la CI no exista (reintentar si existe)
            while Paciente.objects.filter(ci=ci).exists():
                numero_ci = random.randint(1000000, 99999999)
                ci = f"{prefijo}-{numero_ci}"
            
            # Generar fecha de nacimiento (edades entre 1 y 90 años)
            dias_edad = random.randint(365, 365 * 90)
            fecha_nacimiento = date.today() - timedelta(days=dias_edad)
            
            # Generar teléfono venezolano
            tipo_telefono = random.choice(['movil', 'fijo'])
            if tipo_telefono == 'movil':
                operador = random.choice(['412', '414', '416', '424', '426'])
                telefono = f"0{operador}-{random.randint(1000000, 9999999)}"
            else:
                area = random.choice(['212', '241', '251', '261', '271', '281', '291'])
                telefono = f"0{area}-{random.randint(1000000, 9999999)}"
            
            # Teléfono alternativo (opcional)
            telefono_alt = ""
            if random.random() > 0.3:  # 70% tiene teléfono alternativo
                if random.choice(['movil', 'fijo']) == 'movil':
                    operador = random.choice(['412', '414', '416', '424', '426'])
                    telefono_alt = f"0{operador}-{random.randint(1000000, 9999999)}"
                else:
                    area = random.choice(['212', '241', '251', '261', '271', '281', '291'])
                    telefono_alt = f"0{area}-{random.randint(1000000, 9999999)}"
            
            # Generar email
            email_parts = nombre.lower().split()
            if len(email_parts) >= 2:
                email = f"{email_parts[0]}.{email_parts[1]}@email.com"
            else:
                email = f"paciente{i}@email.com"
            
            # Generar dirección
            ciudad = random.choice(ciudades_venezuela)
            estado = random.choice(estados_venezuela)
            direccion = f"{ciudad}, Edo. {estado}"
            
            # Crear paciente
            paciente = Paciente.objects.create(
                ci=ci,
                nombre=nombre,
                sexo=sexo,
                fecha_nacimiento=fecha_nacimiento,
                telefono=telefono,
                telefono_alternativo=telefono_alt,
                email=email,
                direccion=direccion,
                activo=True
            )
            
            pacientes_creados.append(paciente)
            
            # Mostrar progreso
            edad = paciente.edad
            self.stdout.write(
                f"   ✓ [{i:3d}/{cantidad}] {paciente.ci} | {paciente.nombre:40s} | {edad:3d} años | {sexo}"
            )
        
        # Resumen final
        self.stdout.write(self.style.SUCCESS(f'\n✅ ¡COMPLETADO!'))
        self.stdout.write(self.style.SUCCESS(f'   Total de pacientes creados: {len(pacientes_creados)}'))
        self.stdout.write(self.style.SUCCESS(f'   Total en base de datos: {Paciente.objects.count()}'))
        
        # Estadísticas
        total = Paciente.objects.count()
        masculinos = Paciente.objects.filter(sexo='M').count()
        femeninos = Paciente.objects.filter(sexo='F').count()
        venezolanos = Paciente.objects.filter(ci__startswith='V').count()
        extranjeros = Paciente.objects.filter(ci__startswith='E').count()
        
        self.stdout.write(self.style.SUCCESS(f'\n📊 ESTADÍSTICAS:'))
        self.stdout.write(f'   Hombres: {masculinos} ({masculinos*100//total}%)')
        self.stdout.write(f'   Mujeres: {femeninos} ({femeninos*100//total}%)')
        self.stdout.write(f'   Venezolanos: {venezolanos} ({venezolanos*100//total}%)')
        self.stdout.write(f'   Extranjeros: {extranjeros} ({extranjeros*100//total}%)')
        
        # Rango de edades
        edades = [p.edad for p in Paciente.objects.all()]
        self.stdout.write(f'   Edad promedio: {sum(edades)//len(edades)} años')
        self.stdout.write(f'   Edad mínima: {min(edades)} años')
        self.stdout.write(f'   Edad máxima: {max(edades)} años')