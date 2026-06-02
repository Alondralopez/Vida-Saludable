from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

import joblib
import pandas as pd

# ============================================================
# Inicializar API
# ============================================================

app = FastAPI(
    title="API Sistema Inteligente de Salud Infantil",
    description="API para clasificación de riesgo infantil mediante Red Neuronal MLP",
    version="2.1"
)

# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# CARGAR MODELO ÚNICO
# ============================================================

try:
    modelo_general = joblib.load("model/modelo_general_red_neuronal.pkl")
    print("Modelo MLP cargado correctamente")
except Exception as e:
    raise RuntimeError(f"Error cargando el modelo: {e}")

# ============================================================
# ESQUEMA DE ENTRADA
# ============================================================

class SaludInput(BaseModel):
    edad: int = Field(..., example=9)
    peso: float = Field(..., example=28)
    talla: float = Field(..., example=140)

    sexo: int = Field(
        ...,
        example=1,
        description="0 = Femenino, 1 = Masculino"
    )

    usa_lentes: int = Field(
        ...,
        example=0,
        description="0 = No, 1 = Sí"
    )

    ojo_izquierdo: float = Field(..., example=10)
    ojo_derecho: float = Field(..., example=10)
# ============================================================
# FUNCIONES AUXILIARES
# ============================================================

def calcular_imc(peso: float, talla_cm: float) -> float:
    talla_m = talla_cm / 100

    if talla_m <= 0:
        raise ValueError("La talla debe ser mayor a 0")

    return round(peso / (talla_m ** 2), 2)

# ============================================================
# RUTA PRINCIPAL
# ============================================================

@app.get("/")
def root():
    return {
        "message": "API de Salud Infantil funcionando correctamente",
        "modelo": "Red Neuronal MLP Multiclase",
        "version": "2.1",
        "autor": "Daniel Ceja",
        "endpoints": {
            "prediccion": "/api/predict",
            "documentacion": "/docs"
        }
    }

# ============================================================
# HEALTHCHECK
# ============================================================

@app.get("/health")
def health():
    return {
        "status": "ok",
        "modelo": "MLP cargado correctamente"
    }

# ============================================================
# PREDICCIÓN
# ============================================================

@app.post("/api/predict")
def predict(datos: SaludInput):
    try:
        # ====================================================
        # VARIABLES DERIVADAS
        # ====================================================

        imc = calcular_imc(datos.peso, datos.talla)

        vision_promedio = round((datos.ojo_izquierdo + datos.ojo_derecho) / 2, 2)

        diferencia_visual = round(abs(datos.ojo_izquierdo - datos.ojo_derecho), 2)

        # ====================================================
        # DATAFRAME CON LAS 9 COLUMNAS DEL ENTRENAMIENTO
        # ====================================================
        # IMPORTANTE:
        # El modelo espera 9 variables. Si se mandan 7, aparece:
        # X has 7 features, but MLPClassifier is expecting 9 features.

        X = pd.DataFrame([{
            "edad": datos.edad,
            "peso": datos.peso,
            "talla": datos.talla,
            "imc": imc,
            "ojo izquierdo": datos.ojo_izquierdo,
            "ojo derecho": datos.ojo_derecho,
            "vision_promedio": vision_promedio,
            "diferencia_visual": diferencia_visual,
            "usa lentes": datos.usa_lentes
        }])

        # ====================================================
        # PREDICCIÓN
        # ====================================================

        prediccion = int(modelo_general.predict(X)[0])
        probabilidades = modelo_general.predict_proba(X)[0]
        probabilidad = round(max(probabilidades) * 100, 2)

        # ====================================================
        # ETIQUETAS
        # ====================================================

        niveles = {
            0: "Riesgo bajo - Sin alerta principal",
            1: "Riesgo medio - Requiere seguimiento",
            2: "Riesgo alto - Requiere atención prioritaria"
        }

        recomendaciones = {
            0: "El estudiante no presenta una alerta principal según el modelo. Se recomienda mantener hábitos saludables y revisiones periódicas.",
            1: "El estudiante requiere seguimiento preventivo. Se recomienda revisar sus condiciones nutricionales y visuales.",
            2: "El estudiante requiere atención prioritaria. Se recomienda canalizarlo para una valoración más detallada."
        }

        # ====================================================
        # RESPUESTA JSON
        # ====================================================

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
            "resultado_modelo": {
                "clase": prediccion,
                "nivel_riesgo": niveles.get(prediccion, "Clase desconocida"),
                "probabilidad": probabilidad,
                "recomendacion": recomendaciones.get(prediccion, "Sin recomendación disponible")
            }
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# ============================================================
# RUTA ALTERNATIVA
# ============================================================

@app.post("/predict")
def predict_alt(datos: SaludInput):
    return predict(datos)
