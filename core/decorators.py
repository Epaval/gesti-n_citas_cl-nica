# core/decorators.py
from functools import wraps
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.contrib import messages
from .models import Cita

def rol_requerido(*roles_permitidos):
    """
    Decorador para restringir vistas según el rol del usuario.
    Uso: @rol_requerido('ADMIN', 'JEFE')
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Verificar autenticación
            if not request.user.is_authenticated:
                messages.error(request, 'Debes iniciar sesión para acceder')
                return redirect('login')
            
            # Verificar que el usuario tenga rol
            if not hasattr(request.user, 'rol'):
                messages.error(request, 'Usuario sin rol definido')
                return redirect('login')
            
            # Verificar rol permitido
            if request.user.rol not in roles_permitidos:
                messages.error(request, 'No tienes permisos para acceder a esta página')
                raise PermissionDenied("No tienes permisos para acceder a esta página")
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator

# Decoradores específicos por rol
def admin_required(view_func):
    return rol_requerido('ADMIN')(view_func)

def jefe_required(view_func):
    return rol_requerido('ADMIN', 'JEFE')(view_func)

def medico_required(view_func):
    return rol_requerido('ADMIN', 'JEFE', 'MEDICO')(view_func)

def asistente_required(view_func):
    return rol_requerido('ADMIN', 'JEFE', 'MEDICO', 'ASISTENTE')(view_func)

# core/decorators.py - Agregar al final

def medico_o_jefe_required(view_func):
    """
    Decorador: Solo Médicos y Jefe Médico pueden acceder.
    Admin y Asistente son EXCLUIDOS explícitamente.
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'Debes iniciar sesión para acceder')
            return redirect('login')
        
        if request.user.rol not in ['MEDICO', 'JEFE']:
            messages.error(request, '❌ Acceso denegado: Solo personal médico autorizado puede ver expedientes')
            raise PermissionDenied("Acceso restringido a personal médico")
        
        return view_func(request, *args, **kwargs)
    return wrapper


def jefe_medico_required(view_func):
    """
    Decorador: Solo Jefe Médico puede acceder (para activar/desactivar).
    """
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'Debes iniciar sesión para acceder')
            return redirect('login')
        
        if request.user.rol != 'JEFE':
            messages.error(request, '❌ Acceso denegado: Solo el Jefe Médico puede realizar esta acción')
            raise PermissionDenied("Acceso restringido al Jefe Médico")
        
        return view_func(request, *args, **kwargs)
    return wrapper


def puede_ver_expediente_paciente(view_func):
    """
    Decorador: Verifica que el usuario pueda ver el expediente de un paciente específico.
    - Jefe Médico: puede ver todos
    - Médico: solo puede ver pacientes con citas asignadas a él
    """
    @wraps(view_func)
    def wrapper(request, paciente_id, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        
        if request.user.rol not in ['MEDICO', 'JEFE']:
            raise PermissionDenied("Acceso restringido")
        
        # Jefe médico ve todo
        if request.user.rol == 'JEFE':
            return view_func(request, paciente_id, *args, **kwargs)
        
        # Médico: verificar relación con paciente
        if request.user.rol == 'MEDICO' and hasattr(request.user, 'perfil_medico'):
            tiene_relacion = Cita.objects.filter(
                paciente_id=paciente_id,
                doctor=request.user.perfil_medico
            ).exists()
            
            if not tiene_relacion:
                messages.error(request, 'Solo puedes ver expedientes de pacientes atendidos por ti')
                raise PermissionDenied("No tienes relación con este paciente")
        
        return view_func(request, paciente_id, *args, **kwargs)
    return wrapper