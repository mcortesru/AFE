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
    
        if (!file && buttonId === 'chatbot') {
            alert("Por favor, selecciona un archivo antes de procesarlo.");
            return;
        }
    
        const formData = new FormData();
        formData.append('buttonId', buttonId);
        if (file && buttonId !== 'chatbot-general') {
            formData.append('file', file);
        }
    
        const thresholdInput = document.getElementById("ner-threshold");
        const threshold = thresholdInput ? thresholdInput.value || "0.99" : "0.99";

        console.log("Nivel de confianza: " + threshold);

        if (buttonId === 'tokens') {
            formData.append('threshold', threshold);
        }
    
        const output = document.getElementById("output");
        output.style.display = "block";
        output.textContent = "";
    
        if (buttonId === 'chatbot' || buttonId === 'chatbot-general' || buttonId === 'chatbot-final') {
            documentUploaded = true;
            document.getElementById("chat-box").innerHTML = "";
            toggleSections(true);
            if (buttonId === 'chatbot') {
                sessionStorage.setItem("chatMode", "individual");
            } else if (buttonId === 'chatbot-general') {
                sessionStorage.setItem("chatMode", "general");
            } else if (buttonId === 'chatbot-final') {
                sessionStorage.setItem("chatMode", "final");
            }

    
            if (buttonId === 'chatbot') {
                output.textContent = 'Chatbot individual cargado correctamente. Ya puedes hacer preguntas.';
            } else if (buttonId === 'chatbot-general') {
                output.textContent = 'Chatbot general activado. Escribe tu pregunta abajo.';
            } else if (buttonId === 'chatbot-final') {
                output.textContent = 'Chatbot final activado. Pregunta lo que quieras.';
            }

    
            // ✅ NO ejecutar el fetch si es chatbot-general o chatbot final
            if (buttonId === 'chatbot-general' || buttonId === 'chatbot-final') return;
        } else {
            toggleSections(false);
            sessionStorage.removeItem("chatMode");
    
            if (buttonId === 'resumen') output.textContent = 'Resumiendo texto...';
            else if (buttonId === 'clasificacion') output.textContent = 'Clasificando texto...';
            else if (buttonId === 'tokens') output.textContent = 'Obteniendo NERs del texto con una confianza de ' + threshold + '...';
            else if (buttonId === 'palabras') output.textContent = 'Obteniendo palabras clave del texto...';
            else if (buttonId === 'entidades') output.textContent = 'Extrayendo entidades nombradas del texto...';

        }
    
        // 🔄 Solo se ejecuta fetch si no es chatbot-general
        fetch('http://127.0.0.1:5003/process', {
            method: 'POST',
            body: formData,
        })
        .then(response => {
            if (!response.ok) throw new Error('Respuesta de red no fue ok');
            return response.json();
        })
        .then(data => {
            if (buttonId === 'entidades') {
                output.textContent = 'Procesando entidades...';
                setTimeout(() => {
                    output.innerHTML = data.message.replace(/\\n/g, '<br>');
                }, 7000);
            } if (buttonId !== 'chatbot') {
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

        let endpoint;
        if (mode === "general") {
            endpoint = "/chat-general";
        } else if (mode === "final") {
            endpoint = "/chat-final";
        } else {
            endpoint = "/chat";
        }


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
