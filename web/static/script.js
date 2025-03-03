document.addEventListener("DOMContentLoaded", function () {
    function toggleSections(showChat) {
        if (showChat) {
            document.getElementById("output").style.display = "none";
            document.getElementById("chat-section").style.display = "block";
        } else {
            document.getElementById("output").style.display = "block";
            document.getElementById("chat-section").style.display = "none";
        }
    }

    window.showChat = function () {
        toggleSections(true);
    };

    window.sendMessage = function () {
        const chatBox = document.getElementById("chat-box");
        const chatInput = document.getElementById("chat-input");
    
        if (chatInput.value.trim() !== "") {
            const userMessage = document.createElement("p");
            userMessage.classList.add("user-message");
            userMessage.textContent = chatInput.value;
            chatBox.appendChild(userMessage);
    
            fetch("/chatbot", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ pregunta: chatInput.value })
            })
            .then(response => response.json())
            .then(data => {
                const botMessage = document.createElement("p");
                botMessage.classList.add("bot-message");
                botMessage.textContent = data.respuesta;
                chatBox.appendChild(botMessage);
            });
    
            chatInput.value = "";
            chatBox.scrollTop = chatBox.scrollHeight;
        }
    };
});



function processFile(buttonId) {
    const outputElement = document.getElementById('output');
    const formData = new FormData();
    formData.append('file', document.getElementById('file-upload').files[0]);
    formData.append('buttonId', buttonId);

    document.getElementById("output").style.display = "block";
    document.getElementById("chat-section").style.display = "none";

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
