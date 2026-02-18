# core/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Count
from django.utils import timezone
from .models import Usuario, Paciente, Doctor, Cita, Expediente, Diagnostico
from .decorators import (
    rol_requerido, admin_required, jefe_required, medico_required, asistente_required,
    medico_o_jefe_required, jefe_medico_required, puede_ver_expediente_paciente
)

from .forms import UsuarioForm, PacienteForm, DoctorForm, CitaForm, PerfilForm, ExpedienteForm, DiagnosticoForm, StaffUsuarioForm
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger


def politica_privacidad(request):
    """Vista PÚBLICA de política de privacidad  """
    return render(request, 'core/privacidad.html', {
        'titulo_pagina': 'Política de Privacidad',
        'fecha_actual': timezone.now().date()
    })

def terminos_usos(request):
    """Vista pública de terminos y usos"""
    contexto = {
        'fecha_actual': timezone.now().date(),
        'titulo_pagina': 'Términos de Uso'
    }
    return render(request, 'core/terminos.html', contexto)


# ==================== AUTENTICACIÓN ====================
def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            #messages.success(request, f'¡Bienvenido, {user.username}!')
            return redirect('dashboard')
        else:
            messages.error(request, 'Usuario o contraseña incorrectos')
    
    return render(request, 'core/login.html')

@login_required
def logout_view(request):
    logout(request)
    #messages.info(request, 'Has cerrado sesión correctamente')
    return redirect('login')

# ==================== DASHBOARD ====================

@login_required
def dashboard(request):
    contexto = {
        'total_pacientes': Paciente.objects.filter(activo=True).count(),
        'total_doctores': Doctor.objects.filter(activo=True).count(),
        'citas_hoy': Cita.objects.filter(fecha=timezone.now().date()).count(),
        'citas_programadas': Cita.objects.filter(estado='PROGRAMADA').count(),
    }
    
    # ✅ AGREGAR: Estadísticas de staff (solo para ADMIN/JEFE)
    if request.user.rol in ['ADMIN', 'JEFE']:
        contexto['total_admins'] = Usuario.objects.filter(rol='ADMIN', is_active=True).count()
        contexto['total_jefes'] = Usuario.objects.filter(rol='JEFE', is_active=True).count()
        contexto['total_medicos'] = Usuario.objects.filter(rol='MEDICO', is_active=True).count()
        contexto['total_asistentes'] = Usuario.objects.filter(rol='ASISTENTE', is_active=True).count()
    
    # Datos específicos por rol
    if request.user.rol == 'MEDICO' and hasattr(request.user, 'perfil_medico'):
        contexto['mis_citas'] = Cita.objects.filter(
            doctor=request.user.perfil_medico,
            estado='PROGRAMADA'
        )[:5]
    
    return render(request, 'core/dashboard.html', contexto)


# ==================== PACIENTES ====================
@login_required
def lista_pacientes(request):
    """Vista para listar pacientes con búsqueda y paginación"""
    buscar = request.GET.get('buscar', '')
    pacientes_list = Paciente.objects.filter(activo=True)
    
    # Aplicar búsqueda
    if buscar:
        pacientes_list = pacientes_list.filter(
            Q(nombre__icontains=buscar) |
            Q(email__icontains=buscar) |
            Q(telefono__icontains=buscar)
        )
    
    # Ordenar por nombre
    pacientes_list = pacientes_list.order_by('nombre')
    
    # Paginación: 6 pacientes por página
    paginator = Paginator(pacientes_list, 6)
    page_number = request.GET.get('page')
    
    try:
        pacientes = paginator.page(page_number)
    except PageNotAnInteger:
        pacientes = paginator.page(1)
    except EmptyPage:
        pacientes = paginator.page(paginator.num_pages)
    
    contexto = {
        'pacientes': pacientes,
        'buscar': buscar,
        'page_obj': pacientes,
        'total_pacientes': paginator.count,
        'total_paginas': paginator.num_pages,
    }
    
    return render(request, 'core/pacientes/lista.html', contexto)

# ==================== EDITAR PACIENTE ====================

@login_required
@rol_requerido('ADMIN', 'JEFE', 'ASISTENTE')
def editar_paciente(request, id):
    """Vista para editar información de paciente"""
    paciente = get_object_or_404(Paciente, id=id)
    
    if request.method == 'POST':
        form = PacienteForm(request.POST, instance=paciente)
        if form.is_valid():
            try:
                form.save()
                messages.success(request, f'Paciente {paciente.nombre} actualizado exitosamente')
                return redirect('detalle_paciente', id=paciente.id)
            except Exception as e:
                messages.error(request, f'Error al actualizar: {str(e)}')
        else:
            # Mostrar errores específicos del formulario
            errores = []
            for field, errors in form.errors.items():
                for error in errors:
                    errores.append(f"{form.fields[field].label}: {error}")
            
            messages.error(request, 'Error al actualizar. Verifica los datos:\n' + '\n'.join(errores))
    else:
        form = PacienteForm(instance=paciente)
    
    return render(request, 'core/pacientes/form.html', {
        'form': form,
        'titulo': f'Editar: {paciente.nombre}',
        'accion': 'editar',
        'paciente': paciente
    })

# ==================== CREAR PACIENTE ====================

@login_required
@rol_requerido('ADMIN', 'JEFE', 'ASISTENTE')
def crear_paciente(request):
    if request.method == 'POST':
        form = PacienteForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Paciente registrado exitosamente')
            return redirect('lista_pacientes')
    else:
        form = PacienteForm()
    
    return render(request, 'core/pacientes/form.html', {'form': form, 'titulo': 'Nuevo Paciente'})

# ==================== DETALLE PACIENTE ====================

