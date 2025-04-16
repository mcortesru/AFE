document.addEventListener("DOMContentLoaded", function () {
    let documentUploaded = false;  // Rastrea si se ha subido un archivo

    document.getElementById("file-upload").addEventListener("change", function () {
        // Ocultar el chat
        document.getElementById("chat-section").style.display = "none";
        
        // Restablecer el mensaje de salida
        document.getElementById("output").textContent = "Aquí aparecerá el texto procesado.";
    });    

    function toggleSections(showChat) {
        let chatSection = document.getElementById("chat-section");
        if (showChat) {
            chatSection.style.display = "block";
        } else {
            chatSection.style.display = "none";
        }
    }

    window.processFile = function (buttonId) {
        const outputElement = document.getElementById('output');
        const fileInput = document.getElementById('file-upload');
        const file = fileInput.files[0];

        if (!file) {
            alert("Por favor, selecciona un archivo antes de procesarlo.");
            return;
        }

        const formData = new FormData();
        formData.append('file', file);
        formData.append('buttonId', buttonId);

        document.getElementById("output").style.display = "block";
        document.getElementById("chat-section").style.display = "none";

        if (buttonId === 'resumen') {
            outputElement.textContent = 'Resumiendo texto...';
        } else if (buttonId === 'clasificacion') {
            outputElement.textContent = 'Clasificando texto...';
        } else if (buttonId === 'tokens') {
            outputElement.textContent = 'Obteniendo NERs del texto...';
        } else if (buttonId === 'palabras') {
            outputElement.textContent = 'Obteniendo palabras clave del texto...';
        } else if (buttonId === 'chatbot') {
            outputElement.textContent = 'Cargando chatbot...';
            document.getElementById("chat-box").innerHTML = "";
        }

        fetch('http://127.0.0.1:5001/process', {
            method: 'POST',
            body: formData,
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Respuesta de red no fue ok');
            }
            return response.json();
        })
        .then(data => {
            if (buttonId === 'chatbot') {
                documentUploaded = true; // Se confirma que el documento fue subido
                toggleSections(true);  // Mostrar el chat
                outputElement.textContent = 'Documento cargado correctamente'; // Esto limpia el mensaje de carga
            } else {
                outputElement.innerHTML = data.message.replace(/\\n/g, '<br>');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            outputElement.textContent = 'Error al procesar la solicitud';
        });
    };

    window.sendMessage = function () {
        if (!documentUploaded) {
            alert("Sube un documento primero.");
            return;
        }
    
        let inputField = document.getElementById("chat-input");
        let message = inputField.value.trim();
        if (message === "") return;
    
        let chatBox = document.getElementById("chat-box");
    
        let userMessage = document.createElement("div");
        userMessage.className = "message user-message";
        userMessage.innerText = "Tú: " + message;
        chatBox.appendChild(userMessage);
    
        inputField.value = "";
    
        fetch("/chat", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ message: message })
        })
        .then(async response => {
            console.log("🛑 Respuesta completa del servidor:", response);
            let data;
            try {
                data = await response.json();
            } catch (error) {
                console.error("🛑 Error convirtiendo la respuesta a JSON:", error);
                return;
            }
    
            console.log("🛑 JSON recibido:", data);
            if (data.error) {
                alert("Error: " + data.error);
                return;
            }
    
            let botMessage = document.createElement("div");
            botMessage.className = "message bot-message";
            botMessage.innerText = "Bot: " + data.response;
            chatBox.appendChild(botMessage);
    
            chatBox.scrollTop = chatBox.scrollHeight;
        })
        .catch(error => {
            console.error("🛑 Error en la solicitud:", error);
        });
    };    
});
