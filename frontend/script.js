const API_URL = 'https://vida-saludable-api.onrender.com/api/predict';


const form = document.getElementById('formSalud');
const resultado = document.getElementById('resultadoApi');

function calcularIMC(peso, tallaCm) {
  const tallaM = tallaCm / 100;
  return peso / (tallaM * tallaM);
}

function obtenerTextoSexo(valor) {
  return valor === 1 ? 'Masculino' : 'Femenino';
}

function obtenerTextoLentes(valor) {
  return valor === 1 ? 'Sí' : 'No';
}

function obtenerClaseRiesgo(clase) {
  if (clase === 0) return 'riesgo-bajo';
  if (clase === 1) return 'riesgo-medio';
  if (clase === 2) return 'riesgo-alto';
  return '';
}

function mostrarResultado(data) {
  const datos = data.datos_recibidos ?? {};
  const variables = data.variables_calculadas ?? {};
  const modelo = data.resultado_modelo ?? {};

  const imc = variables.imc ?? 'No disponible';
  const visionPromedio = variables.vision_promedio ?? 'No disponible';
  const diferenciaVisual = variables.diferencia_visual ?? 'No disponible';

  const clase = modelo.clase ?? 'No disponible';
  const nivelRiesgo = modelo.nivel_riesgo ?? 'No disponible';
  const descripcion = modelo.descripcion ?? 'No disponible';
  const probabilidad = modelo.probabilidad ?? 'No disponible';
  const recomendacion = modelo.recomendacion ?? 'No disponible';

  const claseRiesgo = obtenerClaseRiesgo(Number(clase));

  resultado.innerHTML = `
    <strong>Respuesta de la API:</strong>

    <div class="result-grid">

      <div class="result-card">
        <h4>Datos recibidos</h4>
        <p><b>Edad:</b> ${datos.edad ?? 'No disponible'} años</p>
        <p><b>Grado:</b> ${datos.grado ?? 'No disponible'}°</p>
        <p><b>Sexo:</b> ${datos.sexo_texto ?? obtenerTextoSexo(Number(datos.sexo))}</p>
        <p><b>Usa lentes:</b> ${datos.usa_lentes_texto ?? obtenerTextoLentes(Number(datos.usa_lentes))}</p>
      </div>

      <div class="result-card">
        <h4>Variables calculadas</h4>
        <p><b>IMC:</b> ${imc}</p>
        <p><b>Visión promedio:</b> ${visionPromedio}</p>
        <p><b>Diferencia visual:</b> ${diferenciaVisual}</p>
      </div>

      <div class="result-card">
        <h4>Clasificación del modelo</h4>
        <p><b>Clase:</b> ${clase}</p>
        <p><b>Nivel de riesgo:</b> <span class="${claseRiesgo}">${nivelRiesgo}</span></p>
        <p><b>Descripción:</b> ${descripcion}</p>
        <p><b>Probabilidad:</b> ${probabilidad}%</p>
      </div>

      <div class="result-card conclusion-card">
        <h4>Conclusión general</h4>
        <p><b class="${claseRiesgo}">${nivelRiesgo}</b></p>
        <p>${recomendacion}</p>
      </div>

    </div>
  `;
}

function validarDatos(datos) {
  if (datos.edad <= 0) return 'La edad debe ser mayor a 0.';
  if (datos.grado < 1 || datos.grado > 6) return 'El grado debe estar entre 1 y 6.';
  if (datos.peso <= 0) return 'El peso debe ser mayor a 0.';
  if (datos.talla <= 0) return 'La talla debe ser mayor a 0.';
  if (datos.ojo_izquierdo < 0 || datos.ojo_derecho < 0) return 'Los valores de visión no pueden ser negativos.';
  return null;
}

form.addEventListener('submit', async (event) => {
  event.preventDefault();

  const edad = Number(document.getElementById('edad').value);
  const grado = Number(document.getElementById('grado').value);
  const peso = Number(document.getElementById('peso').value);
  const talla = Number(document.getElementById('talla').value);
  const sexo = Number(document.getElementById('sexo').value);
  const usa_lentes = Number(document.getElementById('usa_lentes').value);
  const ojo_izquierdo = Number(document.getElementById('ojo_izquierdo').value);
  const ojo_derecho = Number(document.getElementById('ojo_derecho').value);

  const imc = Number(calcularIMC(peso, talla).toFixed(2));
  const vision_promedio = Number(((ojo_izquierdo + ojo_derecho) / 2).toFixed(2));
  const diferencia_visual = Number(Math.abs(ojo_izquierdo - ojo_derecho).toFixed(2));

  const payload = {
    edad,
    peso,
    talla,
    sexo,
    usa_lentes,
    ojo_izquierdo,
    ojo_derecho
  };

  const errorValidacion = validarDatos(payload);

  if (errorValidacion) {
    resultado.innerHTML = `
      <strong>Error en el formulario</strong>
      <p>${errorValidacion}</p>
    `;
    return;
  }

  resultado.innerHTML = `
    <strong>Consultando API...</strong>
    <p>Calculando variables:</p>
    <p><b>IMC:</b> ${imc}</p>
    <p><b>Visión promedio:</b> ${vision_promedio}</p>
    <p><b>Diferencia visual:</b> ${diferencia_visual}</p>
  `;

  try {
    const response = await fetch(API_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(payload)
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || 'La API respondió con error');
    }

    mostrarResultado(data);

  } catch (error) {
    console.error(error);

    resultado.innerHTML = `
      <strong>Error al consultar la API</strong>
      <p>No se pudo obtener respuesta del servidor.</p>
      <p><b>Detalle:</b> ${error.message}</p>
      <p>Verifica que la API esté activa en Render y que el endpoint sea correcto.</p>
    `;
  }
});
