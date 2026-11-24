import secrets
import jwt
from fastapi.responses import JSONResponse
from fastapi import APIRouter, Request, Form, HTTPException, Query, status, Depends, Body
from fastapi.responses import HTMLResponse, RedirectResponse
import os
from typing import Optional
from datetime import datetime, timedelta
from pydantic import EmailStr
from starlette.responses import JSONResponse
from flask import request, jsonify, render_template
import re
import psycopg2

from config.database import obtener_conexion
from config_templates import templates 


from schemas.estudiante import EstudianteActualizar, RecuperarRequest, ActualizarPasswordRequest, MinijuegoRequest, RespuestaEstudianteCompletar


from models.estudiantes import (
    obtener_contexto_base,
    calificar_y_guardar_examen_db,
    obtener_examen_para_estudiante_db,
   

)

router = APIRouter(tags=["Estudiantes"])

@router.get("/resolver-examen/{id_materia}/{id_examen}/{id_usuario}", response_class=HTMLResponse)
def vista_resolver_examen_individual(id_materia: int, id_examen: int, request: Request, id_usuario: int):
    datos_base = obtener_contexto_base(id_usuario)
    
    with obtener_conexion() as conexion:
        # 1. Consultar la materia para que {{ materia.nombre }} y {{ materia.imagen_banner }} existan
        with conexion.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cursor:
            cursor.execute("SELECT id_materia, nombre, descripcion, imagen_banner FROM materias WHERE id_materia = %s;", (id_materia,))
            materia = cursor.fetchone()
            if not materia:
                raise HTTPException(status_code=404, detail="Materia no encontrada")

        # 2. Consultar el examen
        examen = obtener_examen_para_estudiante_db(id_examen, conexion)
        if not examen:
            raise HTTPException(status_code=404, detail="Examen no encontrado")
            
        # 3. Enviar la variable 'materia' en el contexto junto con el examen
        return templates.TemplateResponse(
            request=request, 
            name="Actividades.html", 
            context={
                "request": request, 
                "id_usuario": id_usuario, 
                **datos_base, 
                "materia": materia,  # <--- ¡Esto era lo que faltaba y causaba el Error 500!
                "examen": examen
            }
        )

@router.post("/examen/{id_examen}/enviar")
async def enviar_respuestas_examen(request: Request, id_examen: int):
    try:
        form_data = await request.form()
        
        # Intentar obtener el id_usuario del formulario (enviado por el input hidden) o de la cookie
        id_usuario_str = form_data.get("id_usuario")
        if not id_usuario_str:
            id_usuario_str = request.cookies.get("id_usuario")
            
        if not id_usuario_str:
            return JSONResponse(status_code=400, content={"error": "Falta id_usuario en la solicitud"})
        
        id_usuario = int(id_usuario_str)
        
        # Extraer las respuestas del formulario dinámicamente (ej: pregunta_5: 12)
        respuestas_usuario = {}
        for key, value in form_data.items():
            if key.startswith("pregunta_"):
                if value and str(value).strip():
                    try:
                        id_pregunta = int(key.split("_")[1])
                        respuestas_usuario[id_pregunta] = int(value)
                    except ValueError:
                        continue

        # Conectar a la BD y calificar
        with obtener_conexion() as conexion:
            resultado = calificar_y_guardar_examen_db(id_usuario, id_examen, respuestas_usuario, conexion)
            return JSONResponse(status_code=200, content=resultado)

    except Exception as e:
        print(f"Error crítico al calificar examen: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al calificar: {str(e)}")
    
@router.get("/resolver-examen/{id_materia}/{id_examen}/{id_usuario}", response_class=HTMLResponse)
def vista_resolver_examen_individual(id_examen: int, request: Request, id_usuario: int):
    datos_base = obtener_contexto_base(id_usuario)
    
    with obtener_conexion() as conexion:
        examen = obtener_examen_para_estudiante_db(id_examen, conexion)
        if not examen:
            raise HTTPException(status_code=404, detail="Examen no encontrado")
            
        return templates.TemplateResponse(
            request=request, 
            name="Actividades.html", 
            context={
                "request": request, 
                "id_usuario": id_usuario, 
                **datos_base, 
                "examen": examen
            }
        )