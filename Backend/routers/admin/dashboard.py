import psycopg2

from config.database import obtener_conexion
import traceback
import os
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Request, Form, HTTPException, status, UploadFile, File, Depends, Query
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse

# --- Importaciones de la nueva estructura modular ---
# 1. Instancia global de Jinja2Templates
from config_templates import templates 

# 2. Esquemas de validación (DTOs) - Se asume que existen en app/schemas/admin.py
# IMPORTANTE: Se asume que EstudianteAdminSchema tiene el método estático .as_form()
from schemas.admin import PreguntaCreateSchema, EstudianteAdminSchema,PreguntaRetoCreate,OpcionSchema

# 3. Capa de Modelo (Funciones puras de acceso a datos) - Se asume que existen en app/models/admin.py
from models.admin import (
    obtener_metricas_globales_db,
    obtener_historial_examenes_db,
    obtener_todos_los_estudiantes_db,
    obtener_listado_retos_con_metricas_db,
    obtener_catalogo_preguntas_detallado_db
)

router = APIRouter( tags=["Administración"])

@router.get("/", response_class=HTMLResponse)
def panel_inicio(request: Request, msg: Optional[str] = None):
    """
    Dashboard principal unificado del administrador.
    DELEGACIÓN: Llama a múltiples funciones del modelo para obtener datos crudos.
    """
    try:
        preguntas_raw = obtener_catalogo_preguntas_detallado_db() or []
        usuarios_raw = obtener_todos_los_estudiantes_db() or []
        metricas_materias_raw = obtener_metricas_globales_db() or []
        mejores_examenes_raw = obtener_historial_examenes_db() or []
        lista_retos_raw = obtener_listado_retos_con_metricas_db() or []
    except Exception as e:
        # Manejo de error básico si falla la BD
        raise HTTPException(status_code=500, detail=f"Error al conectar con la base de datos: {e}")

    # Lógica de presentación simple
    total_estudiantes = len(usuarios_raw)
    total_preguntas = len(preguntas_raw)
    
    # Cálculo de promedio
    exp_totales = [u['puntaje_total'] for u in usuarios_raw if isinstance(u, dict) and 'puntaje_total' in u]
    promedio_exp = round(sum(exp_totales) / total_estudiantes, 1) if total_estudiantes > 0 else 0.0
    
    # Reordenamiento para la vista
    ultimas_preguntas = preguntas_raw[-5:][::-1]
    
    # Ordenar mejores estudiantes
    mejores_estudiantes = sorted(
        usuarios_raw, 
        key=lambda x: x.get('puntaje_total', 0) if isinstance(x, dict) else 0, 
        reverse=True
    )[:5]

    # Renderizamos la plantilla pasando los datos y el mensaje opcional
    return templates.TemplateResponse(
        request=request,
        name="Admin.html", 
        context={
            "request": request,
            "total_estudiantes": total_estudiantes,
            "total_preguntas": total_preguntas,
            "promedio_exp": promedio_exp,
            "ultimas_preguntas": ultimas_preguntas,
            "mejores_estudiantes": mejores_estudiantes,
            "retos": lista_retos_raw,
            "metricas_retos": [],
            "msg": msg
        }
    )