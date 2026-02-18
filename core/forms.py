# core/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import date, datetime, timedelta
import re
from .models import Usuario, Paciente, Doctor, Cita, Expediente, Diagnostico


# ==================== FORMULARIO DE USUARIO ====================
class UsuarioForm(UserCreationForm):
    """Formulario para crear nuevos usuarios con rol"""
    
    class Meta:
        model = Usuario
        fields = ['username', 'email', 'rol', 'telefono', 'first_name', 'last_name', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'input-group-field', 'placeholder': 'Nombre de usuario'}),
            'email': forms.EmailInput(attrs={'class': 'input-group-field', 'placeholder': 'email@ejemplo.com'}),
            'rol': forms.Select(attrs={'class': 'input-group-field'}),
            'telefono': forms.TextInput(attrs={'class': 'input-group-field', 'placeholder': '555-0000'}),
            'first_name': forms.TextInput(attrs={'class': 'input-group-field', 'placeholder': 'Nombre'}),
            'last_name': forms.TextInput(attrs={'class': 'input-group-field', 'placeholder': 'Apellido'}),
            'password1': forms.PasswordInput(attrs={'class': 'input-group-field'}),
            'password2': forms.PasswordInput(attrs={'class': 'input-group-field'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Personalizar labels
        self.fields['username'].label = 'Nombre de Usuario'
        self.fields['email'].label = 'Correo Electrónico'
        self.fields['rol'].label = 'Rol en el Sistema'
        self.fields['telefono'].label = 'Teléfono'
        self.fields['password1'].label = 'Contraseña'
        self.fields['password2'].label = 'Confirmar Contraseña'


# ==================== FORMULARIO DE LOGIN ====================
class LoginForm(AuthenticationForm):
    """Formulario de login personalizado"""
    
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'input-group-field',
            'placeholder': 'Usuario'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'input-group-field',
            'placeholder': 'Contraseña'
        })
    )


# ==================== FORMULARIO DE PERFIL ====================
class PerfilForm(forms.ModelForm):
    """Formulario para editar perfil de usuario"""
    
    class Meta:
        model = Usuario
        fields = ['first_name', 'last_name', 'email', 'telefono', 'foto_perfil']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'input-group-field'}),
            'last_name': forms.TextInput(attrs={'class': 'input-group-field'}),
            'email': forms.EmailInput(attrs={'class': 'input-group-field'}),
            'telefono': forms.TextInput(attrs={'class': 'input-group-field'}),
            'foto_perfil': forms.ClearableFileInput(attrs={'class': 'input-group-field'}),
        }


# ==================== FORMULARIO DE PACIENTE ====================
 
