# core/management/commands/crear_usuarios.py

from django.core.management.base import BaseCommand
from core.models import Usuario, Doctor, Especialidad
from datetime import date, timedelta
import random

class Command(BaseCommand):
    help = 'Crea usuarios de prueba: Admins, Jefes Médicos, Médicos y Asistentes'

    def add_arguments(self, parser):
        parser.add_argument(
            '--admins',
            type=int,
            default=3,
            help='Cantidad de administradores (default: 3)'
        )
        parser.add_argument(
            '--jefes',
            type=int,
            default=3,
            help='Cantidad de jefes médicos (default: 3)'
        )
        parser.add_argument(
            '--medicos',
            type=int,
            default=20,
            help='Cantidad de médicos (default: 20)'
        )
        parser.add_argument(
            '--asistentes',
            type=int,
            default=5,
            help='Cantidad de asistentes (default: 5)'
        )
        parser.add_argument(
            '--password',
            type=str,
            default='prueba12345',
            help='Contraseña para todos los usuarios (default: prueba12345)'
        )

    def handle(self, *args, **kwargs):
        password = kwargs['password']
        
        self.stdout.write(self.style.SUCCESS('\n' + '='*70))
        self.stdout.write(self.style.SUCCESS('🏥 SISTEMA DE GESTIÓN DE CITAS MÉDICAS'))
        self.stdout.write(self.style.SUCCESS('👥 CREACIÓN DE USUARIOS DE PRUEBA'))
        self.stdout.write(self.style.SUCCESS('='*70 + '\n'))
        
        self.stdout.write(self.style.WARNING(f'⚠️  CONTRASEÑA PARA TODOS: {password}'))
        self.stdout.write(self.style.WARNING('   ⚠️  SOLO PARA DESARROLLO - NO USAR EN PRODUCCIÓN\n'))
        
        # Confirmación
        confirmacion = input(self.style.WARNING('¿Continuar con la creación de usuarios? (yes/no): '))
        if confirmacion.lower() != 'yes':
            self.stdout.write(self.style.ERROR('❌ Operación cancelada'))
            return
        
        # ✅ VERIFICAR QUE HAY ESPECIALIDADES EN LA BD
        especialidades = list(Especialidad.objects.filter(activa=True))
        if not especialidades:
            self.stdout.write(self.style.ERROR('\n❌ No hay especialidades en la base de datos'))
            self.stdout.write(self.style.WARNING('   Primero crea especialidades o ejecuta:'))
            self.stdout.write(self.style.WARNING('   python3 manage.py shell\n'))
            self.stdout.write(self.style.WARNING('   >>> from core.models import Especialidad'))
            self.stdout.write(self.style.WARNING('   >>> Especialidad.objects.create(nombre="Medicina General", nombre_corto="GENERAL")'))
            self.stdout.write(self.style.WARNING('   >>> exit()\n'))
            return
        
        self.stdout.write(self.style.SUCCESS(f'✅ Especialidades disponibles: {len(especialidades)}'))
        
        # Datos de prueba para Venezuela
        nombres_masculinos = [
            'Carlos', 'José', 'Luis', 'Miguel', 'Antonio', 'Manuel', 'Pedro',
            'Juan', 'Rafael', 'Ángel', 'Fernando', 'Roberto', 'Jorge', 'Daniel',
            'Alejandro', 'Ricardo', 'Alberto', 'Eduardo', 'Francisco', 'David',
            'Andrés', 'Raúl', 'Héctor', 'Gustavo', 'Ramón', 'Enrique', 'Oscar'
        ]
        
        nombres_femeninos = [
            'María', 'Carmen', 'Ana', 'Isabel', 'Laura', 'Sofía', 'Lucía',
            'Paula', 'Andrea', 'Marta', 'Sara', 'Elena', 'Cristina', 'Beatriz',
            'Rosa', 'Dolores', 'Pilar', 'Silvia', 'Patricia', 'Gabriela',
            'Valentina', 'Camila', 'Mariana', 'Alejandra', 'Verónica', 'Adriana'
        ]
        
        apellidos = [
            'García', 'Rodríguez', 'López', 'Martínez', 'González', 'Hernández',
            'Pérez', 'Sánchez', 'Ramírez', 'Torres', 'Flores', 'Rivera', 'Gómez',
            'Díaz', 'Moreno', 'Muñoz', 'Álvarez', 'Romero', 'Alonso', 'Gutiérrez',
            'Vargas', 'Castro', 'Ortega', 'Delgado', 'Jiménez', 'Ruiz', 'Mendoza',
            'Silva', 'Contreras', 'Medina', 'Aguilar', 'Cortez', 'León', 'Reyes'
        ]
        
        usuarios_creados = {
            'ADMIN': [],
            'JEFE': [],
            'MEDICO': [],
            'ASISTENTE': []
        }
        
        # ==================== ADMINISTRADORES ====================
        self.stdout.write(self.style.SUCCESS('\n' + '='*70))
        self.stdout.write(self.style.SUCCESS('📊 CREANDO ADMINISTRADORES'))
        self.stdout.write(self.style.SUCCESS('='*70))
        
        for i in range(1, kwargs['admins'] + 1):
            username = f'admin{i:02d}'
            nombre = random.choice(nombres_masculinos + nombres_femeninos)
            apellido = random.choice(apellidos)
            email = f'{username}@consultorio.com'
            
            if Usuario.objects.filter(username=username).exists():
                self.stdout.write(self.style.WARNING(f'   ⚠️  {username} ya existe, saltando...'))
                continue
            
            usuario = Usuario.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=nombre,
                last_name=apellido,
                rol='ADMIN',
                telefono=f'0412-{random.randint(1000000, 9999999)}'
            )
            
            usuarios_creados['ADMIN'].append(usuario)
            self.stdout.write(
                self.style.SUCCESS(f'   ✓ [{i:2d}] {username:15s} | {nombre} {apellido:20s} | {email}')
            )
        
        # ==================== JEFES MÉDICOS ====================
        self.stdout.write(self.style.SUCCESS('\n' + '='*70))
        self.stdout.write(self.style.SUCCESS('👨‍⚕️ CREANDO JEFES MÉDICOS'))
        self.stdout.write(self.style.SUCCESS('='*70))
        
        for i in range(1, kwargs['jefes'] + 1):
            username = f'jefe{i:02d}'
            nombre = random.choice(nombres_masculinos + nombres_femeninos)
            apellido = random.choice(apellidos)
            email = f'{username}@consultorio.com'
            
            if Usuario.objects.filter(username=username).exists():
                self.stdout.write(self.style.WARNING(f'   ⚠️  {username} ya existe, saltando...'))
                continue
            
            usuario = Usuario.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=nombre,
                last_name=apellido,
                rol='JEFE',
                telefono=f'0414-{random.randint(1000000, 9999999)}'
            )
            
            # ✅ Crear perfil de doctor con especialidad dinámica
            especialidad = random.choice(especialidades)
            doctor = Doctor.objects.create(
                nombre=f'Dr(a). {nombre} {apellido}',
                especialidad=especialidad,  # ✅ Ahora es ForeignKey
                telefono=f'0212-{random.randint(1000000, 9999999)}',
                costo_consulta=random.choice([500, 600, 700, 800, 900, 1000]),
                usuario=usuario,
                activo=True
            )
            
            usuarios_creados['JEFE'].append(usuario)
            self.stdout.write(
                self.style.SUCCESS(f'   ✓ [{i:2d}] {username:15s} | {nombre} {apellido:20s} | {especialidad.nombre}')
            )
        
        # ==================== MÉDICOS ====================
        self.stdout.write(self.style.SUCCESS('\n' + '='*70))
        self.stdout.write(self.style.SUCCESS('🩺 CREANDO MÉDICOS'))
        self.stdout.write(self.style.SUCCESS('='*70))
        
        for i in range(1, kwargs['medicos'] + 1):
            username = f'medico{i:02d}'
            nombre = random.choice(nombres_masculinos + nombres_femeninos)
            apellido = random.choice(apellidos)
            email = f'{username}@consultorio.com'
            
            if Usuario.objects.filter(username=username).exists():
                self.stdout.write(self.style.WARNING(f'   ⚠️  {username} ya existe, saltando...'))
                continue
            
            # ✅ Asignar especialidad rotativa de la lista dinámica
            especialidad = especialidades[i % len(especialidades)]
            
            usuario = Usuario.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=nombre,
                last_name=apellido,
                rol='MEDICO',
                telefono=f'0416-{random.randint(1000000, 9999999)}'
            )
            
            # ✅ Crear perfil de doctor con especialidad dinámica
            doctor = Doctor.objects.create(
                nombre=f'Dr(a). {nombre} {apellido}',
                especialidad=especialidad,  # ✅ Ahora es ForeignKey
                telefono=f'0241-{random.randint(1000000, 9999999)}',
                costo_consulta=random.choice([400, 500, 600, 700, 800]),
                usuario=usuario,
                activo=True
            )
            
            usuarios_creados['MEDICO'].append(usuario)
            self.stdout.write(
                self.style.SUCCESS(f'   ✓ [{i:2d}] {username:15s} | {nombre} {apellido:20s} | {especialidad.nombre}')
            )
        
        # ==================== ASISTENTES ====================
        self.stdout.write(self.style.SUCCESS('\n' + '='*70))
        self.stdout.write(self.style.SUCCESS('📋 CREANDO ASISTENTES'))
        self.stdout.write(self.style.SUCCESS('='*70))
        
        for i in range(1, kwargs['asistentes'] + 1):
            username = f'asistente{i:02d}'
            nombre = random.choice(nombres_femeninos)
            apellido = random.choice(apellidos)
            email = f'{username}@consultorio.com'
            
            if Usuario.objects.filter(username=username).exists():
                self.stdout.write(self.style.WARNING(f'   ⚠️  {username} ya existe, saltando...'))
                continue
            
            usuario = Usuario.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=nombre,
                last_name=apellido,
                rol='ASISTENTE',
                telefono=f'0424-{random.randint(1000000, 9999999)}'
            )
            
            usuarios_creados['ASISTENTE'].append(usuario)
            self.stdout.write(
                self.style.SUCCESS(f'   ✓ [{i:2d}] {username:15s} | {nombre} {apellido:20s} | {email}')
            )
        
        # ==================== RESUMEN FINAL ====================
        self.stdout.write(self.style.SUCCESS('\n' + '='*70))
        self.stdout.write(self.style.SUCCESS('✅ ¡CREACIÓN COMPLETADA!'))
        self.stdout.write(self.style.SUCCESS('='*70))
        
        total = sum(len(v) for v in usuarios_creados.values())
        self.stdout.write(self.style.SUCCESS(f'\n📊 RESUMEN DE USUARIOS CREADOS: {total}'))
        self.stdout.write(f'\n   👤 ADMINISTRADORES:  {len(usuarios_creados["ADMIN"])}')
        self.stdout.write(f'   👨‍⚕️ JEFES MÉDICOS:     {len(usuarios_creados["JEFE"])}')
        self.stdout.write(f'   🩺 MÉDICOS:           {len(usuarios_creados["MEDICO"])}')
        self.stdout.write(f'   📋 ASISTENTES:        {len(usuarios_creados["ASISTENTE"])}')
        
        self.stdout.write(self.style.SUCCESS(f'\n🔐 CREDENCIALES DE ACCESO:'))
        self.stdout.write(self.style.WARNING(f'   Contraseña: {password}'))
        
        self.stdout.write(self.style.SUCCESS(f'\n📋 PRIMEROS USUARIOS DE CADA ROL:'))
        self.stdout.write('\n   ' + '-'*60)
        self.stdout.write('   {:<20} {:<15} {:<15}'.format('USERNAME', 'ROL', 'CONTRASEÑA'))
        self.stdout.write('   ' + '-'*60)
        
        for rol, usuarios in usuarios_creados.items():
            for usuario in usuarios[:3]:  # Mostrar primeros 3 de cada rol
                self.stdout.write('   {:<20} {:<15} {:<15}'.format(
                    usuario.username, 
                    usuario.get_rol_display(), 
                    password
                ))
        
        if any(len(v) > 3 for v in usuarios_creados.values()):
            self.stdout.write('   ... (más usuarios creados, ver lista completa en admin)')
        
        self.stdout.write('   ' + '-'*60 + '\n')
        
        # Estadísticas de doctores por especialidad
        self.stdout.write(self.style.SUCCESS(f'\n📊 DISTRIBUCIÓN DE DOCTORES POR ESPECIALIDAD:'))
        for esp in Especialidad.objects.all():
            num_doctores = esp.doctores.count()
            if num_doctores > 0:
                self.stdout.write(f'   {esp.nombre:25s}: {num_doctores} doctores')
        
        self.stdout.write(self.style.SUCCESS(f'\n🌐 URL DE ACCESO: http://127.0.0.1:8000/'))
        self.stdout.write(self.style.SUCCESS('='*70 + '\n'))
