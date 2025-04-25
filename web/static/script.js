document.addEventListener("DOMContentLoaded", function () {
    let documentUploaded = false;

    document.getElementById("file-upload").addEventListener("change", function () {
        document.getElementById("chat-section").style.display = "none";
        document.getElementById("chat-box").innerHTML = "";
        document.getElementById("output").textContent = "Aquí aparecerá el texto procesado.";
        sessionStorage.removeItem("chatMode");
    });

    function toggleSections(showChat) {
        document.getElementById("chat-section").style.display = showChat ? "block" : "none";
    }

    window.processFile = function (buttonId) {
        const fileInput = document.getElementById("file-upload");
        const file = fileInput.files[0];
    
        if (!file && buttonId !== 'chatbot-general') {
            alert("Por favor, selecciona un archivo antes de procesarlo.");
            return;
        }
    
        const formData = new FormData();
        formData.append('buttonId', buttonId);
        if (file && buttonId !== 'chatbot-general') {
            formData.append('file', file);
        }
    
        const threshold = document.getElementById("ner-threshold").value || "0.99";
        console.log("Nivel de confianza: " + threshold);

        if (buttonId === 'tokens') {
            formData.append('threshold', threshold);
        }
    
        const output = document.getElementById("output");
        output.style.display = "block";
        output.textContent = "";
    
        if (buttonId === 'chatbot' || buttonId === 'chatbot-general') {
            documentUploaded = true;
            document.getElementById("chat-box").innerHTML = "";
            toggleSections(true);
            sessionStorage.setItem("chatMode", buttonId === 'chatbot' ? "individual" : "general");
    
            output.textContent = buttonId === 'chatbot'
                ? 'Chatbot individual cargado correctamente. Ya puedes hacer preguntas.'
                : 'Chatbot general activado. Escribe tu pregunta abajo.';
    
            // ✅ NO ejecutar el fetch si es chatbot-general
            if (buttonId === 'chatbot-general') return;
        } else {
            toggleSections(false);
            sessionStorage.removeItem("chatMode");
    
            if (buttonId === 'resumen') output.textContent = 'Resumiendo texto...';
            else if (buttonId === 'clasificacion') output.textContent = 'Clasificando texto...';
            else if (buttonId === 'tokens') output.textContent = 'Obteniendo NERs del texto con una confianza de ' + threshold + '...';
            else if (buttonId === 'palabras') output.textContent = 'Obteniendo palabras clave del texto...';
        }
    
        // 🔄 Solo se ejecuta fetch si no es chatbot-general
        fetch('http://127.0.0.1:5002/process', {
            method: 'POST',
            body: formData,
        })
        .then(response => {
            if (!response.ok) throw new Error('Respuesta de red no fue ok');
            return response.json();
        })
        .then(data => {
            if (buttonId !== 'chatbot') {
                output.innerHTML = data.message.replace(/\\n/g, '<br>');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            output.textContent = 'Error al procesar la solicitud';
        });
    };
    

    window.sendMessage = function () {
        const mode = sessionStorage.getItem("chatMode");
        if (mode === "individual" && !documentUploaded) {
            alert("Sube un documento primero.");
            return;
        }

        const inputField = document.getElementById("chat-input");
        const message = inputField.value.trim();
        if (message === "") return;

        const chatBox = document.getElementById("chat-box");

        const userMessage = document.createElement("div");
        userMessage.className = "message user-message";
        userMessage.innerText = "Tú: " + message;
        chatBox.appendChild(userMessage);
        inputField.value = "";

        const endpoint = mode === "general" ? "/chat-general" : "/chat";

        fetch(endpoint, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ message: message })
        })
        .then(async response => {
            const data = await response.json();
            if (data.error) {
                alert("Error: " + data.error);
                return;
            }

            const botMessage = document.createElement("div");
            botMessage.className = "message bot-message";
            botMessage.innerText = mode === "general" ? data.response : "Bot: " + data.response;

            chatBox.appendChild(botMessage);
            chatBox.scrollTop = chatBox.scrollHeight;
        })
        .catch(error => {
            console.error("Error en la solicitud:", error);
        });
    };
});
