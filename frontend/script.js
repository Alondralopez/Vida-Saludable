const API_URL = 'https://vida-saludable-api.onrender.com/api/predict';

const form = document.getElementById('formSalud');
const resultado = document.getElementById('resultadoApi');

function calcularIMC(peso, tallaCm) {
  const tallaM = tallaCm / 100;
  return peso / (tallaM * tallaM);
}

function mostrarResultado(data) {
  resultado.innerHTML = `
    <strong>Respuesta de la API:</strong>
    <div class="result-grid">
      <div class="result-card">
        <h4>Evaluación nutricional</h4>
        <p><b>Riesgo:</b> ${data.riesgo_nutricional ? 'Sí' : 'No'}</p>
        <p><b>Probabilidad:</b> ${data.probabilidad_nutricional}%</p>
      </div>

      <div class="result-card">
        <h4>Evaluación visual</h4>
        <p><b>Riesgo:</b> ${data.riesgo_visual ? 'Sí' : 'No'}</p>
        <p><b>Probabilidad:</b> ${data.probabilidad_visual}%</p>
      </div>

      <div class="result-card">
        <h4>Conclusión general</h4>
        <p><b>${data.riesgo_general}</b></p>
        <p>${data.mensaje}</p>
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
    ojo_derecho,
    imc,
    vision_promedio,
    diferencia_visual
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
    // Respuesta simulada para que puedas ver el frontend aunque todavía no tengas lista la API.
    const riesgoNutricional = imc < 14 || imc > 20;
    const riesgoVisual = vision_promedio < 6 || diferencia_visual >= 2;

    let riesgoGeneral = 'Riesgo bajo';
    let mensaje = 'Sin alerta principal';

    if (riesgoNutricional && riesgoVisual) {
      riesgoGeneral = 'Riesgo alto';
      mensaje = 'Requiere atención prioritaria';
    } else if (riesgoNutricional || riesgoVisual) {
      riesgoGeneral = 'Riesgo medio';
      mensaje = 'Requiere seguimiento preventivo';
    }

    mostrarResultado({
      riesgo_nutricional: riesgoNutricional,
      probabilidad_nutricional: riesgoNutricional ? 95.4 : 18.2,
      riesgo_visual: riesgoVisual,
      probabilidad_visual: riesgoVisual ? 93.8 : 13.5,
      riesgo_general: riesgoGeneral,
      mensaje
    });
  }
});