@login_required
def detalle_paciente(request, id):
    """Vista para mostrar detalle completo de un paciente"""
    paciente = get_object_or_404(Paciente, id=id)
    
    # Obtener citas del paciente
    citas = paciente.citas.select_related('doctor').order_by('-fecha', '-hora')[:20]
    
    # Estadísticas
    stats = {
        'total_citas': paciente.citas.count(),
        'programadas': paciente.citas.filter(estado='PROGRAMADA').count(),
        'completadas': paciente.citas.filter(estado='COMPLETADA').count(),
        'canceladas': paciente.citas.filter(estado='CANCELADA').count(),
    }
    
    contexto = {
        'paciente': paciente,
        'citas': citas,
        'stats': stats,
        'can_edit': request.user.rol in ['ADMIN', 'JEFE', 'ASISTENTE'],
        'can_view_expediente': request.user.rol in ['MEDICO', 'JEFE'],
    }
    
    return render(request, 'core/pacientes/detalle.html', contexto)

# ==================== BUSCAR PACIENTE DINAMICAMENTE ====================
@login_required
def api_buscar_pacientes(request):
    """API endpoint para búsqueda dinámica de pacientes"""
    buscar = request.GET.get('q', '')
    
    pacientes_list = Paciente.objects.filter(activo=True)
    
    if buscar:
        pacientes_list = pacientes_list.filter(
            Q(nombre__icontains=buscar) |
            Q(ci__icontains=buscar) |
            Q(telefono__icontains=buscar) |
            Q(email__icontains=buscar)
        )
    
    pacientes_list = pacientes_list.order_by('nombre')[:50]
    
    pacientes_data = []
    for paciente in pacientes_list:
        # Calcular edad si tienes fecha_nacimiento
        edad = None
        if hasattr(paciente, 'fecha_nacimiento') and paciente.fecha_nacimiento:
            from datetime import date
            hoy = date.today()
            edad = hoy.year - paciente.fecha_nacimiento.year - ((hoy.month, hoy.day) < (paciente.fecha_nacimiento.month, paciente.fecha_nacimiento.day))
        
        pacientes_data.append({
            'id': paciente.id,
            'nombre': paciente.nombre,
            'ci': paciente.ci,
            'telefono': paciente.telefono,
            'email': paciente.email,
            'edad': edad,
            'sexo': paciente.get_sexo_display() if hasattr(paciente, 'get_sexo_display') else None,
            'activo': paciente.activo,
            'inicial': paciente.nombre.split()[0][:1].upper() if paciente.nombre else '?',
            'url_detalle': f"/pacientes/{paciente.id}/",
        })
    
    return JsonResponse({
        'success': True,
        'total': len(pacientes_data),
        'results': pacientes_data,  # Usamos 'results' para consistencia
        'buscar': buscar,
    })

# ==================== LISTA DE DOCTORES ====================
@login_required
@jefe_required
def lista_doctores(request):
    """Vista para listar doctores con búsqueda dinámica y paginación"""
    buscar = request.GET.get('buscar', '')
    especialidad = request.GET.get('especialidad', '')
    
    doctores_list = Doctor.objects.filter(activo=True).annotate(
        citas_programadas=Count('citas', filter=Q(citas__estado='PROGRAMADA')),
        total_citas=Count('citas')
    )
    
    # Aplicar filtros
    if buscar:
        doctores_list = doctores_list.filter(
            Q(nombre__icontains=buscar) |
            Q(telefono__icontains=buscar) |
            Q(especialidad__icontains=buscar)
        )
    
    if especialidad:
        doctores_list = doctores_list.filter(especialidad=especialidad)
    
    doctores_list = doctores_list.order_by('nombre')
    
    # Paginación: 6 doctores por página
    paginator = Paginator(doctores_list, 6)
    page_number = request.GET.get('page')
    
    try:
        doctores = paginator.page(page_number)
    except PageNotAnInteger:
        doctores = paginator.page(1)
    except EmptyPage:
        doctores = paginator.page(paginator.num_pages)
    
    contexto = {
        'doctores': doctores,
        'buscar': buscar,
        'especialidad': especialidad,
        'page_obj': doctores,
        'total_doctores': paginator.count,
        'total_paginas': paginator.num_pages,
        'especialidades': Doctor.ESPECIALIDADES,
    }
    
    return render(request, 'core/doctores/lista.html', contexto)

# ==================== API BÚSQUEDA DINÁMICA DOCTORES ====================
@login_required
def api_buscar_doctores(request):
    """API endpoint para búsqueda dinámica de doctores"""
    buscar = request.GET.get('q', '')
    especialidad = request.GET.get('especialidad', '')
    
    doctores_list = Doctor.objects.filter(activo=True)
    
    if buscar:
        doctores_list = doctores_list.filter(
            Q(nombre__icontains=buscar) |
            Q(telefono__icontains=buscar) |
            Q(especialidad__icontains=buscar)
        )
    
    if especialidad:
        doctores_list = doctores_list.filter(especialidad=especialidad)
    
    doctores_list = doctores_list.order_by('nombre')[:50]
    
    doctores_data = []
    for doctor in doctores_list:
        doctores_data.append({
            'id': doctor.id,
            'nombre': doctor.nombre,
            'especialidad': doctor.get_especialidad_display(),
            'especialidad_code': doctor.especialidad,
            'telefono': doctor.telefono,
            'costo_consulta': float(doctor.costo_consulta),
            'activo': doctor.activo,
            'inicial': doctor.nombre.split()[0][:1].upper() if doctor.nombre else '?',
            'url_detalle': f"/doctores/{doctor.id}/",
            'url_editar': f"/doctores/{doctor.id}/editar/",
            'total_citas': doctor.citas.count(),
        })
    
    return JsonResponse({
        'success': True,
        'total': len(doctores_data),
        'doctores': doctores_data,
        'buscar': buscar,
    })

