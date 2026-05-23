from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import joblib
import pandas as pd
import numpy as np

# -----------------------------------
# Inicializar aplicación
# -----------------------------------
app = FastAPI(
    title="API Sistema Inteligente de Salud Infantil",
    description="API para evaluar riesgo nutricional y visual mediante modelos de Machine Learning",
    version="1.0"
)

# -----------------------------------
# Configuración CORS
# -----------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción cambia esto por el dominio de tu frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -----------------------------------
# Cargar modelos UNA sola vez
# -----------------------------------
try:
    modelo_nutricional = joblib.load("model/modelo_nutricional_xgb.pkl")
    modelo_visual = joblib.load("model/modelo_visual_xgb.pkl")
    print("Modelos cargados correctamente")
except Exception as e:
    raise RuntimeError(f"Error cargando los modelos: {e}")

# -----------------------------------
# Esquema de entrada
# -----------------------------------
class SaludInput(BaseModel):
    edad: int = Field(..., example=9)
    grado: int = Field(..., example=4)
    peso: float = Field(..., example=32)
    talla: float = Field(..., example=135)
    sexo: int = Field(..., example=1, description="0 = Femenino, 1 = Masculino")
    usa_lentes: int = Field(..., example=0, description="0 = No, 1 = Sí")
    ojo_izquierdo: float = Field(..., example=9)
    ojo_derecho: float = Field(..., example=9)

# -----------------------------------
# Función para calcular IMC
# -----------------------------------
def calcular_imc(peso: float, talla_cm: float) -> float:
    talla_m = talla_cm / 100
    if talla_m <= 0:
        raise ValueError("La talla debe ser mayor a 0")
    return round(peso / (talla_m ** 2), 2)

# -----------------------------------
# Motor de decisión general
# -----------------------------------
def obtener_conclusion_general(riesgo_nutricional: int, riesgo_visual: int) -> str:
    if riesgo_nutricional == 1 and riesgo_visual == 1:
        return "Riesgo alto - Requiere atención prioritaria"
    elif riesgo_nutricional == 1 and riesgo_visual == 0:
        return "Riesgo medio - Requiere revisión nutricional"
    elif riesgo_nutricional == 0 and riesgo_visual == 1:
        return "Riesgo medio - Requiere revisión visual"
    else:
        return "Riesgo bajo - Sin alerta principal"

# -----------------------------------
# Ruta raíz
# -----------------------------------
@app.get("/")
def root():
    return {
        "message": "API del Sistema Inteligente de Salud Infantil funcionando correctamente",
        "version": "1.0",
        "autor": "Daniel Ceja",
        "endpoints": {
            "prediccion": "/api/predict",
            "documentacion": "/docs"
        }
    }

# -----------------------------------
# Ruta de prueba
# -----------------------------------
@app.get("/health")
def health():
    return {
        "status": "ok",
        "message": "API activa y modelos cargados"
    }

# -----------------------------------
# Ruta de predicción
# -----------------------------------
@app.post("/api/predict")
def predict(datos: SaludInput):
    try:
        # -----------------------------------
        # Calcular variables derivadas
        # -----------------------------------
        imc = calcular_imc(datos.peso, datos.talla)

        vision_promedio = round(
            (datos.ojo_izquierdo + datos.ojo_derecho) / 2,
            2
        )

        diferencia_visual = round(
            abs(datos.ojo_izquierdo - datos.ojo_derecho),
            2
        )

        # -----------------------------------
        # DataFrame para modelo nutricional
        # IMPORTANTE: debe tener el mismo orden de columnas usado al entrenar
        # -----------------------------------
        X_nutricional = pd.DataFrame([{
            "edad": datos.edad,
            "peso": datos.peso,
            "talla": datos.talla,
            "imc": imc
        }])

        # -----------------------------------
        # DataFrame para modelo visual
        # IMPORTANTE: debe tener el mismo orden de columnas usado al entrenar
        # -----------------------------------
        X_visual = pd.DataFrame([{
            "ojo izquierdo": datos.ojo_izquierdo,
            "ojo derecho": datos.ojo_derecho,
            "vision_promedio": vision_promedio,
            "diferencia_visual": diferencia_visual,
            "usa lentes": datos.usa_lentes
        }])

        # -----------------------------------
        # Predicciones
        # -----------------------------------
        pred_nutricional = int(modelo_nutricional.predict(X_nutricional)[0])
        pred_visual = int(modelo_visual.predict(X_visual)[0])

        # -----------------------------------
        # Probabilidades
        # -----------------------------------
        prob_nutricional = float(modelo_nutricional.predict_proba(X_nutricional)[0][1])
        prob_visual = float(modelo_visual.predict_proba(X_visual)[0][1])

        # Convertir a porcentaje
        prob_nutricional_pct = round(prob_nutricional * 100, 2)
        prob_visual_pct = round(prob_visual * 100, 2)

        # -----------------------------------
        # Conclusión general
        # -----------------------------------
        conclusion = obtener_conclusion_general(
            pred_nutricional,
            pred_visual
        )

        # -----------------------------------
        # Respuesta para el frontend
        # -----------------------------------
        return {
            "datos_recibidos": {
                "edad": datos.edad,
                "grado": datos.grado,
                "peso": datos.peso,
                "talla": datos.talla,
                "sexo": datos.sexo,
                "usa_lentes": datos.usa_lentes,
                "ojo_izquierdo": datos.ojo_izquierdo,
                "ojo_derecho": datos.ojo_derecho
            },
            "variables_calculadas": {
                "imc": imc,
                "vision_promedio": vision_promedio,
                "diferencia_visual": diferencia_visual
            },
            "evaluacion_nutricional": {
                "riesgo": "Sí" if pred_nutricional == 1 else "No",
                "clase": pred_nutricional,
                "probabilidad": prob_nutricional_pct
            },
            "evaluacion_visual": {
                "riesgo": "Sí" if pred_visual == 1 else "No",
                "clase": pred_visual,
                "probabilidad": prob_visual_pct
            },
            "resultado_general": {
                "conclusion": conclusion
            }
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# -----------------------------------
# Ruta alternativa por si tu frontend usa /predict
# -----------------------------------
@app.post("/predict")
def predict_alt(datos: SaludInput):
    return predict(datos)
