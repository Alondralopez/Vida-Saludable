from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import joblib
import pandas as pd
from pathlib import Path

# ============================================================
# Inicializar API
# ============================================================

app = FastAPI(
    title="API Sistema Inteligente de Salud Infantil",
    description="API para clasificación general de riesgo infantil mediante Red Neuronal MLP",
    version="3.0"
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

def cargar_modelo():
    """
    Carga el modelo entrenado.
    Se dejan dos nombres posibles para evitar error si en tu proyecto
    el archivo quedó guardado con cualquiera de estos nombres.
    """
    rutas_posibles = [
        Path("model/modelo_general_red_neuronal.pkl"),
        Path("model/modelo_general_red_neuronal_mejorado.pkl"),
        Path("modelo_general_red_neuronal.pkl"),
        Path("modelo_general_red_neuronal_mejorado.pkl")
    ]

    for ruta in rutas_posibles:
        if ruta.exists():
            print(f"Modelo cargado desde: {ruta}")
            return joblib.load(ruta)

    raise RuntimeError(
        "No se encontró el modelo. Verifica que el archivo .pkl esté dentro de la carpeta model/"
    )


try:
    modelo_general = cargar_modelo()
    print("Modelo MLP cargado correctamente")
except Exception as e:
    raise RuntimeError(f"Error cargando el modelo: {e}")


# ============================================================
# ESQUEMA DE ENTRADA
# ============================================================

class SaludInput(BaseModel):
    edad: int = Field(..., example=9)
    grado: int = Field(..., example=4)
    peso: float = Field(..., example=32)
    talla: float = Field(..., example=135)

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

    ojo_izquierdo: float = Field(..., example=9)
    ojo_derecho: float = Field(..., example=9)


# ============================================================
# FUNCIONES DE APOYO
# ============================================================

def calcular_imc(peso: float, talla_cm: float) -> float:
    talla_m = talla_cm / 100

    if talla_m <= 0:
        raise ValueError("La talla debe ser mayor a 0")

    return round(peso / (talla_m ** 2), 2)


def interpretar_clase(clase: int) -> dict:
    niveles = {
        0: {
            "nivel_riesgo": "Riesgo bajo",
            "descripcion": "Sin alerta principal",
            "recomendacion": "Mantener hábitos saludables y seguimiento escolar normal."
        },
        1: {
            "nivel_riesgo": "Riesgo medio",
            "descripcion": "Requiere seguimiento",
            "recomendacion": "Se recomienda revisar los indicadores nutricionales o visuales con mayor atención."
        },
        2: {
            "nivel_riesgo": "Riesgo alto",
            "descripcion": "Requiere atención prioritaria",
            "recomendacion": "Se recomienda canalizar al estudiante para valoración médica o seguimiento especializado."
        }
    }

    return niveles.get(
        clase,
        {
            "nivel_riesgo": "No disponible",
            "descripcion": "Clase no reconocida",
            "recomendacion": "Revisar la salida del modelo."
        }
    )


# ============================================================
# RUTA PRINCIPAL
# ============================================================

@app.get("/")
def root():
    return {
        "message": "API de Salud Infantil funcionando correctamente",
        "modelo": "Red Neuronal MLP Multiclase",
        "version": "3.0",
        "autor": "Daniel Ceja",
        "endpoints": {
            "prediccion": "/api/predict",
            "documentacion": "/docs",
            "healthcheck": "/health"
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
        # VALIDACIONES BÁSICAS
        # ====================================================

        if datos.edad <= 0:
            raise ValueError("La edad debe ser mayor a 0")

        if datos.grado < 1 or datos.grado > 6:
            raise ValueError("El grado debe estar entre 1 y 6")

        if datos.peso <= 0:
            raise ValueError("El peso debe ser mayor a 0")

        if datos.talla <= 0:
            raise ValueError("La talla debe ser mayor a 0")

        if datos.sexo not in [0, 1]:
            raise ValueError("El sexo debe ser 0 = Femenino o 1 = Masculino")

        if datos.usa_lentes not in [0, 1]:
            raise ValueError("Usa lentes debe ser 0 = No o 1 = Sí")

        if datos.ojo_izquierdo < 0 or datos.ojo_derecho < 0:
            raise ValueError("Los valores de visión no pueden ser negativos")

        # ====================================================
        # VARIABLES DERIVADAS
        # ====================================================

        imc = calcular_imc(datos.peso, datos.talla)

        vision_promedio = round(
            (datos.ojo_izquierdo + datos.ojo_derecho) / 2,
            2
        )

        diferencia_visual = round(
            abs(datos.ojo_izquierdo - datos.ojo_derecho),
            2
        )

        # ====================================================
        # DATAFRAME EXACTAMENTE IGUAL AL ENTRENAMIENTO FINAL
        # ====================================================
        # Según el modelo único del notebook, las columnas usadas fueron:
        # edad, peso, talla, imc, ojo izquierdo, ojo derecho, usa lentes.
        # vision_promedio y diferencia_visual se calculan solo para mostrarlas.

        columnas_modelo_general = [
            "edad",
            "peso",
            "talla",
            "imc",
            "ojo izquierdo",
            "ojo derecho",
            "usa lentes"
        ]

        X = pd.DataFrame([{
            "edad": datos.edad,
            "peso": datos.peso,
            "talla": datos.talla,
            "imc": imc,
            "ojo izquierdo": datos.ojo_izquierdo,
            "ojo derecho": datos.ojo_derecho,
            "usa lentes": datos.usa_lentes
        }])

        X = X[columnas_modelo_general]

        # ====================================================
        # PREDICCIÓN
        # ====================================================

        prediccion = int(modelo_general.predict(X)[0])

        probabilidades = modelo_general.predict_proba(X)[0]
        probabilidad = round(float(max(probabilidades)) * 100, 2)

        interpretacion = interpretar_clase(prediccion)

        # ====================================================
        # RESPUESTA JSON PARA EL FRONTEND
        # ====================================================

        return {
            "datos_recibidos": {
                "edad": datos.edad,
                "grado": datos.grado,
                "peso": datos.peso,
                "talla": datos.talla,
                "sexo": datos.sexo,
                "sexo_texto": "Masculino" if datos.sexo == 1 else "Femenino",
                "usa_lentes": datos.usa_lentes,
                "usa_lentes_texto": "Sí" if datos.usa_lentes == 1 else "No",
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
                "nivel_riesgo": interpretacion["nivel_riesgo"],
                "descripcion": interpretacion["descripcion"],
                "probabilidad": probabilidad,
                "recomendacion": interpretacion["recomendacion"]
            }
        }

    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )


# ============================================================
# RUTA ALTERNATIVA
# ============================================================

@app.post("/predict")
def predict_alt(datos: SaludInput):
    return predict(datos)
