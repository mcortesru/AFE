document.addEventListener("DOMContentLoaded", function () {
    let documentUploaded = false;  // Rastrea si se ha subido un archivo

    function toggleSections(showChat) {
        let chatSection = document.getElementById("chat-section");
        chatSection.style.display = showChat ? "block" : "none";
    }

    function clearChatHistory() {
        let chatBox = document.getElementById("chat-box");
        chatBox.innerHTML = "";  // 🔥 Borra todos los mensajes del chat
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
        }

        fetch('http://127.0.0.1:5000/process', {
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
                clearChatHistory();  // 🔥 Limpiar chat al subir nuevo documento
                toggleSections(true);  // Mostrar el chat
                outputElement.textContent = 'Documento cargado correctamente'; // Limpia mensaje de carga
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
        .then(response => response.json())
        .then(data => {
            let botMessage = document.createElement("div");
            botMessage.className = "message bot-message";
            botMessage.innerText = "Bot: " + data.response;
            chatBox.appendChild(botMessage);

            chatBox.scrollTop = chatBox.scrollHeight;
        })
        .catch(error => {
            console.error("Error en la solicitud:", error);
        });
    };
});