# ==================== DETALLE DE DOCTOR ====================
@login_required
def detalle_doctor(request, id):
    """Vista para mostrar detalle completo de un doctor"""
    doctor = get_object_or_404(Doctor, id=id)
    
    # Obtener citas programadas y completadas
    citas_programadas = doctor.citas.filter(estado='PROGRAMADA').order_by('fecha', 'hora')[:10]
    citas_completadas = doctor.citas.filter(estado='COMPLETADA').order_by('-fecha')[:10]
    
    # Estadísticas
    stats = {
        'total_citas': doctor.citas.count(),
        'programadas': doctor.citas.filter(estado='PROGRAMADA').count(),
        'completadas': doctor.citas.filter(estado='COMPLETADA').count(),
        'canceladas': doctor.citas.filter(estado='CANCELADA').count(),
    }
    
    contexto = {
        'doctor': doctor,
        'citas_programadas': citas_programadas,
        'citas_completadas': citas_completadas,
        'stats': stats,
    }
    
    return render(request, 'core/doctores/detalle.html', contexto)

# ==================== CREAR DOCTOR ====================
@login_required
@jefe_required
def crear_doctor(request):
    """Vista para registrar nuevo doctor"""
    if request.method == 'POST':
        form = DoctorForm(request.POST)
        if form.is_valid():
            doctor = form.save()
            messages.success(request, f'Dr(a). {doctor.nombre} registrado exitosamente')
            return redirect('lista_doctores')
    else:
        form = DoctorForm()
    
    return render(request, 'core/doctores/form.html', {
        'form': form, 
        'titulo': 'Registrar Nuevo Doctor',
        'accion': 'crear'
    })

# ==================== EDITAR DOCTOR ====================
@login_required
@jefe_required
def editar_doctor(request, id):
    """Vista para editar información de doctor"""
    doctor = get_object_or_404(Doctor, id=id)
    
    if request.method == 'POST':
        form = DoctorForm(request.POST, instance=doctor)
        if form.is_valid():
            form.save()
            messages.success(request, f'Dr(a). {doctor.nombre} actualizado exitosamente')
            return redirect('detalle_doctor', id=doctor.id)
    else:
        form = DoctorForm(instance=doctor)
    
    return render(request, 'core/doctores/form.html', {
        'form': form, 
        'titulo': f'Editar: {doctor.nombre}',
        'accion': 'editar',
        'doctor': doctor
    })

# ==================== ACTIVAR/DESACTIVAR DOCTOR ====================
@login_required
@jefe_required
def activar_doctor(request, id):
    """Vista para activar o desactivar doctor (soft delete)"""
    doctor = get_object_or_404(Doctor, id=id)
    doctor.activo = not doctor.activo
    doctor.save()
    
    estado = 'activado' if doctor.activo else 'desactivado'
    messages.info(request, f'Dr(a). {doctor.nombre} ha sido {estado}')
    
    return redirect('detalle_doctor', id=doctor.id)


# ==================== CITAS ====================
@login_required
def lista_citas(request):
    filtro = request.GET.get('filtro', 'todas')
    citas = Cita.objects.select_related('paciente', 'doctor').all()
    
    if filtro == 'programadas':
        citas = citas.filter(estado='PROGRAMADA')
    elif filtro == 'completadas':
        citas = citas.filter(estado='COMPLETADA')
    elif filtro == 'canceladas':
        citas = citas.filter(estado='CANCELADA')
    elif filtro == 'hoy':
        citas = citas.filter(fecha=timezone.now().date())
    
    # Médicos solo ven sus citas
    if request.user.rol == 'MEDICO' and hasattr(request.user, 'perfil_medico'):
        citas = citas.filter(doctor=request.user.perfil_medico)
    
    return render(request, 'core/citas/lista.html', {'citas': citas, 'filtro': filtro})

@login_required
@rol_requerido('ADMIN', 'JEFE', 'ASISTENTE')
def crear_cita(request):
    if request.method == 'POST':
        form = CitaForm(request.POST)
        form.fields['doctor'].queryset = Doctor.objects.filter(activo=True)
        form.fields['paciente'].queryset = Paciente.objects.filter(activo=True)
        
        if form.is_valid():
            cita = form.save(commit=False)
            cita.creado_por = request.user
            cita.save()
            messages.success(request, 'Cita agendada exitosamente')
            return redirect('lista_citas')
    else:
        form = CitaForm()
        form.fields['doctor'].queryset = Doctor.objects.filter(activo=True)
        form.fields['paciente'].queryset = Paciente.objects.filter(activo=True)
    
    return render(request, 'core/citas/form.html', {'form': form, 'titulo': 'Nueva Cita'})

@login_required
def detalle_cita(request, id):
    cita = get_object_or_404(Cita, id=id)
    return render(request, 'core/citas/detalle.html', {'cita': cita})

@login_required
@rol_requerido('ADMIN', 'JEFE', 'ASISTENTE')
def cancelar_cita(request, id):
    cita = get_object_or_404(Cita, id=id)
    cita.estado = 'CANCELADA'
    cita.save()
    messages.warning(request, 'Cita cancelada exitosamente')
    return redirect('lista_citas')

@login_required
@medico_required
def completar_cita(request, id):
    cita = get_object_or_404(Cita, id=id)
    
    # Solo el médico asignado puede completar
    if request.user.rol == 'MEDICO' and hasattr(request.user, 'perfil_medico'):
        if cita.doctor != request.user.perfil_medico:
            messages.error(request, 'No puedes completar esta cita')
            return redirect('lista_citas')
    
    if request.method == 'POST':
        diagnostico = request.POST.get('diagnostico')
        cita.estado = 'COMPLETADA'
        cita.diagnostico = diagnostico
        cita.save()
        messages.success(request, 'Cita completada exitosamente')
        return redirect('lista_citas')
    
    return render(request, 'core/citas/completar.html', {'cita': cita})

