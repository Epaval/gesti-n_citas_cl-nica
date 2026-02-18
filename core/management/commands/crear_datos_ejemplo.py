# core/management/commands/crear_datos_ejemplo.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from core.models import Usuario, Paciente, Doctor, Cita
from datetime import datetime, timedelta

class Command(BaseCommand):
    help = 'Crea datos de ejemplo para desarrollo'

    def handle(self, *args, **kwargs):
        self.stdout.write('🔄 Creando datos de ejemplo...')

        # ==================== USUARIOS ====================
        usuarios_data = [
            {'username': 'admin', 'email': 'admin@consultorio.com', 'rol': 'ADMIN', 'password': 'Admin123!'},
            {'username': 'jefe', 'email': 'jefe@consultorio.com', 'rol': 'JEFE', 'password': 'Jefe123!'},
            {'username': 'medico1', 'email': 'medico1@consultorio.com', 'rol': 'MEDICO', 'password': 'Medico123!'},
            {'username': 'medico2', 'email': 'medico2@consultorio.com', 'rol': 'MEDICO', 'password': 'Medico123!'},
            {'username': 'asistente', 'email': 'asistente@consultorio.com', 'rol': 'ASISTENTE', 'password': 'Asistente123!'},
        ]

        for user_data in usuarios_data:
            user, created = Usuario.objects.get_or_create(
                username=user_data['username'],
                defaults={
                    'email': user_data['email'],
                    'rol': user_data['rol'],
                    'first_name': user_data['username'].title(),
                    'last_name': 'Usuario',
                }
            )
            if created:
                user.set_password(user_data['password'])
                user.save()
                self.stdout.write(f'✓ Usuario creado: {user.username} ({user.get_rol_display()})')

        # ==================== PACIENTES ====================
        pacientes_data = [
            {'nombre': 'Juan Pérez García', 'edad': 45, 'telefono': '555-0101', 'email': 'juan.perez@email.com'},
            {'nombre': 'María López Hernández', 'edad': 32, 'telefono': '555-0102', 'email': 'maria.lopez@email.com'},
            {'nombre': 'Carlos Rodríguez Sánchez', 'edad': 28, 'telefono': '555-0103', 'email': 'carlos.rodriguez@email.com'},
            {'nombre': 'Ana Martínez Torres', 'edad': 55, 'telefono': '555-0104', 'email': 'ana.martinez@email.com'},
            {'nombre': 'Luis González Ramírez', 'edad': 40, 'telefono': '555-0105', 'email': 'luis.gonzalez@email.com'},
            {'nombre': 'Patricia Díaz Flores', 'edad': 35, 'telefono': '555-0106', 'email': 'patricia.diaz@email.com'},
            {'nombre': 'Roberto Silva Mendoza', 'edad': 62, 'telefono': '555-0107', 'email': 'roberto.silva@email.com'},
            {'nombre': 'Carmen Ruiz Castillo', 'edad': 29, 'telefono': '555-0108', 'email': 'carmen.ruiz@email.com'},
        ]

        for paciente_data in pacientes_data:
            paciente, created = Paciente.objects.get_or_create(
                email=paciente_data['email'],
                defaults=paciente_data
            )
            if created:
                self.stdout.write(f'✓ Paciente creado: {paciente.nombre}')

        # ==================== DOCTORES ====================
        doctores_data = [
            {'nombre': 'Dra. Ana García', 'especialidad': 'CARDIOLOGIA', 'telefono': '555-1001', 'costo_consulta': 800.00},
            {'nombre': 'Dr. Carlos Rodríguez', 'especialidad': 'PEDIATRIA', 'telefono': '555-1002', 'costo_consulta': 600.00},
            {'nombre': 'Dra. María López', 'especialidad': 'DERMATOLOGIA', 'telefono': '555-1003', 'costo_consulta': 700.00},
            {'nombre': 'Dr. José Hernández', 'especialidad': 'CARDIOLOGIA', 'telefono': '555-1004', 'costo_consulta': 850.00},
            {'nombre': 'Dra. Laura Sánchez', 'especialidad': 'GENERAL', 'telefono': '555-1005', 'costo_consulta': 500.00},
        ]

        for doctor_data in doctores_data:
            doctor, created = Doctor.objects.get_or_create(
                nombre=doctor_data['nombre'],
                defaults=doctor_data
            )
            if created:
                self.stdout.write(f'✓ Doctor creado: {doctor.nombre} ({doctor.get_especialidad_display()})')

        # ==================== CITAS ====================
        pacientes = list(Paciente.objects.all()[:6])
        doctores = list(Doctor.objects.all())
        
        hoy = timezone.now().date()
        motivos = [
            'Consulta general',
            'Seguimiento de tratamiento',
            'Chequeo preventivo',
            'Dolor de cabeza persistente',
            'Revisión de resultados',
            'Vacunación',
        ]

        citas_data = []
        for i in range(10):
            cita = Cita.objects.create(
                paciente=pacientes[i % len(pacientes)],
                doctor=doctores[i % len(doctores)],
                fecha=hoy + timedelta(days=i % 7),
                hour=(8 + (i % 10)),
                hora=f"{8 + (i % 10):02d}:00:00",
                motivo=motivos[i % len(motivos)],
                estado=['PROGRAMADA', 'PROGRAMADA', 'COMPLETADA', 'CANCELADA'][i % 4],
                creado_por=Usuario.objects.filter(rol='ASISTENTE').first(),
            )
            if i % 4 == 2:  # Completadas
                cita.diagnostico = 'Paciente en buen estado. Continuar tratamiento.'
                cita.save()
            self.stdout.write(f'✓ Cita creada: {cita.paciente.nombre} con {cita.doctor.nombre}')

        self.stdout.write(self.style.SUCCESS('\n✅ ¡Datos de ejemplo creados exitosamente!'))
        self.stdout.write(self.style.WARNING('\n📋 Credenciales de acceso:'))
        self.stdout.write('   Admin: admin / Admin123!')
        self.stdout.write('   Jefe: jefe / Jefe123!')
        self.stdout.write('   Médico: medico1 / Medico123!')
        self.stdout.write('   Asistente: asistente / Asistente123!')