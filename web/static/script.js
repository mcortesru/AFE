function processFile(buttonId) {
    const outputElement = document.getElementById('output');
    const formData = new FormData();
    formData.append('file', document.getElementById('file-upload').files[0]);
    formData.append('buttonId', buttonId);

    if (buttonId === 'resumen'){
        outputElement.textContent = 'Resuminedo texto...';
    } else if (buttonId === 'clasificacion'){
        outputElement.textContent = 'Clasificando texto...';
    } else if (buttonId === 'tokens'){
        outputElement.textContent = 'Obteniendo NERs del texto...';
    } else if (buttonId === 'palabras'){
        outputElement.textContent = 'Obteniendo palabras clave del texto...';
    }

    fetch('http://127.0.0.1:5000/process', {
        method: 'POST',
        body: formData,
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Respuesta de red no fue ok');
        }
        return response.text();
    })
    .then(text => {
        try {
            const data = JSON.parse(text);
            outputElement.innerHTML = data.message.replace(/\\n/g, '<br>'); // Convierte \n a <br>
        } catch (error) {
            console.error('Error al parsear JSON:', error);
            outputElement.innerHTML = 'Respuesta no es JSON válido';
        }
    })
    .catch(error => {
        console.error('Error:', error);
        outputElement.textContent = 'Error al procesar la solicitud';
    });
}
