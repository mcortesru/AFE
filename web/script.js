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
        outputElement.textContent = 'Obteniendo tokens del texto...';
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
            outputElement.innerHTML = '<pre>' + data.message + '</pre>';
        } catch (error) {
            console.error('Error al parsear JSON:', error);
            outputElement.innerHTML = '<pre>Respuesta no es JSON válido</pre>';
        }
    })
    .catch(error => {
        console.error('Error:', error);
        outputElement.textContent = 'Error al procesar la solicitud';
    });
}
