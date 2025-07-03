const locationCategoryLabels = {
    em: "Emisión",
    re: "Recepción",
    ot: "Otro"
};

const personTypeLabels = {
    pe: "Persona natural",
    ej: "Entidad jurídica"
};

const personCategoryLabels = {
    au: "Autor",
    de: "Destinatario",
    ot: "Otro"
};



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

        // Oculta la vista de información completa si está activa
        document.getElementById("informacion-completa").style.display = "none";

    
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
        userMessage.innerText = message;
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

            let formattedResponse = data.response;
            console.log("RESPUESTA OBTENIDA:")
            console.log(formattedResponse)
            
            //FORMATEO DE LA RESPUESTA
            formattedResponse = formattedResponse.replace(/\[Documentos usados:\s*\[[^\]]*\]\]/g, match => {
                return `<span class="docs-used" style="display:none;color:#555">${match}</span>`;
            });

            formattedResponse = formattedResponse
                .replace(/===\s*(.+?)\s*===/g, "<b>$1</b>")
                .replace(/\n/g, "<br>")
                .replace(/<\/b>/g, "</b>");

            const botMessage = document.createElement("div");
            botMessage.className = "message bot-message";
            botMessage.innerHTML = formattedResponse

            const toggleButton = document.createElement("button");
            toggleButton.textContent = "Mostrar/ocultar documentos usados";
            toggleButton.style.display = "block";
            toggleButton.style.marginTop = "10px";
            toggleButton.onclick = () => {
                const docsUsedElements = botMessage.querySelectorAll(".docs-used");
                docsUsedElements.forEach(elem => {
                    elem.style.display = elem.style.display === "none" ? "inline" : "none";
                });
            };

            chatBox.appendChild(botMessage);
            chatBox.appendChild(toggleButton);
            chatBox.scrollTop = chatBox.scrollHeight;
        })
        .catch(error => {
            console.error("Error en la solicitud:", error);
        });
    };


    window.verTodaLaInformacion = function () {
    fetch('/ver-informacion-completa')
        .then(response => {
            if (!response.ok) throw new Error("Error al obtener la información");
            return response.json();
        })
        .then(data => {
            const container = document.getElementById("accordion-container");
            container.innerHTML = "";

            data.documentos.forEach((doc, i) => {
                const section = document.createElement("div");
                section.classList.add("accordion-item");

                const header = document.createElement("button");
                header.classList.add("accordion-toggle");
                header.textContent = `${doc.file_name} – ${doc.title}`;

                const content = document.createElement("div");
                content.classList.add("accordion-content");
                content.style.display = "none";
                header.onclick = () => {
                    content.style.display = content.style.display === "none" ? "block" : "none";
                };

                // === PERSONAS ===
                let personasHTML = "";

                // Autores (solo personas físicas)
                const autores = doc.people.filter(p => p.category === "au" && p.person_type === "pe");
                if (autores.length) {
                    personasHTML += `<p><strong>Autores:</strong></p><ul>`;
                    personasHTML += autores.map(p => {
                        const nombre = [p.name, p.surname1, p.surname2].filter(Boolean).join(" ") || "(sin nombre)";
                        const rol = p.role ? ` – ${p.role}` : "";
                        return `<li>${nombre}${rol}</li>`;
                    }).join("");
                    personasHTML += `</ul>`;
                }

                // Destinatarios (solo personas físicas)
                const destinatarios = doc.people.filter(p => p.category === "de" && p.person_type === "pe");
                if (destinatarios.length) {
                    personasHTML += `<p><strong>Destinatarios:</strong></p><ul>`;
                    personasHTML += destinatarios.map(p => {
                        const nombre = [p.name, p.surname1, p.surname2].filter(Boolean).join(" ") || "(sin nombre)";
                        const rol = p.role ? ` – ${p.role}` : "";
                        return `<li>${nombre}${rol}</li>`;
                    }).join("");
                    personasHTML += `</ul>`;
                }

                // Otras personas físicas
                const otrasPersonas = doc.people.filter(p => p.category === "ot" && p.person_type === "pe");
                if (otrasPersonas.length) {
                    personasHTML += `<p><strong>Resto de personas:</strong></p><ul>`;
                    personasHTML += otrasPersonas.map(p => {
                        const nombre = [p.name, p.surname1, p.surname2].filter(Boolean).join(" ") || "(sin nombre)";
                        const rol = p.role ? ` – ${p.role}` : "";
                        return `<li>${nombre}${rol}</li>`;
                    }).join("");
                    personasHTML += `</ul>`;
                }

                // Organizaciones (entidades jurídicas)
                const organizaciones = doc.people.filter(p => p.person_type === "ej");
                if (organizaciones.length) {
                    personasHTML += `<p><strong>Organizaciones:</strong></p><ul>`;
                    personasHTML += organizaciones.map(p => {
                        const nombre = p.name || "(sin nombre)";
                        const rol = p.role ? ` – ${p.role}` : "";
                        return `<li>${nombre}${rol}</li>`;
                    }).join("");
                    personasHTML += `</ul>`;
                }

                // === LUGARES ===
                const lugaresHTML = `
                    <p><strong>Lugares:</strong></p>
                    <ul>
                        ${doc.locations.map(l => {
                            const label = locationCategoryLabels[l.category] || l.category;
                            return `<li>${l.name} (${label})</li>`;
                        }).join("")}
                    </ul>`;

                // === CONTENIDO FINAL ===
                content.innerHTML = `
                    <p><strong>Resumen:</strong> ${doc.summary}</p>
                    <p><strong>Tipo:</strong> ${doc.document_type}</p>
                    <p><strong>Localización:</strong> Caja: ${doc.box} | Carpeta: ${doc.folder}</p>
                    ${personasHTML}
                    ${lugaresHTML}
                `;

                section.appendChild(header);
                section.appendChild(content);
                container.appendChild(section);
            });

            document.getElementById("informacion-completa").style.display = "block";
            document.getElementById("output").style.display = "none";
            document.getElementById("chat-section").style.display = "none";
        })
        .catch(error => {
            console.error("Error:", error);
            alert("No se pudo cargar la información");
        });
    };
});
