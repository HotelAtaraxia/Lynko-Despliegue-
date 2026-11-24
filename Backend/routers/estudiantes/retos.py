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
    obtener_reto_semanal_activo_db,
    obtener_contexto_base,
    guardar_intento_reto_db,
    calificar_y_guardar_reto_db,
    finalizar_intento_reto_db

)

router = APIRouter(tags=["Estudiantes"])

@router.get("/progreso-estudiante/{id_usuario}", response_class=HTMLResponse)
def vista_reto_semanal(id_usuario: int, request: Request):
    """
    Muestra el reto semanal activo para el estudiante consumiendo la BD real.
    """
    contexto_base = obtener_contexto_base(id_usuario)
    
    # 1. Llamamos a tu función de la BD
    reto_raw, preguntas_raw = obtener_reto_semanal_activo_db(id_usuario)
    
    reto_formateado = None
    if reto_raw:
        reto_formateado = {
            "id_reto": reto_raw['id_reto'],
            "titulo": reto_raw['titulo_general'], # ⚠️ Ojo aquí: en la BD se llama titulo_general
            "descripcion": reto_raw['descripcion'],
            "puntos_recompensa_max": reto_raw['puntos_recompensa_total'],
            "completado": bool(reto_raw.get('ya_completado')),
            "link_audio": reto_raw['link_audio'],
            "preguntas": preguntas_raw # Trae id_pregunta_reto, pregunta, puntos_recompensa y opciones
        }

    contexto = {
        "request": request,
        "id_usuario": id_usuario,
        **contexto_base,
        "reto": reto_formateado,
        "mensaje": "¡Ya has completado el reto de esta semana!" if (reto_formateado and reto_formateado['completado']) else ""
    }
    
    return templates.TemplateResponse(
        request=request,
        name="Reto_semanal.html",
        context=contexto
    )

@router.post("/api/retos/{id_reto}/iniciar")
def api_iniciar_intento_reto(id_reto: int, id_usuario: int = Query(...)):

    try:
        id_intento = guardar_intento_reto_db(id_usuario, id_reto)
        return {"status": "success", "id_intento": id_intento}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

import re
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse

@router.post("/guardar-reto/{id_usuario}/{id_reto}")
async def guardar_reto_estudiante(id_usuario: int, id_reto: int, request: Request):
    try:
        form_data = await request.form()
        
        # Procesar dinámicamente las respuestas del formulario de preguntas del reto
        respuestas_usuario = {}
        for key, value in form_data.items():
            if key.startswith("pregunta_"):
                if value and str(value).strip():
                    try:
                        # Extrae el ID de la pregunta desde el nombre del campo (ej. pregunta_4 -> 4)
                        numeros = re.findall(r'\d+', key)
                        if numeros:
                            id_pregunta_reto = int(numeros[0])
                            respuestas_usuario[id_pregunta_reto] = int(value)
                    except ValueError:
                        continue

        # Ejecutar la lógica de calificación y otorgamiento de premios conectando a la BD
        with obtener_conexion() as conexion:
            resultado_calificacion = calificar_y_guardar_reto_db(id_usuario, id_reto, respuestas_usuario, conexion)
            
            if "error" in resultado_calificacion:
                raise HTTPException(status_code=400, detail=resultado_calificacion["error"])
            
            avatar_nuevo = resultado_calificacion.get("avatar_desbloqueado_nuevo")

        # Preparar contexto para recargar la vista con el estado de "Completado" y el modal activo
        contexto_base = obtener_contexto_base(id_usuario)
        reto_raw, preguntas_raw = obtener_reto_semanal_activo_db(id_usuario)
        
        reto_formateado = None
        if reto_raw:
            reto_formateado = {
                "id_reto": reto_raw['id_reto'],
                "titulo": reto_raw['titulo_general'],
                "descripcion": reto_raw['descripcion'],
                "puntos_recompensa_max": reto_raw['puntos_recompensa_total'],
                "completado": True,  # Forzamos a que aparezca como completado
                "link_audio": reto_raw['link_audio'],
                "preguntas": preguntas_raw
            }

        return templates.TemplateResponse(
            request=request,
            name="Reto_semanal.html",
            context={
                "request": request,
                "id_usuario": id_usuario,
                **contexto_base,
                "reto": reto_formateado,
                "avatar_desbloqueado_nuevo": avatar_nuevo # <--- ¡Este despliega automáticamente el modal navideño!
            }
        )

    except Exception as e:
        print(f"Error crítico al guardar reto: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    
@router.post("/api/retos/{id_intento}/finalizar")
def api_finalizar_intento_reto(
    id_intento: int,
    data: dict = Body(...),
    id_usuario: int = Query(...) 
):
    
    try:
        puntaje = data.get("puntaje_total", 0)
        usuario_id = data.get("id_usuario")
        finalizar_intento_reto_db(id_intento, puntaje, usuario_id)
        return {"status": "success", "message": "Reto finalizado"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

def finalizar_intento_reto_db(id_intento: int, puntaje: int, id_usuario: int):
    conexion_db = obtener_conexion() # Asumiendo tu función de conexión
    cursor = conexion_db.cursor()
    try:
        # 1. Obtener el id_reto asociado a este intento
        cursor.execute("SELECT id_reto FROM intentos_retos WHERE id_intento = %s", (id_intento,))
        res_intento = cursor.fetchone()
        if not res_intento:
            raise Exception("Intento no encontrado")
        id_reto = res_intento[0]

        # 2. Marcar el reto como completado / guardar puntaje (Tu lógica actual)
        cursor.execute("""
            UPDATE intentos_reto 
            SET estado = 'FINALIZADO', puntaje_obtenido = %s 
            WHERE id_intento = %s
        """, (puntaje, id_intento))

        # 3. VERIFICAR SI ESTE RETO TIENE UN AVATAR NAVIDEÑO / HITO ASOCIADO (RF-34)
        cursor.execute("""
            SELECT id_item FROM items_desbloqueables 
            WHERE requisito_tipo = 'reto_semanal' AND id_reto_asociado = %s
        """, (id_reto,))
        item_premio = cursor.fetchone()

        if item_premio:
            id_item = item_premio[0]
            # 4. Asignar el avatar al inventario del usuario (si no lo tiene ya)
            cursor.execute("""
                INSERT INTO usuario_items_desbloqueables (id_usuario, id_item)
                VALUES (%s, %s)
                ON CONFLICT (id_usuario, id_item) DO NOTHING;
            """, (id_usuario, id_item))

        conexion_db.commit()
    except Exception as e:
        conexion_db.rollback()
        raise e
    finally:
        cursor.close()
        conexion_db.close()