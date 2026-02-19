# core/urls.py
from django.urls import path
from . import views

urlpatterns = [
    
    # Autenticación
    path('', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Pacientes
    path('pacientes/', views.lista_pacientes, name='lista_pacientes'),
    path('pacientes/crear/', views.crear_paciente, name='crear_paciente'),
    path('pacientes/<int:id>/', views.detalle_paciente, name='detalle_paciente'),
    path('pacientes/<int:id>/editar/', views.editar_paciente, name='editar_paciente'),
    path('api/pacientes/buscar/', views.api_buscar_pacientes, name='api_buscar_pacientes'),
    path('api/pacientes/<int:paciente_id>/', views.api_obtener_paciente, name='api_obtener_paciente'),


   # ==================== DOCTORES ====================
    path('doctores/', views.lista_doctores, name='lista_doctores'),
    path('doctores/crear/', views.crear_doctor, name='crear_doctor'),
    path('doctores/<int:id>/', views.detalle_doctor, name='detalle_doctor'),
    path('doctores/<int:id>/editar/', views.editar_doctor, name='editar_doctor'),
    path('doctores/<int:id>/activar/', views.activar_doctor, name='activar_doctor'),
    path('api/doctores/<int:doctor_id>/', views.api_obtener_doctor, name='api_obtener_doctor'),
    # API Endpoints para doctores
    path('api/doctores/buscar/', views.api_buscar_doctores, name='api_buscar_doctores'),
    
    # Citas
    path('citas/', views.lista_citas, name='lista_citas'),
    path('citas/crear/', views.crear_cita, name='crear_cita'),
    path('citas/<int:id>/', views.detalle_cita, name='detalle_cita'),
    path('citas/<int:id>/cancelar/', views.cancelar_cita, name='cancelar_cita'),
    path('citas/<int:id>/completar/', views.completar_cita, name='completar_cita'),
    
    # Perfil
    path('perfil/', views.perfil, name='perfil'),
    path('perfil/editar/', views.editar_perfil, name='editar_perfil'),

    # ==================== API ENDPOINTS ====================
    path('api/pacientes/buscar/', views.api_buscar_pacientes, name='api_buscar_pacientes'),

   

    # ==================== EXPEDIENTE MÉDICO ====================
    path('pacientes/<int:paciente_id>/expediente/', views.ver_expediente, name='ver_expediente'),
    path('pacientes/<int:paciente_id>/expediente/actualizar/', views.actualizar_expediente, name='actualizar_expediente'),
    path('pacientes/<int:paciente_id>/expediente/activar/', views.activar_expediente, name='activar_expediente'),
    
    # Diagnósticos
    path('pacientes/<int:paciente_id>/diagnostico/crear/', views.crear_diagnostico, name='crear_diagnostico'),
    path('diagnostico/<int:diagnostico_id>/editar/', views.editar_diagnostico, name='editar_diagnostico'),
    path('diagnostico/<int:diagnostico_id>/activar/', views.activar_diagnostico, name='activar_diagnostico'),

   
    # ==================== GESTIÓN DE STAFF ====================
    path('staff/', views.lista_staff, name='lista_staff'),
    path('staff/crear/', views.crear_staff_usuario, name='crear_staff_usuario'),
    path('staff/<int:usuario_id>/editar/', views.editar_staff_usuario, name='editar_staff_usuario'),
    path('staff/<int:usuario_id>/activar/', views.activar_staff_usuario, name='activar_staff_usuario'),
    path('doctores/<int:doctor_id>/vincular-usuario/', views.vincular_doctor_usuario, name='vincular_doctor_usuario'), 
 

    # ==================== CALENDARIO DE CITAS ====================
    path('calendario/', views.calendario_citas, name='calendario_citas'),
    path('api/calendario/citas/', views.api_calendario_citas, name='api_calendario_citas'),
    path('api/calendario/disponibilidad/', views.api_verificar_disponibilidad, name='api_verificar_disponibilidad'),

 

    # ==================== DOCUMENTOS MÉDICOS (IMPRESIÓN) ====================
    path('pacientes/<int:paciente_id>/examenes/', views.formulario_examenes, name='formulario_examenes'),
    path('pacientes/<int:paciente_id>/receta/', views.formulario_receta, name='formulario_receta'),
    path('pacientes/<int:paciente_id>/imprimir/examenes/', views.imprimir_examenes, name='imprimir_examenes'),
    path('pacientes/<int:paciente_id>/imprimir/receta/', views.imprimir_receta, name='imprimir_receta'),

    # ==================== PAGINS PUBLICAS ====================
    path('privacidad/', views.politica_privacidad, name='politica_privacidad'),
    path('terminos/', views.terminos_usos, name='terminos_usos'),
     

    # ==================== ESPECIALIDADES MÉDICAS ====================
    path('especialidades/', views.lista_especialidades, name='lista_especialidades'),
    path('especialidades/crear/', views.crear_especialidad, name='crear_especialidad'),
    path('especialidades/<int:especialidad_id>/editar/', views.editar_especialidad, name='editar_especialidad'),
    path('especialidades/<int:especialidad_id>/activar/', views.activar_especialidad, name='activar_especialidad'),
    path('especialidades/<int:especialidad_id>/eliminar/', views.eliminar_especialidad, name='eliminar_especialidad'),
    
    # ==================== ESPECIALIDADES DESDE DASHBOARD ====================
    path('dashboard/agregar-especialidad/', views.agregar_especialidad_dashboard, name='agregar_especialidad_dashboard'),
]