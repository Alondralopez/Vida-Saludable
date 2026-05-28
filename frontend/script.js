const API_URL = 'https://vida-saludable-api.onrender.com/api/predict';

const form = document.getElementById('formSalud');
const resultado = document.getElementById('resultadoApi');

function calcularIMC(peso, tallaCm) {
  const tallaM = tallaCm / 100;
  return peso / (tallaM * tallaM);
}

function mostrarResultado(data) {
  const imc = data.variables_calculadas?.imc ?? 'No disponible';
  const visionPromedio = data.variables_calculadas?.vision_promedio ?? 'No disponible';
  const diferenciaVisual = data.variables_calculadas?.diferencia_visual ?? 'No disponible';

  const clase = data.resultado_modelo?.clase ?? 'No disponible';
  const nivelRiesgo = data.resultado_modelo?.nivel_riesgo ?? 'No disponible';
  const probabilidad = data.resultado_modelo?.probabilidad ?? 'No disponible';

  resultado.innerHTML = `
    <strong>Respuesta de la API:</strong>

    <div class="result-grid">

      <div class="result-card">
        <h4>Variables calculadas</h4>
        <p><b>IMC:</b> ${imc}</p>
        <p><b>Visión promedio:</b> ${visionPromedio}</p>
        <p><b>Diferencia visual:</b> ${diferenciaVisual}</p>
      </div>

      <div class="result-card">
        <h4>Clasificación del modelo</h4>
        <p><b>Clase:</b> ${clase}</p>
        <p><b>Nivel de riesgo:</b> ${nivelRiesgo}</p>
        <p><b>Probabilidad:</b> ${probabilidad}%</p>
      </div>

      <div class="result-card">
        <h4>Conclusión general</h4>
        <p><b>${nivelRiesgo}</b></p>
      </div>

    </div>
  `;
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
    grado,
    peso,
    talla,
    sexo,
    usa_lentes,
    ojo_izquierdo,
    ojo_derecho
  };

  resultado.innerHTML = '<strong>Consultando API...</strong><p>Espere un momento.</p>';

  try {
    const response = await fetch(API_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(payload)
    });

    if (!response.ok) {
      throw new Error('La API respondió con error');
    }

    const data = await response.json();
    mostrarResultado(data);

  } catch (error) {
    console.error(error);

    resultado.innerHTML = `
      <strong>Error al consultar la API</strong>
      <p>No se pudo obtener respuesta del servidor.</p>
      <p>Verifica que la API esté activa en Render y que el endpoint sea correcto.</p>
    `;
  }
});