# ==================== PERFIL ====================
@login_required
def perfil(request):
    return render(request, 'core/perfil.html', {'usuario': request.user})

@login_required
def editar_perfil(request):
    if request.method == 'POST':
        form = PerfilForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Perfil actualizado exitosamente')
            return redirect('perfil')
    else:
        form = PerfilForm(instance=request.user)
    
    return render(request, 'core/perfil_editar.html', {'form': form})


@login_required
def api_buscar_pacientes(request):
    """API endpoint para búsqueda dinámica de pacientes"""
    buscar = request.GET.get('q', '')
    
    pacientes_list = Paciente.objects.filter(activo=True)
    
    if buscar:
        pacientes_list = pacientes_list.filter(
            Q(nombre__icontains=buscar) |
            Q(ci__icontains=buscar) |
            Q(email__icontains=buscar) |
            Q(telefono__icontains=buscar)
        ).order_by('nombre')[:50]
    else:
        pacientes_list = pacientes_list.order_by('nombre')[:50]
    
    pacientes_data = []
    for paciente in pacientes_list:
        pacientes_data.append({
            'id': paciente.id,
            'ci': paciente.ci,
            'nombre': paciente.nombre,
            'sexo': paciente.get_sexo_display(),
            'fecha_nacimiento': paciente.fecha_nacimiento.strftime('%d/%m/%Y') if paciente.fecha_nacimiento else None,
            'edad': paciente.edad,  # ← Ahora es propiedad calculada
            'telefono': paciente.telefono,
            'email': paciente.email,
            'fecha_registro': paciente.fecha_registro.strftime('%d/%m/%Y'),
            'inicial': paciente.nombre[:1].upper(),
            'url_detalle': f"/pacientes/{paciente.id}/",
            'url_editar': f"/pacientes/{paciente.id}/editar/",
        })
    
    return JsonResponse({
        'success': True,
        'total': len(pacientes_data),
        'pacientes': pacientes_data,
        'buscar': buscar,
    })
 

# ==================== EXPEDIENTE MÉDICO ====================

@login_required 
@medico_o_jefe_required
def ver_expediente(request, paciente_id):
    """Vista para ver expediente médico de un paciente"""
    paciente = get_object_or_404(Paciente, id=paciente_id, activo=True)
    
    # Obtener o crear expediente
    expediente, created = Expediente.objects.get_or_create(
        paciente=paciente,
        defaults={'creado_por': request.user, 'activo': True}
    )
    
    # Obtener diagnósticos activos
    diagnosticos_qs = expediente.diagnosticos.filter(
        activo=True
    ).select_related('doctor', 'creado_por', 'modificado_por').order_by('-fecha')
    
    # ✅ PRE-CALCULAR: ¿Puede el usuario editar cada diagnóstico?
    diagnosticos = []
    for diag in diagnosticos_qs:
        diagnosticos.append({
            'obj': diag,
            'can_edit': (
                request.user.rol in ['ADMIN', 'JEFE'] or  # Admin/Jefe editan todo
                (request.user.rol == 'MEDICO' and 
                 hasattr(request.user, 'perfil_medico') and 
                 diag.doctor.usuario == request.user)  # Médico solo edita los suyos
            ),
            'can_activate': (
                request.user.rol == 'JEFE' or  # Jefe activa/desactiva todo
                diag.creado_por == request.user  # Creador puede activar/desactivar el suyo
            )
        })
    
    contexto = {
        'paciente': paciente,
        'expediente': expediente,
        'diagnosticos': diagnosticos,  # ← Ahora es una lista de dicts
        'can_edit_expediente': request.user.rol in ['MEDICO', 'JEFE'],
        'can_activate_expediente': request.user.rol == 'JEFE',
    }
    
    return render(request, 'core/expediente/ver.html', contexto)


@login_required
@medico_o_jefe_required
def actualizar_expediente(request, paciente_id):
    """Vista para actualizar información del expediente"""
    paciente = get_object_or_404(Paciente, id=paciente_id, activo=True)
    expediente = get_object_or_404(Expediente, paciente=paciente)
    
    if request.method == 'POST':
        form = ExpedienteForm(request.POST, instance=expediente, user=request.user)
        if form.is_valid():
            expediente = form.save(commit=False)
            expediente.modificado_por = request.user
            expediente.save()
            messages.success(request, 'Expediente actualizado exitosamente')
            return redirect('ver_expediente', paciente_id=paciente.id)
    else:
        form = ExpedienteForm(instance=expediente, user=request.user)
    
    return render(request, 'core/expediente/form_expediente.html', {
        'form': form,
        'paciente': paciente,
        'titulo': 'Actualizar Expediente'
    })


@login_required
@jefe_medico_required
def activar_expediente(request, paciente_id):
    """Vista para activar/desactivar expediente (SOLO JEFE MÉDICO)"""
    paciente = get_object_or_404(Paciente, id=paciente_id)
    expediente = get_object_or_404(Expediente, paciente=paciente)
    
    expediente.activo = not expediente.activo
    expediente.modificado_por = request.user
    expediente.save()
    
    estado = 'activado' if expediente.activo else 'desactivado'
    messages.info(request, f'Expediente de {paciente.nombre} ha sido {estado}')
    
    return redirect('ver_expediente', paciente_id=paciente.id)


# ==================== CREAR DIAGNÓSTICO ====================