class PacienteForm(forms.ModelForm):
    """Formulario para registrar/editar pacientes con datos completos"""
    
    class Meta:
        model = Paciente
        fields = [
            'ci', 'nombre', 'sexo', 'fecha_nacimiento',
            'telefono', 'telefono_alternativo', 'email', 'direccion'
        ]
        widgets = {
            'ci': forms.TextInput(attrs={
                'class': 'input-group-field',
                'placeholder': 'Ej: V-12345678 o E-87654321',
                'required': True,
                'pattern': '[VEJve]-[0-9]{7,8}',
                'title': 'Formato: V-12345678 (Venezolano) o E-87654321 (Extranjero)',
                # ✅ HACER SOLO LECTURA SI YA EXISTE
                'readonly': True,  # Se setea dinámicamente en __init__
            }),
            'nombre': forms.TextInput(attrs={
                'class': 'input-group-field',
                'placeholder': 'Nombre completo del paciente',
                'required': True
            }),
            'sexo': forms.Select(attrs={'class': 'input-group-field'}),
            'fecha_nacimiento': forms.DateInput(attrs={
                'class': 'input-group-field',
                'type': 'date',
                'required': True,
                # ✅ HACER SOLO LECTURA SI YA EXISTE
                'readonly': True,  # Se setea dinámicamente en __init__
            }),
            'telefono': forms.TextInput(attrs={
                'class': 'input-group-field',
                'placeholder': '0412-1234567',
                'required': True
            }),
            'telefono_alternativo': forms.TextInput(attrs={
                'class': 'input-group-field',
                'placeholder': 'Opcional'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'input-group-field',
                'placeholder': 'email@ejemplo.com'
            }),
            'direccion': forms.Textarea(attrs={
                'class': 'input-group-field',
                'rows': 2,
                'placeholder': 'Dirección completa (opcional)'
            }),
        }
        labels = {
            'ci': 'Cédula de Identidad *',
            'nombre': 'Nombre Completo *',
            'sexo': 'Sexo *',
            'fecha_nacimiento': 'Fecha de Nacimiento *',
            'telefono': 'Teléfono Principal *',
            'telefono_alternativo': 'Teléfono Alternativo',
            'email': 'Correo Electrónico',
            'direccion': 'Dirección',
        }
    
    def __init__(self, *args, **kwargs):
        """
        Personalizar el formulario según si es creación o edición.
        En edición, CI y fecha_nacimiento son solo lectura.
        """
        super().__init__(*args, **kwargs)
        
        # Si es edición (el objeto ya existe), hacer CI y fecha_nacimiento solo lectura
        if self.instance and self.instance.pk:
            self.fields['ci'].widget.attrs['readonly'] = True
            self.fields['ci'].widget.attrs['disabled'] = False  # disabled no envía el valor
            self.fields['fecha_nacimiento'].widget.attrs['readonly'] = True
            self.fields['fecha_nacimiento'].widget.attrs['disabled'] = False
            
            # Agregar clase visual para indicar que es solo lectura
            self.fields['ci'].widget.attrs['class'] += ' bg-gray-100'
            self.fields['fecha_nacimiento'].widget.attrs['class'] += ' bg-gray-100'
            
            # Agregar tooltip
            self.fields['ci'].help_text = "La cédula no se puede modificar"
            self.fields['fecha_nacimiento'].help_text = "La fecha de nacimiento no se puede modificar"
    
    def clean_ci(self):
        """Validar formato de cédula venezolana"""
        ci = self.cleaned_data.get('ci', '').strip().upper()
        
        if not ci:
            raise ValidationError("La cédula de identidad es obligatoria")
        
        # Validar formato: V-12345678 o E-87654321
        if not re.match(r'^[VEJ]-\d{7,8}$', ci):
            raise ValidationError(
                "Formato inválido. Use: V-12345678 (venezolano) o E-87654321 (extranjero)"
            )
        
        # Verificar unicidad (excluyendo el propio paciente si está editando)
        queryset = Paciente.objects.filter(ci=ci)
        if self.instance.pk:
            queryset = queryset.exclude(pk=self.instance.pk)
        
        if queryset.exists():
            raise ValidationError("Ya existe un paciente registrado con esta cédula")
        
        return ci
    
    def clean_fecha_nacimiento(self):
        """Validar que la fecha de nacimiento sea razonable"""
        fecha = self.cleaned_data.get('fecha_nacimiento')
        
        if fecha:
            hoy = date.today()
            edad = hoy.year - fecha.year - ((hoy.month, hoy.day) < (fecha.month, fecha.day))
            
            if edad < 0 or edad > 120:
                raise ValidationError("Fecha de nacimiento no válida")
            
            if edad < 1:
                raise ValidationError("El paciente debe tener al menos 1 año de edad")
        
        return fecha
    
    def clean_telefono(self):
        """Validar formato de teléfono venezolano - MÁS FLEXIBLE"""
        telefono = self.cleaned_data.get('telefono', '').strip()
        
        if telefono:
            # Remover caracteres no numéricos excepto + y -
            limpio = re.sub(r'[^\d+\-]', '', telefono)
            digitos = re.sub(r'[^\d]', '', limpio)
            
            # ✅ HACER MÁS FLEXIBLE: Mínimo 7 dígitos (teléfonos fijos)
            if len(digitos) < 7:
                raise ValidationError(
                    "Teléfono no válido. Mínimo 7 dígitos (ej: 555-0104 o 0412-1234567)"
                )
            
            # Máximo 11 dígitos (celulares con 04xx)
            if len(digitos) > 11:
                raise ValidationError("Teléfono no válido. Máximo 11 dígitos")
        
        return telefono




