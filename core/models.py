# core/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

# ==================== MODELO DE USUARIO (ROLES) ====================
class Usuario(AbstractUser):
    ROLES = (
        ('ADMIN', 'Administrador'),
        ('JEFE', 'Jefe de Médicos'),
        ('MEDICO', 'Médico'),
        ('ASISTENTE', 'Asistente'),
    )
    rol = models.CharField(max_length=10, choices=ROLES, default='ASISTENTE')
    telefono = models.CharField(max_length=20, blank=True)
    foto_perfil = models.ImageField(upload_to='perfiles/', null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'

    def __str__(self):
        return f"{self.username} - {self.get_rol_display()}"

    def es_admin(self):
        return self.rol == 'ADMIN'

    def es_jefe(self):
        return self.rol in ['ADMIN', 'JEFE']

    def es_medico(self):
        return self.rol in ['ADMIN', 'JEFE', 'MEDICO']

    def es_asistente(self):
        return self.rol in ['ADMIN', 'JEFE', 'MEDICO', 'ASISTENTE']

# ==================== MODELO PACIENTE ====================
# core/models.py - Modelo Paciente ACTUALIZADO

class Paciente(models.Model):
    """
    Representa un paciente del consultorio médico.
    Incluye datos completos para identificación venezolana.
    """
    # ==================== DATOS DE IDENTIFICACIÓN ====================
    ci = models.CharField(
        max_length=20, 
        unique=True,
        null=True,
        blank=True,
        help_text="Cédula de Identidad (ej: V-12345678 o E-87654321)",
        verbose_name="Cédula de Identidad"
    )
    
    nombre = models.CharField(max_length=150, verbose_name="Nombre Completo")
    
    # Sexo: Opciones para Venezuela
    SEXO_CHOICES = [
        ('M', 'Masculino'),
        ('F', 'Femenino'),
        ('O', 'Otro'),
    ]
    sexo = models.CharField(
        max_length=1, 
        choices=SEXO_CHOICES, 
        default='M',
        verbose_name="Sexo"
    )
    
    # Fecha de nacimiento (la edad se calcula automáticamente)
    fecha_nacimiento = models.DateField(
        null=True,
        blank=True,
        verbose_name="Fecha de Nacimiento",
        help_text="DD/MM/AAAA - La edad se calculará automáticamente"
    )
    
    # ==================== CONTACTO ====================
    telefono = models.CharField(max_length=20, verbose_name="Teléfono")
    telefono_alternativo = models.CharField(max_length=20, blank=True, verbose_name="Teléfono Alternativo")
    email = models.EmailField(blank=True, verbose_name="Correo Electrónico")
    direccion = models.TextField(blank=True, verbose_name="Dirección")
    
    # ==================== ESTADO ====================
    fecha_registro = models.DateTimeField(auto_now_add=True)
    activo = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Paciente"
        verbose_name_plural = "Pacientes"
        ordering = ['nombre']
        indexes = [
            models.Index(fields=['ci']),
            models.Index(fields=['activo']),
        ]

    def __str__(self):
        return f"{self.nombre} ({self.get_ci_display()})"
    
    def get_ci_display(self):
        """Muestra la cédula con formato legible"""
        return f"{self.ci}"
    
    @property
    def edad(self):
        """
        Calcula la edad automáticamente basada en fecha_nacimiento.
        Retorna la edad en años completos.
        """
        from datetime import date
        if not self.fecha_nacimiento:
            return None
        
        today = date.today()
        edad = today.year - self.fecha_nacimiento.year
        
        # Ajustar si aún no ha cumplido años este año
        if (today.month, today.day) < (self.fecha_nacimiento.month, self.fecha_nacimiento.day):
            edad -= 1
        
        return edad
    
    @property
    def edad_str(self):
        """Retorna edad con formato legible"""
        edad = self.edad
        if edad is None:
            return "N/A"
        return f"{edad} año(s)"
   

# ==================== MODELO DOCTOR ====================
class Doctor(models.Model):
    ESPECIALIDADES = (
        ('CARDIOLOGIA', 'Cardiología'),
        ('PEDIATRIA', 'Pediatría'),
        ('DERMATOLOGIA', 'Dermatología'),
        ('GENERAL', 'Medicina General'),
    )
    
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE, related_name='perfil_medico', null=True, blank=True)
    nombre = models.CharField(max_length=100)
    especialidad = models.CharField(max_length=50, choices=ESPECIALIDADES)
    telefono = models.CharField(max_length=20)
    costo_consulta = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    activo = models.BooleanField(default=True)

    class Meta:
        ordering = ['nombre']

    def __str__(self):
        return f"Dr(a). {self.nombre} - {self.especialidad}"

# ==================== MODELO CITA ====================
class Cita(models.Model):
    ESTADOS = (
        ('PROGRAMADA', 'Programada'),
        ('EN_ESPERA', 'En Sala de Espera'),
        ('COMPLETADA', 'Completada'),
        ('CANCELADA', 'Cancelada'),
    )

    paciente = models.ForeignKey(Paciente, on_delete=models.PROTECT, related_name='citas')
    doctor = models.ForeignKey(Doctor, on_delete=models.PROTECT, related_name='citas')
    fecha = models.DateField()
    hora = models.TimeField()
    motivo = models.TextField()
    estado = models.CharField(max_length=20, choices=ESTADOS, default='PROGRAMADA')
    diagnostico = models.TextField(blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    creado_por = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, related_name='citas_creadas')

    class Meta:
        ordering = ['-fecha', '-hora']
        constraints = [
            models.UniqueConstraint(fields=['doctor', 'fecha', 'hora'], name='cita_unica_horario')
        ]

    def __str__(self):
        return f"Cita {self.id} - {self.paciente.nombre} con {self.doctor.nombre}"