@login_required
@medico_o_jefe_required
def crear_diagnostico(request, paciente_id):
    """Vista para crear nuevo diagnóstico"""
    paciente = get_object_or_404(Paciente, id=paciente_id, activo=True)
    expediente = get_object_or_404(Expediente, paciente=paciente)
    
    # ✅ Obtener doctor del usuario si es médico
    doctor = None
    if request.user.rol == 'MEDICO' and hasattr(request.user, 'perfil_medico'):
        doctor = request.user.perfil_medico
    # Si es JEFE, podrá seleccionar el doctor (opcional, ver paso 2)
    
    if request.method == 'POST':
        form = DiagnosticoForm(request.POST, user=request.user)
        if form.is_valid():
            # ✅ Guardar sin commit para asignar doctor y otros campos
            diagnostico = form.save(commit=False)
            diagnostico.expediente = expediente
            
            # ✅ Asignar doctor: del usuario o del POST si es JEFE
            if doctor:
                diagnostico.doctor = doctor
            else:
                # Si es JEFE, debe seleccionar el doctor en el formulario
                doctor_id = request.POST.get('doctor')
                if doctor_id:
                    diagnostico.doctor = get_object_or_404(Doctor, id=doctor_id)
                else:
                    messages.error(request, 'Debes seleccionar un doctor')
                    return render(request, 'core/expediente/form_diagnostico.html', {
                        'form': form, 'paciente': paciente, 'titulo': 'Nuevo Diagnóstico'
                    })
            
            diagnostico.creado_por = request.user
            diagnostico.save()
            
            messages.success(request, 'Diagnóstico registrado exitosamente')
            return redirect('ver_expediente', paciente_id=paciente.id)
        else:
            # Mostrar errores del formulario
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = DiagnosticoForm(user=request.user)
    
    return render(request, 'core/expediente/form_diagnostico.html', {
        'form': form,
        'paciente': paciente,
        'titulo': 'Nuevo Diagnóstico',
        'doctor_actual': doctor,  # Para mostrar en template si es médico
        'doctores': Doctor.objects.filter(activo=True).order_by('nombre') if request.user.rol == 'JEFE' else None,
    })


# ==================== EDITAR DIAGNÓSTICO ====================

@login_required
@medico_o_jefe_required
def editar_diagnostico(request, diagnostico_id):
    """Vista para editar diagnóstico (solo creador o JEFE)"""
    diagnostico = get_object_or_404(Diagnostico, id=diagnostico_id)
    
    # Verificar permisos de edición
    if not diagnostico.can_be_edited_by(request.user):
        messages.error(request, 'No tienes permisos para editar este diagnóstico')
        return redirect('ver_expediente', paciente_id=diagnostico.paciente.id)
    
    if request.method == 'POST':
        form = DiagnosticoForm(request.POST, instance=diagnostico, user=request.user)
        if form.is_valid():
            diagnostico = form.save(commit=False)
            diagnostico.modificado_por = request.user
            diagnostico.save()
            messages.success(request, 'Diagnóstico actualizado exitosamente')
            return redirect('ver_expediente', paciente_id=diagnostico.paciente.id)
    else:
        form = DiagnosticoForm(instance=diagnostico, user=request.user)
    
    return render(request, 'core/expediente/form_diagnostico.html', {
        'form': form,
        'paciente': diagnostico.paciente,
        'titulo': f'Editar Diagnóstico: {diagnostico.diagnostico_principal[:50]}',
        'diagnostico': diagnostico
    })

# ==================== ACTIVAR DIAGNÓSTICO ====================
@login_required
@medico_o_jefe_required
def activar_diagnostico(request, diagnostico_id):
    """Vista para activar/desactivar diagnóstico"""
    diagnostico = get_object_or_404(Diagnostico, id=diagnostico_id)
    
    # Solo JEFE o el médico creador pueden cambiar estado
    if request.user.rol != 'JEFE' and diagnostico.creado_por != request.user:
        messages.error(request, 'No tienes permisos para modificar este diagnóstico')
        return redirect('ver_expediente', paciente_id=diagnostico.paciente.id)
    
    diagnostico.activo = not diagnostico.activo
    diagnostico.modificado_por = request.user
    diagnostico.save()
    
    estado = 'activado' if diagnostico.activo else 'desactivado'
    messages.info(request, f'Diagnóstico ha sido {estado}')
    
    return redirect('ver_expediente', paciente_id=diagnostico.paciente.id)

 

# ==================== GESTIÓN DE STAFF ====================

@login_required
@jefe_required
def lista_staff(request):
    """Vista para listar todo el personal con usuarios del sistema"""
    rol_filtro = request.GET.get('rol', '')
    estado_filtro = request.GET.get('estado', '')
    buscar = request.GET.get('buscar', '')
    
    usuarios = Usuario.objects.all()
    
    # Filtrar por rol
    if rol_filtro:
        usuarios = usuarios.filter(rol=rol_filtro)
    
    # Filtrar por estado
    if estado_filtro:
        usuarios = usuarios.filter(activo=(estado_filtro == 'activo'))
    
    # Buscar por nombre o email
    if buscar:
        usuarios = usuarios.filter(
            Q(username__icontains=buscar) |
            Q(email__icontains=buscar) |
            Q(first_name__icontains=buscar) |
            Q(last_name__icontains=buscar)
        )
    
    # Ordenar por rol y nombre
    usuarios = usuarios.order_by('rol', 'username')
    
    # Paginación
    paginator = Paginator(usuarios, 10)
    page_number = request.GET.get('page')
    
    try:
        usuarios_page = paginator.page(page_number)
    except PageNotAnInteger:
        usuarios_page = paginator.page(1)
    except EmptyPage:
        usuarios_page = paginator.page(paginator.num_pages)
    
    contexto = {
        'usuarios': usuarios_page,
        'rol_filtro': rol_filtro,
        'estado_filtro': estado_filtro,
        'buscar': buscar,
        'roles': Usuario.ROLES,
        'page_obj': usuarios_page,
        'total_usuarios': paginator.count,
    }
    
    return render(request, 'core/staff/lista.html', contexto)


