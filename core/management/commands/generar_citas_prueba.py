# core/management/commands/generar_citas_prueba.py
from django.core.management.base import BaseCommand
from core.models import Paciente, Doctor, Cita, Usuario
from datetime import datetime, timedelta
import random

class Command(BaseCommand):
    help = 'Genera citas de prueba para visualizar el calendario (20 citas distribuidas en el mes)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--cantidad',
            type=int,
            default=20,
            help='Cantidad de citas a generar (default: 20)'
        )
        parser.add_argument(
            '--mes',
            type=str,
            default=None,
            help='Mes en formato YYYY-MM (default: mes actual)'
        )
        parser.add_argument(
            '--limpiar',
            action='store_true',
            help='Eliminar citas existentes antes de generar nuevas'
        )

    def handle(self, *args, **kwargs):
        cantidad = kwargs['cantidad']
        mes_str = kwargs['mes']
        limpiar = kwargs['limpiar']
        
        self.stdout.write(self.style.SUCCESS('\n' + '='*70))
        self.stdout.write(self.style.SUCCESS('📅 GENERADOR DE CITAS DE PRUEBA'))
        self.stdout.write(self.style.SUCCESS('='*70 + '\n'))
        
        # Determinar el mes a usar
        if mes_str:
            try:
                año, mes = map(int, mes_str.split('-'))
                fecha_base = datetime(año, mes, 1)
            except ValueError:
                self.stdout.write(self.style.ERROR('❌ Formato de mes inválido. Usa YYYY-MM (ej: 2026-03)'))
                return
        else:
            fecha_base = datetime.now()
            año, mes = fecha_base.year, fecha_base.month
        
        self.stdout.write(f'📆 Generando citas para: {año}-{mes:02d}\n')
        
        # Obtener datos necesarios
        pacientes = list(Paciente.objects.filter(activo=True))
        doctores = list(Doctor.objects.filter(activo=True))
        
        if not pacientes:
            self.stdout.write(self.style.ERROR('❌ No hay pacientes activos. Ejecuta primero: python3 manage.py reset_pacientes'))
            return
        
        if not doctores:
            self.stdout.write(self.style.ERROR('❌ No hay doctores activos. Ejecuta primero: python3 manage.py crear_usuarios'))
            return
        
        self.stdout.write(f'✅ Pacientes disponibles: {len(pacientes)}')
        self.stdout.write(f'✅ Doctores disponibles: {len(doctores)}\n')
        
        # Limpiar citas existentes si se solicita
        if limpiar:
            confirmacion = input(self.style.WARNING(f'¿Eliminar todas las citas existentes? (yes/no): '))
            if confirmacion.lower() == 'yes':
                eliminadas = Cita.objects.all().count()
                Cita.objects.all().delete()
                self.stdout.write(self.style.SUCCESS(f'🗑️  {eliminadas} citas eliminadas\n'))
            else:
                self.stdout.write(self.style.WARNING('⚠️  Operación cancelada. Se agregarán nuevas citas sin eliminar las existentes.\n'))
        
        # Motivos de consulta realistas
        motivos = [
            'Consulta de seguimiento',
            'Control de presión arterial',
            'Evaluación de dolor abdominal',
            'Chequeo general anual',
            'Consulta por gripe',
            'Control de diabetes',
            'Evaluación de dolor de cabeza',
            'Revisión de resultados de laboratorio',
            'Consulta dermatológica',
            'Control prenatal',
            'Evaluación de dolor de espalda',
            'Consulta por alergia',
            'Control de colesterol',
            'Evaluación de fatiga crónica',
            'Consulta de salud mental',
            'Revisión de medicación',
            'Consulta por dolor articular',
            'Control de peso',
            'Evaluación de problemas digestivos',
            'Consulta de vacunación',
        ]
        
        # Estados de cita con pesos (más programadas para ver el calendario activo)
        estados_pesos = [
            ('PROGRAMADA', 0.50),
            ('COMPLETADA', 0.30),
            ('EN_ESPERA', 0.15),
            ('CANCELADA', 0.05),
        ]
        estados = [e for e, p in estados_pesos]
        pesos = [p for e, p in estados_pesos]
        
        # Horarios disponibles (evitar muy temprano o muy tarde)
        horarios = [
            '08:00', '08:30', '09:00', '09:30', '10:00', '10:30',
            '11:00', '11:30', '14:00', '14:30', '15:00', '15:30',
            '16:00', '16:30', '17:00', '17:30'
        ]
        
        # Diagnósticos para citas completadas
        diagnosticos = [
            'Hipertensión arterial esencial. Se ajusta medicación.',
            'Gastroenteritis aguda. Hidratación y dieta blanda.',
            'Infección de vías respiratorias altas. Antibiótico prescrito.',
            'Control normal. Continuar con estilo de vida saludable.',
            'Dermatitis de contacto. Crema tópica indicada.',
            'Migraña tensional. Manejo del estrés y analgésicos.',
            'Dislipidemia. Recomendaciones dietéticas y ejercicio.',
            'Ansiedad leve. Técnicas de relajación y seguimiento.',
            'Artrosis de rodilla. Fisioterapia y antiinflamatorios.',
            'Rinitis alérgica estacional. Antihistamínico prescrito.',
        ]
        
        citas_creadas = []
        fechas_usadas = set()  # Para evitar duplicados exactos
        
        for i in range(1, cantidad + 1):
            # Generar fecha aleatoria en el mes
            while True:
                dia = random.randint(1, 28)  # Evitar problemas con meses de 30/31 días
                fecha_cita = datetime(año, mes, dia)
                clave_fecha = f"{fecha_cita.date()}"
                if clave_fecha not in fechas_usadas or len(fechas_usadas) >= 20:
                    fechas_usadas.add(clave_fecha)
                    break
            
            # Hora aleatoria
            hora_str = random.choice(horarios)
            hora = datetime.strptime(hora_str, '%H:%M').time()
            
            # Seleccionar paciente y doctor aleatorios
            paciente = random.choice(pacientes)
            doctor = random.choice(doctores)
            
            # Estado aleatorio con pesos
            estado = random.choices(estados, weights=pesos)[0]
            
            # Motivo aleatorio
            motivo = random.choice(motivos)
            
            # Diagnóstico solo si está completada
            diagnostico = None
            if estado == 'COMPLETADA':
                diagnostico = random.choice(diagnosticos)
            
            # Usuario que crea la cita (simular)
            creador = Usuario.objects.filter(rol__in=['ADMIN', 'JEFE', 'ASISTENTE']).first()
            
            # Crear cita
            try:
                # Verificar que no exista cita exacta (mismo doctor, fecha, hora)
                if not Cita.objects.filter(
                    doctor=doctor,
                    fecha=fecha_cita.date(),
                    hora=hora,
                    estado__in=['PROGRAMADA', 'EN_ESPERA']
                ).exists():
                    cita = Cita.objects.create(
                        paciente=paciente,
                        doctor=doctor,
                        fecha=fecha_cita.date(),
                        hora=hora,
                        motivo=motivo,
                        estado=estado,
                        diagnostico=diagnostico,
                        creado_por=creador or Usuario.objects.first()
                    )
                    citas_creadas.append(cita)
                    
                    # Mostrar progreso
                    estado_emoji = {'PROGRAMADA': '🔵', 'COMPLETADA': '🟢', 'EN_ESPERA': '🟠', 'CANCELADA': '🔴'}
                    self.stdout.write(
                        f"   ✓ [{i:2d}] {fecha_cita.strftime('%d/%m')} {hora_str} | "
                        f"{estado_emoji[estado]} {estado:12s} | "
                        f"{paciente.nombre[:25]:25s} | Dr(a). {doctor.nombre.split()[-1]}"
                    )
                else:
                    self.stdout.write(f"   ⚠️  [{i:2d}] Horario ocupado, saltando...")
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"   ❌ Error creando cita {i}: {str(e)}"))
        
        # Resumen final
        self.stdout.write(self.style.SUCCESS(f'\n✅ ¡GENERACIÓN COMPLETADA!'))
        self.stdout.write(self.style.SUCCESS(f'   Citas creadas exitosamente: {len(citas_creadas)}'))
        
        if citas_creadas:
            # Estadísticas por estado
            self.stdout.write(self.style.SUCCESS(f'\n📊 DISTRIBUCIÓN POR ESTADO:'))
            for estado in estados:
                count = Cita.objects.filter(estado=estado).count()
                total = Cita.objects.count()
                porcentaje = (count * 100 // total) if total > 0 else 0
                barra = '█' * (porcentaje // 5)
                self.stdout.write(f'   {estado:12s}: {count:3d} ({porcentaje:2d}%) {barra}')
            
            # Citas por doctor
            self.stdout.write(self.style.SUCCESS(f'\n👨‍⚕️ CITAS POR DOCTOR:'))
            for doctor in doctores[:5]:  # Mostrar primeros 5
                count = Cita.objects.filter(doctor=doctor).count()
                if count > 0:
                    self.stdout.write(f'   {doctor.nombre:30s}: {count} citas')
            
            # Rango de fechas
            fechas_citas = Cita.objects.values_list('fecha', flat=True).order_by('fecha')
            if fechas_citas:
                self.stdout.write(self.style.SUCCESS(f'\n📅 RANGO DE FECHAS:'))
                self.stdout.write(f'   Primera cita: {fechas_citas.first().strftime("%d/%m/%Y")}')
                self.stdout.write(f'   Última cita:  {fechas_citas.last().strftime("%d/%m/%Y")}')
        
        self.stdout.write(self.style.SUCCESS(f'\n🌐 URL PARA VER CALENDARIO:'))
        self.stdout.write(self.style.SUCCESS(f'   http://127.0.0.1:8000/calendario/'))
        self.stdout.write(self.style.SUCCESS('='*70 + '\n'))