# ==================== EXPEDIENTE MÉDICO ====================
class Expediente(models.Model):
    """
    Expediente médico único por paciente.
    Solo Médicos y Jefe Médico pueden acceder.
    """
    paciente = models.OneToOneField(
        Paciente, 
        on_delete=models.PROTECT, 
        related_name='expediente',
        unique=True
    )
    fecha_apertura = models.DateTimeField(auto_now_add=True)
    fecha_cierre = models.DateTimeField(null=True, blank=True)
    observaciones_generales = models.TextField(blank=True, help_text="Observaciones generales del expediente")
    alergias = models.TextField(blank=True, help_text="Alergias conocidas del paciente")
    medicamentos_actuales = models.TextField(blank=True, help_text="Medicamentos que toma actualmente")
    antecedentes = models.TextField(blank=True, help_text="Antecedentes médicos importantes")
    activo = models.BooleanField(default=True)
    creado_por = models.ForeignKey(Usuario, on_delete=models.PROTECT, related_name='expedientes_creados')
    modificado_por = models.ForeignKey(Usuario, on_delete=models.PROTECT, null=True, blank=True, related_name='expedientes_modificados')
    fecha_modificacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Expediente Médico'
        verbose_name_plural = 'Expedientes Médicos'
        permissions = [
            ('can_view_expediente', 'Puede ver expedientes médicos'),
            ('can_edit_expediente', 'Puede editar expedientes médicos'),
            ('can_activate_expediente', 'Puede activar/desactivar expedientes'),
        ]

    def __str__(self):
        return f"Expediente #{self.id} - {self.paciente.nombre}"

    def save(self, *args, **kwargs):
        # No permitir eliminación lógica desde aquí, usar campo activo
        if not self.pk and not self.creado_por:
            raise ValueError("Debe especificar quién crea el expediente")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # ⛔ BLOQUEAR eliminación física - solo soft delete con activo=False
        raise PermissionError("No está permitido eliminar expedientes médicos. Use el campo 'activo' para desactivar.")


# ==================== DIAGNÓSTICO ====================
class Diagnostico(models.Model):
    """
    Diagnóstico realizado por un médico a un paciente.
    Un expediente puede tener múltiples diagnósticos de diferentes médicos.
    """
    expediente = models.ForeignKey(
        Expediente, 
        on_delete=models.PROTECT, 
        related_name='diagnosticos',
        help_text="Expediente al que pertenece este diagnóstico"
    )
    doctor = models.ForeignKey(
        Doctor, 
        on_delete=models.PROTECT, 
        related_name='diagnosticos_realizados',
        help_text="Médico que realizó el diagnóstico"
    )
    cita = models.ForeignKey(
        Cita, 
        on_delete=models.SET_NULL, 
        null=True, blank=True,
        related_name='diagnosticos',
        help_text="Cita asociada (opcional)"
    )
    fecha = models.DateTimeField(auto_now_add=True)
    diagnostico_principal = models.CharField(max_length=255, help_text="Diagnóstico principal (CIE-10 recomendado)")
    descripcion = models.TextField(help_text="Descripción detallada del diagnóstico")
    tratamiento = models.TextField(help_text="Tratamiento prescrito")
    recomendaciones = models.TextField(blank=True, help_text="Recomendaciones para el paciente")
    pronostico = models.TextField(blank=True, help_text="Pronóstico del cuadro clínico")
    archivos_adjuntos = models.JSONField(blank=True, default=list, help_text="Lista de archivos adjuntos: [{'nombre': '', 'url': ''}]")
    activo = models.BooleanField(default=True)
    creado_por = models.ForeignKey(Usuario, on_delete=models.PROTECT, related_name='diagnosticos_creados')
    modificado_por = models.ForeignKey(Usuario, on_delete=models.PROTECT, null=True, blank=True, related_name='diagnosticos_modificados')
    fecha_modificacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Diagnóstico'
        verbose_name_plural = 'Diagnósticos'
        ordering = ['-fecha']
        permissions = [
            ('can_view_diagnostico', 'Puede ver diagnósticos'),
            ('can_edit_diagnostico', 'Puede editar diagnósticos'),
        ]

    def __str__(self):
        return f"Diagnóstico #{self.id} - {self.diagnostico_principal} - {self.paciente.nombre}"

    @property
    def paciente(self):
        """Propiedad para acceder al paciente desde el diagnóstico"""
        return self.expediente.paciente

    def delete(self, *args, **kwargs):
        # ⛔ BLOQUEAR eliminación física - solo soft delete
        raise PermissionError("No está permitido eliminar diagnósticos. Use el campo 'activo' para desactivar.")

    def can_be_edited_by(self, user):
        """Verifica si un usuario puede editar este diagnóstico"""
        if not hasattr(user, 'rol'):
            return False
        # Jefe médico puede editar todo
        if user.rol in ['ADMIN', 'JEFE']:
            return True
        # Médico solo puede editar sus propios diagnósticos
        if user.rol == 'MEDICO' and hasattr(user, 'perfil_medico'):
            return self.doctor.usuario == user
        return False