@login_required
@jefe_required
def crear_staff_usuario(request):
    """Vista para crear usuario de staff (Médico, Asistente o Admin)"""
    if request.method == 'POST':
        form = StaffUsuarioForm(request.POST, user_request=request.user)
        if form.is_valid():
            usuario = form.save()
            messages.success(
                request, 
                f'Usuario {usuario.username} creado exitosamente con rol {usuario.get_rol_display()}'
            )
            return redirect('lista_staff')
        else:
            # Mostrar errores del formulario
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = StaffUsuarioForm(user_request=request.user)
    
    return render(request, 'core/staff/form_usuario.html', {
        'form': form,
        'titulo': 'Crear Usuario de Staff',
        'accion': 'crear'
    })


@login_required
@jefe_required
def editar_staff_usuario(request, usuario_id):
    """Vista para editar usuario de staff"""
    usuario = get_object_or_404(Usuario, id=usuario_id)
    
    # No permitir editar el propio usuario desde esta vista
    if usuario == request.user:
        messages.warning(request, 'Para editar tu propio usuario, ve a tu perfil')
        return redirect('perfil')
    
    if request.method == 'POST':
        form = StaffUsuarioForm(request.POST, instance=usuario, user_request=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, f'Usuario {usuario.username} actualizado exitosamente')
            return redirect('lista_staff')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = StaffUsuarioForm(instance=usuario, user_request=request.user)
    
    return render(request, 'core/staff/form_usuario.html', {
        'form': form,
        'titulo': f'Editar Usuario: {usuario.username}',
        'accion': 'editar',
        'usuario_editando': usuario
    })


@login_required
@jefe_required
def activar_staff_usuario(request, usuario_id):
    """Vista para activar/desactivar usuario de staff"""
    usuario = get_object_or_404(Usuario, id=usuario_id)
    
    # No permitir desactivar el propio usuario
    if usuario == request.user:
        messages.error(request, 'No puedes desactivar tu propio usuario')
        return redirect('lista_staff')
    
    usuario.is_active = not usuario.is_active
    usuario.save()
    
    estado = 'activado' if usuario.is_active else 'desactivado'
    messages.info(request, f'Usuario {usuario.username} ha sido {estado}')
    
    return redirect('lista_staff')


@login_required
@jefe_required
def vincular_doctor_usuario(request, doctor_id):
    """Vista para vincular un doctor con un usuario del sistema"""
    doctor = get_object_or_404(Doctor, id=doctor_id)
    
    # Si ya tiene usuario, redirigir a editar
    if doctor.usuario:
        messages.info(request, 'Este doctor ya tiene un usuario asignado')
        return redirect('editar_staff_usuario', usuario_id=doctor.usuario.id)
    
    if request.method == 'POST':
        form = StaffUsuarioForm(request.POST, user_request=request.user)
        if form.is_valid():
            usuario = form.save(commit=False)
            usuario.rol = 'MEDICO'  # Forzar rol médico
            usuario.save()
            
            # Vincular doctor con usuario
            doctor.usuario = usuario
            doctor.save()
            
            messages.success(request, f'Usuario {usuario.username} vinculado al Dr(a). {doctor.nombre}')
            return redirect('detalle_doctor', id=doctor.id)
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = StaffUsuarioForm(initial={
            'first_name': doctor.nombre.split()[0] if doctor.nombre else '',
            'last_name': ' '.join(doctor.nombre.split()[1:]) if doctor.nombre else '',
            'rol': 'MEDICO',
        }, user_request=request.user)
    
    return render(request, 'core/staff/vincular_doctor.html', {
        'form': form,
        'doctor': doctor,
        'titulo': f'Vincular Usuario - {doctor.nombre}'
    })


 

# ==================== CALENDARIO DE CITAS ====================

@login_required
def calendario_citas(request):
    """Vista principal del calendario de citas"""
    
    # Obtener doctores para el filtro (solo los activos)
    doctores = Doctor.objects.filter(activo=True).order_by('nombre')
    
    # Determinar qué doctores puede ver el usuario
    if request.user.rol == 'MEDICO' and hasattr(request.user, 'perfil_medico'):
        doctores = Doctor.objects.filter(id=request.user.perfil_medico.id)
        doctor_seleccionado = request.user.perfil_medico
    else:
        doctor_seleccionado = None
    
    contexto = {
        'doctores': doctores,
        'doctor_seleccionado': doctor_seleccionado,
        'puede_ver_todos': request.user.rol in ['ADMIN', 'JEFE'],
        'estados_cita': Cita.ESTADOS,
    }
    
    return render(request, 'core/calendario/calendario.html', contexto)