# ==================== FORMULARIO DE DOCTOR ====================

class DoctorForm(forms.ModelForm):
    """Formulario para registrar/editar doctores"""
    
    class Meta:
        model = Doctor
        fields = ['nombre', 'especialidad', 'telefono', 'costo_consulta', 'activo']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'input-group-field',
                'placeholder': 'Nombre completo del doctor',
                'required': True
            }),
            'especialidad': forms.Select(attrs={'class': 'input-group-field'}),
            'telefono': forms.TextInput(attrs={
                'class': 'input-group-field',
                'placeholder': '555-0000',
                'required': True
            }),
            'costo_consulta': forms.NumberInput(attrs={
                'class': 'input-group-field',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            }),
            'activo': forms.CheckboxInput(attrs={'class': 'switch-input'}),
        }
    
    def clean_costo_consulta(self):
        costo = self.cleaned_data.get('costo_consulta')
        if costo is not None and costo < 0:
            raise ValidationError("El costo no puede ser negativo")
        return costo
    
    def clean_telefono(self):
        telefono = self.cleaned_data.get('telefono')
        if telefono and len(telefono.replace(' ', '').replace('-', '')) < 7:
            raise ValidationError("Teléfono no válido")
        return telefono



# ==================== FORMULARIO DE CITA ====================
class CitaForm(forms.ModelForm):
    """Formulario para agendar citas médicas"""
    
    class Meta:
        model = Cita
        fields = ['paciente', 'doctor', 'fecha', 'hora', 'motivo']
        widgets = {
            'paciente': forms.Select(attrs={'class': 'input-group-field'}),
            'doctor': forms.Select(attrs={'class': 'input-group-field'}),
            'fecha': forms.DateInput(attrs={
                'class': 'input-group-field',
                'type': 'date'
            }),
            'hora': forms.TimeInput(attrs={
                'class': 'input-group-field',
                'type': 'time'
            }),
            'motivo': forms.Textarea(attrs={
                'class': 'input-group-field',
                'rows': 3,
                'placeholder': 'Describa brevemente el motivo de la consulta...'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrar solo pacientes y doctores activos
        self.fields['paciente'].queryset = Paciente.objects.filter(activo=True).order_by('nombre')
        self.fields['doctor'].queryset = Doctor.objects.filter(activo=True).order_by('nombre')
        
        # Personalizar labels
        self.fields['paciente'].label = 'Paciente'
        self.fields['doctor'].label = 'Doctor'
        self.fields['fecha'].label = 'Fecha de la Cita'
        self.fields['hora'].label = 'Hora'
        self.fields['motivo'].label = 'Motivo de la Consulta'
    
    def clean(self):
        """Validaciones personalizadas para la cita"""
        cleaned_data = super().clean()
        doctor = cleaned_data.get('doctor')
        fecha = cleaned_data.get('fecha')
        hora = cleaned_data.get('hora')
        
        if doctor and fecha and hora:
            # Verificar que la fecha no sea en el pasado
            if fecha < timezone.now().date():
                raise ValidationError("No se pueden agendar citas en fechas pasadas")
            
            # Verificar disponibilidad del doctor en ese horario
            cita_existente = Cita.objects.filter(
                doctor=doctor,
                fecha=fecha,
                hora=hora,
                estado__in=['PROGRAMADA', 'EN_ESPERA']
            ).exists()
            
            if cita_existente:
                raise ValidationError("⚠️ El doctor no está disponible en ese horario. Por favor, seleccione otra hora.")
        
        return cleaned_data
    
#========================Expedientes y Diagnostico======================== 


class ExpedienteForm(forms.ModelForm):
    """Formulario para crear/editar expediente médico"""
    
    class Meta:
        model = Expediente
        fields = [
            'observaciones_generales', 'alergias', 'medicamentos_actuales', 
            'antecedentes', 'activo'
        ]
        widgets = {
            'observaciones_generales': forms.Textarea(attrs={
                'class': 'input-group-field', 'rows': 3,
                'placeholder': 'Observaciones generales del paciente...'
            }),
            'alergias': forms.Textarea(attrs={
                'class': 'input-group-field', 'rows': 2,
                'placeholder': 'Alergias conocidas (separar con comas)...'
            }),
            'medicamentos_actuales': forms.Textarea(attrs={
                'class': 'input-group-field', 'rows': 2,
                'placeholder': 'Medicamentos actuales y dosis...'
            }),
            'antecedentes': forms.Textarea(attrs={
                'class': 'input-group-field', 'rows': 3,
                'placeholder': 'Antecedentes médicos, quirúrgicos, familiares...'
            }),
            'activo': forms.CheckboxInput(attrs={'class': 'switch-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Solo Jefe Médico puede ver/editar campo 'activo'
        if user and user.rol != 'JEFE':
            self.fields['activo'].widget = forms.HiddenInput()
            self.fields['activo'].disabled = True

#========================DIAGNOSTICO======================

class DiagnosticoForm(forms.ModelForm):
    """Formulario para crear/editar diagnóstico"""
    
    # ✅ Campo opcional para que JEFE seleccione el doctor
    doctor = forms.ModelChoiceField(
        queryset=Doctor.objects.filter(activo=True),
        required=False,  # No requerido si es médico (se asigna automático)
        widget=forms.Select(attrs={'class': 'input-group-field'}),
        label='Doctor',
        empty_label='Seleccionar doctor...'
    )
    
    class Meta:
        model = Diagnostico
        # ✅ Incluir 'doctor' en fields para que esté disponible
        fields = ['doctor', 'diagnostico_principal', 'descripcion', 'tratamiento', 'recomendaciones', 'pronostico', 'activo']
        widgets = {
            'diagnostico_principal': forms.TextInput(attrs={
                'class': 'input-group-field',
                'placeholder': 'Ej: Hipertensión arterial esencial (I10)'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'input-group-field', 'rows': 4,
                'placeholder': 'Descripción detallada del cuadro clínico...'
            }),
            'tratamiento': forms.Textarea(attrs={
                'class': 'input-group-field', 'rows': 4,
                'placeholder': 'Medicamentos, dosis, frecuencia, duración...'
            }),
            'recomendaciones': forms.Textarea(attrs={
                'class': 'input-group-field', 'rows': 3,
                'placeholder': 'Recomendaciones de estilo de vida, seguimiento...'
            }),
            'pronostico': forms.Textarea(attrs={
                'class': 'input-group-field', 'rows': 2,
                'placeholder': 'Pronóstico esperado...'
            }),
            'activo': forms.CheckboxInput(attrs={'class': 'switch-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # ✅ Si es médico, ocultar campo doctor (se asigna automático)
        if user and user.rol == 'MEDICO':
            self.fields['doctor'].widget = forms.HiddenInput()
            self.fields['doctor'].required = False
        # Si es JEFE, el campo doctor se muestra para selección
        
        # ✅ Solo JEFE puede ver/editar campo 'activo'
        if user and user.rol != 'JEFE':
            self.fields['activo'].widget = forms.HiddenInput()
            self.fields['activo'].disabled = True
    
    def clean_diagnostico_principal(self):
        diagnostico = self.cleaned_data.get('diagnostico_principal')
        if diagnostico and len(diagnostico.strip()) < 3:
            raise ValidationError("El diagnóstico principal debe tener al menos 3 caracteres")
        return diagnostico.strip()


# ===============Formulario para Staff===========================

class StaffUsuarioForm(forms.ModelForm):
    """
    Formulario para crear/editar usuario de staff (Médico o Asistente).
    Permite asignar credenciales de acceso al sistema.
    """
    username = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'input-group-field',
            'placeholder': 'nombre.apellido',
            'pattern': '[a-z][a-z0-9_.]*',
            'title': 'Solo letras minúsculas, números, puntos y guiones bajos'
        }),
        label="Nombre de Usuario *"
    )
    
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'input-group-field',
            'placeholder': 'usuario@consultorio.com'
        }),
        label="Correo Electrónico *"
    )
    
    password1 = forms.CharField(
        label="Contraseña *",
        widget=forms.PasswordInput(attrs={
            'class': 'input-group-field',
            'placeholder': 'Mínimo 8 caracteres'
        }),
        required=False  # No requerido en edición
    )
    
    password2 = forms.CharField(
        label="Confirmar Contraseña *",
        widget=forms.PasswordInput(attrs={
            'class': 'input-group-field',
            'placeholder': 'Repite la contraseña'
        }),
        required=False
    )
    
    rol = forms.ChoiceField(
        choices=Usuario.ROLES,
        widget=forms.Select(attrs={'class': 'input-group-field'}),
        label="Rol en el Sistema *"
    )
    
    # ✅ CAMPO CORREGIDO: Usar is_active en lugar de activo
    is_active = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'switch-input'}),
        label="Usuario Activo",
        initial=True,
        help_text="Desmarcar para desactivar el acceso al sistema"
    )
    
    class Meta:
        model = Usuario
        # ✅ REMOVER 'activo' y usar 'is_active' (campo nativo de Django)
        fields = ['username', 'email', 'rol', 'first_name', 'last_name', 'telefono', 'is_active']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'input-group-field', 'placeholder': 'Nombre'}),
            'last_name': forms.TextInput(attrs={'class': 'input-group-field', 'placeholder': 'Apellido'}),
            'telefono': forms.TextInput(attrs={'class': 'input-group-field', 'placeholder': '0412-1234567'}),
            # is_active ya está definido arriba como campo personalizado
        }
    
    def __init__(self, *args, **kwargs):
        self.user_request = kwargs.pop('user_request', None)
        super().__init__(*args, **kwargs)
        
        # Si es edición, ocultar campo de contraseña (se maneja separado)
        if self.instance and self.instance.pk:
            self.fields['password1'].required = False
            self.fields['password2'].required = False
            self.fields['password1'].widget.attrs['placeholder'] = 'Dejar vacío para mantener actual'
            self.fields['password2'].widget.attrs['placeholder'] = 'Dejar vacío para mantener actual'
        
        # Solo ADMIN puede asignar rol ADMIN
        if self.user_request and self.user_request.rol != 'ADMIN':
            self.fields['rol'].choices = [r for r in Usuario.ROLES if r[0] != 'ADMIN']
    
    def clean_username(self):
        """Validar que el username sea único"""
        username = self.cleaned_data.get('username', '').lower().strip()
        
        if not username:
            raise ValidationError("El nombre de usuario es obligatorio")
        
        # Verificar unicidad
        queryset = Usuario.objects.filter(username=username)
        if self.instance.pk:
            queryset = queryset.exclude(pk=self.instance.pk)
        
        if queryset.exists():
            raise ValidationError("Ya existe un usuario con este nombre de usuario")
        
        return username
    
    def clean_email(self):
        """Validar que el email sea único"""
        email = self.cleaned_data.get('email', '').lower().strip()
        
        if not email:
            raise ValidationError("El correo electrónico es obligatorio")
        
        # Verificar unicidad
        queryset = Usuario.objects.filter(email__iexact=email)
        if self.instance.pk:
            queryset = queryset.exclude(pk=self.instance.pk)
        
        if queryset.exists():
            raise ValidationError("Ya existe un usuario con este correo electrónico")
        
        return email
    
    def clean_password2(self):
        """Validar que las contraseñas coincidan"""
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        
        # Si es creación nueva, ambas son requeridas
        if not self.instance.pk:
            if not password1 or not password2:
                raise ValidationError("Ambos campos de contraseña son obligatorios para nuevos usuarios")
        
        # Si se está cambiando contraseña, validar coincidencia
        if password1 or password2:
            if password1 != password2:
                raise ValidationError("Las contraseñas no coinciden")
            
            # Validar longitud mínima
            if password1 and len(password1) < 8:
                raise ValidationError("La contraseña debe tener al menos 8 caracteres")
        
        return password2
    
    def save(self, commit=True):
        """Guardar usuario con contraseña encriptada"""
        user = super().save(commit=False)
        
        # Si es usuario nuevo o se está cambiando contraseña
        password1 = self.cleaned_data.get('password1')
        if password1:
            user.set_password(password1)
        
        if commit:
            user.save()
        
        return user