@login_required
def api_calendario_citas(request):
    """API endpoint para proporcionar datos de citas al calendario"""
    
    # Obtener parámetros de filtro
    doctor_id = request.GET.get('doctor_id')
    fecha_inicio = request.GET.get('start')  # Formato: YYYY-MM-DD
    fecha_fin = request.GET.get('end')  # Formato: YYYY-MM-DD
    estado = request.GET.get('estado')
    
    # Filtrar citas
    citas = Cita.objects.select_related('paciente', 'doctor').all()
    
    # Filtrar por doctor
    if doctor_id:
        citas = citas.filter(doctor_id=doctor_id)
    elif request.user.rol == 'MEDICO' and hasattr(request.user, 'perfil_medico'):
        citas = citas.filter(doctor=request.user.perfil_medico)
    
    # Filtrar por rango de fechas
    if fecha_inicio and fecha_fin:
        citas = citas.filter(fecha__gte=fecha_inicio, fecha__lte=fecha_fin)
    
    # Filtrar por estado
    if estado and estado != 'todas':
        citas = citas.filter(estado=estado)
    
    # Construir eventos para FullCalendar
    eventos = []
    for cita in citas:
        # Determinar color según estado
        colores = {
            'PROGRAMADA': '#3498db',      # Azul
            'EN_ESPERA': '#f39c12',        # Naranja
            'COMPLETADA': '#27ae60',       # Verde
            'CANCELADA': '#e74c3c',        # Rojo
        }
        color = colores.get(cita.estado, '#95a5a6')
        
        # Crear evento
        evento = {
            'id': cita.id,
            'title': f"{cita.paciente.nombre}\n{cita.doctor.nombre}",
            'start': f"{cita.fecha}T{cita.hora}",
            'end': f"{cita.fecha}T{(cita.hora.hour + 1):02d}:{cita.hora.minute:02d}",
            'backgroundColor': color,
            'borderColor': color,
            'textColor': '#fff',
            'extendedProps': {
                'paciente': {
                    'id': cita.paciente.id,
                    'nombre': cita.paciente.nombre,
                    'telefono': cita.paciente.telefono,
                    'email': cita.paciente.email,
                },
                'doctor': {
                    'id': cita.doctor.id,
                    'nombre': cita.doctor.nombre,
                    'especialidad': cita.doctor.get_especialidad_display(),
                },
                'motivo': cita.motivo,
                'estado': cita.get_estado_display(),
                'estado_code': cita.estado,
                'diagnostico': cita.diagnostico,
                'url_detalle': f"/citas/{cita.id}/",
            }
        }
        eventos.append(evento)
    
    return JsonResponse({'events': eventos})


@login_required
def api_verificar_disponibilidad(request):
    """API para verificar disponibilidad de horario para un doctor"""
    
    doctor_id = request.GET.get('doctor_id')
    fecha = request.GET.get('fecha')  # YYYY-MM-DD
    hora = request.GET.get('hora')    # HH:MM
    
    if not all([doctor_id, fecha, hora]):
        return JsonResponse({'error': 'Faltan parámetros'}, status=400)
    
    # Verificar si ya existe una cita programada en ese horario
    cita_existente = Cita.objects.filter(
        doctor_id=doctor_id,
        fecha=fecha,
        hora=hora,
        estado__in=['PROGRAMADA', 'EN_ESPERA']
    ).exists()
    
    return JsonResponse({
        'disponible': not cita_existente,
        'mensaje': 'Horario disponible' if not cita_existente else 'Horario ya ocupado'
    })


# ==================== DOCUMENTOS MÉDICOS PARA IMPRESIÓN ====================

@login_required
@medico_o_jefe_required
def formulario_examenes(request, paciente_id):
    """Vista para seleccionar exámenes de laboratorio (no se guardan en BD)"""
    paciente = get_object_or_404(Paciente, id=paciente_id, activo=True)
    
    # Lista completa de exámenes de laboratorio organizados por categoría
    examenes_laboratorio = {
        'Hematología': [
            'Hemograma completo', 'Recuento de plaquetas', 'Tiempo de protrombina (TP)',
            'Tiempo de tromboplastina parcial (TTP)', 'Fibrinógeno', 'Dímero D',
            'Velocidad de sedimentación globular (VSG)', 'Grupo sanguíneo y factor Rh',
            'Prueba de Coombs directa', 'Prueba de Coombs indirecta',
        ],
        'Química Sanguínea': [
            'Glucosa en ayunas', 'Glucosa postprandial', 'Hemoglobina glicosilada (HbA1c)',
            'Perfil lipídico (colesterol total, HDL, LDL, triglicéridos)',
            'Urea', 'Creatinina', 'Ácido úrico', 'Electrolitos (Na, K, Cl)',
            'Calcio', 'Fósforo', 'Magnesio', 'Proteínas totales y albúmina',
            'Bilirrubina total y directa', 'Transaminasas (ALT/AST)',
            'Fosfatasa alcalina', 'GGT', 'Amilasa', 'Lipasa',
        ],
        'Marcadores Cardíacos': [
            'Troponina I/T', 'CK-MB', 'Mioglobina', 'BNP/NT-proBNP',
        ],
        'Marcadores Tumorales': [
            'PSA total y libre', 'CEA', 'CA 125', 'CA 15-3', 'CA 19-9',
            'AFP', 'Beta-HCG', 'NSE',
        ],
        'Hormonas': [
            'TSH', 'T4 libre', 'T3 libre', 'Anticuerpos anti-TPO', 'Anticuerpos anti-tiroglobulina',
            'Cortisol basal', 'Cortisol post-estimulación', 'ACTH',
            'Prolactina', 'FSH', 'LH', 'Estradiol', 'Progesterona', 'Testosterona total y libre',
            'DHEA-S', '17-OH progesterona',
        ],
        'Inmunología/Serología': [
            'Proteína C reactiva (PCR)', 'Procalcitonina', 'Factor reumatoide',
            'Anticuerpos antinucleares (ANA)', 'Anti-DNA', 'Anti-CCP',
            'Complemento C3/C4', 'Inmunoglobulinas (IgG, IgA, IgM)',
            'VDRL/RPR', 'FTA-ABS', 'VIH 1/2 (ELISA/Western Blot)',
            'Hepatitis A (IgM/IgG)', 'Hepatitis B (HBsAg, Anti-HBs, Anti-HBc)',
            'Hepatitis C (Anti-VHC)', 'Toxoplasma IgM/IgG', 'Rubéola IgM/IgG',
            'Citomegalovirus IgM/IgG', 'EBV (VCA IgM/IgG)', 'Parvovirus B19 IgM/IgG',
        ],
        'Microbiología': [
            'Urocultivo con antibiograma', 'Coprocultivo', 'Hemocultivo',
            'Cultivo de secreciones', 'Cultivo de herida', 'BK (baciloscopia)',
            'Cultivo de BK', 'Prueba de tuberculosis (PPD/IGRA)',
        ],
        'Orina/Heces': [
            'Examen general de orina (EGO)', 'Microalbuminuria', 'Proteinuria de 24h',
            'Coproscópico/Parasitológico seriado', 'Sangre oculta en heces',
            'Calprotectina fecal', 'Elastasa fecal',
        ],
        'Otros/Personalizados': [
            # Se ingresan manualmente en el textarea
        ],
    }
    
    # Obtener doctores para asignar quién solicita (si es JEFE)
    doctores = Doctor.objects.filter(activo=True).order_by('nombre')
    doctor_solicitante = None
    
    if request.user.rol == 'MEDICO' and hasattr(request.user, 'perfil_medico'):
        doctor_solicitante = request.user.perfil_medico
    
    contexto = {
        'paciente': paciente,
        'examenes': examenes_laboratorio,
        'doctores': doctores,
        'doctor_solicitante': doctor_solicitante,
        'fecha_solicitud': timezone.now().date(),
    }
    
    return render(request, 'core/documentos/formulario_examenes.html', contexto)


@login_required
@medico_o_jefe_required
def imprimir_examenes(request, paciente_id):
    """Vista para generar vista de impresión de exámenes seleccionados"""
    paciente = get_object_or_404(Paciente, id=paciente_id, activo=True)
    
    # Obtener datos del POST para la impresión
    examenes_seleccionados = request.POST.getlist('examenes')
    examenes_personalizados = request.POST.get('examenes_personalizados', '').strip()
    observaciones = request.POST.get('observaciones', '').strip()
    doctor_id = request.POST.get('doctor_solicitante')
    
    doctor_solicitante = None
    if doctor_id:
        doctor_solicitante = get_object_or_404(Doctor, id=doctor_id)
    elif request.user.rol == 'MEDICO' and hasattr(request.user, 'perfil_medico'):
        doctor_solicitante = request.user.perfil_medico
    
    contexto = {
        'paciente': paciente,
        'examenes_seleccionados': examenes_seleccionados,
        'examenes_personalizados': examenes_personalizados,
        'observaciones': observaciones,
        'doctor_solicitante': doctor_solicitante,
        'fecha_impresion': timezone.now(),
        'es_impresion': True,  # Flag para aplicar estilos de impresión
    }
    
    return render(request, 'core/documentos/imprimir_examenes.html', contexto)


@login_required
@medico_o_jefe_required
def formulario_receta(request, paciente_id):
    """Vista para crear receta médica e indicaciones (no se guardan en BD)"""
    paciente = get_object_or_404(Paciente, id=paciente_id, activo=True)
    
    doctor_solicitante = None
    if request.user.rol == 'MEDICO' and hasattr(request.user, 'perfil_medico'):
        doctor_solicitante = request.user.perfil_medico
    
    contexto = {
        'paciente': paciente,
        'doctor_solicitante': doctor_solicitante,
        'fecha_actual': timezone.now().date(),
    }
    
    return render(request, 'core/documentos/formulario_receta.html', contexto)


@login_required
@medico_o_jefe_required
def imprimir_receta(request, paciente_id):
    """Vista para generar vista de impresión de receta"""
    paciente = get_object_or_404(Paciente, id=paciente_id, activo=True)
    
    # Obtener datos del POST
    receta = request.POST.get('receta', '').strip()
    indicaciones = request.POST.get('indicaciones', '').strip()
    doctor_id = request.POST.get('doctor_solicitante')
    
    doctor_solicitante = None
    if doctor_id:
        doctor_solicitante = get_object_or_404(Doctor, id=doctor_id)
    elif request.user.rol == 'MEDICO' and hasattr(request.user, 'perfil_medico'):
        doctor_solicitante = request.user.perfil_medico
    
    contexto = {
        'paciente': paciente,
        'receta': receta,
        'indicaciones': indicaciones,
        'doctor_solicitante': doctor_solicitante,
        'fecha_impresion': timezone.now(),
        'es_impresion': True,
    }
    
    return render(request, 'core/documentos/imprimir_receta.html', contexto)



#====================== OBTENER PACIENTE/DOCTOR================
@login_required
def api_obtener_paciente(request, paciente_id):
    """API endpoint para obtener datos de un paciente específico"""
    try:
        paciente = Paciente.objects.get(id=paciente_id, activo=True)
        
        # Calcular edad
        edad = None
        if paciente.fecha_nacimiento:
            from datetime import date
            hoy = date.today()
            edad = hoy.year - paciente.fecha_nacimiento.year - ((hoy.month, hoy.day) < (paciente.fecha_nacimiento.month, paciente.fecha_nacimiento.day))
        
        data = {
            'id': paciente.id,
            'nombre': paciente.nombre,
            'ci': paciente.ci,
            'telefono': paciente.telefono,
            'email': paciente.email,
            'edad': edad,
            'sexo': paciente.get_sexo_display() if hasattr(paciente, 'get_sexo_display') else None,
        }
        return JsonResponse(data)
    except Paciente.DoesNotExist:
        return JsonResponse({'error': 'Paciente no encontrado'}, status=404)

@login_required
def api_obtener_doctor(request, doctor_id):
    """API endpoint para obtener datos de un doctor específico"""
    try:
        doctor = Doctor.objects.get(id=doctor_id, activo=True)
        data = {
            'id': doctor.id,
            'nombre': doctor.nombre,
            'especialidad_display': doctor.get_especialidad_display(),
            'telefono': doctor.telefono,
            'costo_consulta': float(doctor.costo_consulta),
        }
        return JsonResponse(data)
    except Doctor.DoesNotExist:
        return JsonResponse({'error': 'Doctor no encontrado'}, status=404)