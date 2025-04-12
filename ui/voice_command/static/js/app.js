/**
 * Application JavaScript pour le module de commande vocale
 * Le Vieux Moulin - Système de gestion intelligente
 */

// Variables globales
let socket;
let sounds = {};
let currentCommand = {};
let isListening = false;
let isConnected = true;

/**
 * Initialise l'application
 */
function initApp() {
    initSocketIO();
    loadSounds();
    setupUserActivityMonitoring();
    
    // Notification initiale
    updateStatus('Système prêt');
}

/**
 * Initialise la connexion Socket.IO
 */
function initSocketIO() {
    // Connexion au serveur WebSocket
    socket = io();
    
    // Événement de connexion
    socket.on('connect', function() {
        console.log('Connexion WebSocket établie');
        isConnected = true;
        updateStatus('Connecté au serveur');
    });
    
    // Événement de déconnexion
    socket.on('disconnect', function() {
        console.log('Connexion WebSocket perdue');
        isConnected = false;
        updateStatus('Connexion perdue', 'error');
        stopListening();
    });
    
    // Mise à jour de statut
    socket.on('status_update', function(data) {
        updateStatus(data.status);
    });
    
    // Texte reconnu
    socket.on('speech_recognized', function(data) {
        displayRecognizedText(data.text, data.confidence);
    });
    
    // Commande identifiée
    socket.on('command_identified', function(data) {
        displayCommand(data);
    });
    
    // Résultat de commande
    socket.on('command_result', function(data) {
        displayCommandResult(data);
    });
    
    // Demande de confirmation
    socket.on('request_confirmation', function(data) {
        requestConfirmation(data);
    });
    
    // Affichage d'erreur
    socket.on('show_error', function(data) {
        showError(data.title, data.message);
    });
    
    // Mise à jour de l'historique
    socket.on('history_updated', function(data) {
        if (window.location.pathname === '/history') {
            updateHistory(data.history);
        }
    });
    
    // Jouer un son
    socket.on('play_sound', function(data) {
        playSound(data.sound);
    });
    
    // Gestion de la veille de l'écran
    socket.on('screen_sleep', function() {
        document.body.classList.add('screen-sleep');
        document.body.classList.remove('screen-wake');
    });
    
    socket.on('screen_wake', function() {
        document.body.classList.remove('screen-sleep');
        document.body.classList.add('screen-wake');
    });
}

/**
 * Charge les sons utilisés par l'application
 */
function loadSounds() {
    sounds = {
        speech_recognized: new Howl({
            src: ['/static/sounds/speech_recognized.mp3'],
            volume: 0.5
        }),
        command_identified: new Howl({
            src: ['/static/sounds/command_identified.mp3'],
            volume: 0.5
        }),
        command_success: new Howl({
            src: ['/static/sounds/command_success.mp3'],
            volume: 0.5
        }),
        confirmation_needed: new Howl({
            src: ['/static/sounds/confirmation_needed.mp3'],
            volume: 0.5
        }),
        error: new Howl({
            src: ['/static/sounds/error.mp3'],
            volume: 0.5
        })
    };
}

/**
 * Configure la surveillance d'activité utilisateur
 */
function setupUserActivityMonitoring() {
    // Liste des événements à surveiller
    const events = ['mousedown', 'touchstart', 'keydown', 'scroll'];
    
    // Ajouter les écouteurs d'événements
    events.forEach(event => {
        document.addEventListener(event, notifyUserActivity);
    });
    
    // Fonction de notification
    function notifyUserActivity() {
        socket.emit('user_activity');
    }
    
    // Notification initiale
    notifyUserActivity();
    
    // Notification périodique si la page est active
    setInterval(() => {
        if (document.visibilityState === 'visible') {
            notifyUserActivity();
        }
    }, 60000); // Chaque minute
}

/**
 * Met à jour le statut affiché
 * @param {string} message - Message de statut
 * @param {string} type - Type de statut (info, success, warning, error)
 */
function updateStatus(message, type = 'info') {
    const statusElement = document.getElementById('status');
    if (!statusElement) return;
    
    // Nettoyer les classes existantes
    statusElement.className = 'alert';
    
    // Ajouter la classe appropriée
    switch (type) {
        case 'success':
            statusElement.classList.add('alert-success');
            break;
        case 'warning':
            statusElement.classList.add('alert-warning');
            break;
        case 'error':
            statusElement.classList.add('alert-danger');
            break;
        default:
            statusElement.classList.add('alert-info');
    }
    
    // Mettre à jour le texte
    statusElement.textContent = message;
    
    // Animation
    statusElement.classList.add('highlight');
    setTimeout(() => {
        statusElement.classList.remove('highlight');
    }, 1500);
}

/**
 * Affiche le texte reconnu
 * @param {string} text - Texte reconnu
 * @param {number} confidence - Indice de confiance (0-100)
 */
function displayRecognizedText(text, confidence) {
    const textElement = document.getElementById('recognizedText');
    const confidenceBar = document.getElementById('confidenceBar');
    const confidenceText = document.getElementById('confidenceText');
    
    if (!textElement || !confidenceBar || !confidenceText) return;
    
    // Mettre à jour le texte
    textElement.textContent = text;
    textElement.classList.add('active');
    
    // Mettre à jour la barre de confiance
    confidenceBar.style.width = `${confidence}%`;
    confidenceBar.textContent = `${confidence}%`;
    confidenceText.textContent = `Confiance: ${confidence}%`;
    
    // Couleur selon le niveau de confiance
    if (confidence > 80) {
        confidenceBar.className = 'progress-bar bg-success';
    } else if (confidence > 50) {
        confidenceBar.className = 'progress-bar bg-info';
    } else if (confidence > 30) {
        confidenceBar.className = 'progress-bar bg-warning';
    } else {
        confidenceBar.className = 'progress-bar bg-danger';
    }
    
    // Réinitialiser l'état actif après un délai
    setTimeout(() => {
        textElement.classList.remove('active');
    }, 2000);
}

/**
 * Affiche une commande identifiée
 * @param {Object} data - Données de la commande
 */
function displayCommand(data) {
    const commandDisplay = document.getElementById('commandDisplay');
    if (!commandDisplay) return;
    
    // Stocker la commande courante
    currentCommand = data;
    
    // Formater l'affichage
    let content = '';
    content += `<div class="command-type"><strong>${data.display_category}</strong> › ${data.display_name}</div>`;
    
    if (Object.keys(data.params).length > 0) {
        content += '<div class="command-params mt-2"><small>';
        for (const [key, value] of Object.entries(data.params)) {
            content += `<span class="badge bg-light text-dark me-1">${key}: ${value}</span>`;
        }
        content += '</small></div>';
    }
    
    // Mettre à jour l'affichage
    commandDisplay.innerHTML = content;
    commandDisplay.classList.add('highlight');
    
    // Masquer le résultat précédent
    const resultElement = document.getElementById('commandResult');
    if (resultElement) {
        resultElement.classList.add('d-none');
    }
}

/**
 * Affiche le résultat d'une commande
 * @param {Object} data - Données du résultat
 */
function displayCommandResult(data) {
    const resultElement = document.getElementById('commandResult');
    if (!resultElement) return;
    
    // Formater le contenu selon le type de résultat
    let content = '';
    
    // Vérifier le type de résultat
    if (data.result && typeof data.result === 'object') {
        // Résultat complexe (objet)
        if (data.command.startsWith('stock.')) {
            // Résultat de stock
            const stockInfo = data.result;
            content = formatStockResult(stockInfo);
        } else if (data.command.startsWith('equipment.')) {
            // Résultat d'équipement
            const equipmentInfo = data.result;
            content = formatEquipmentResult(equipmentInfo);
        } else if (data.command.startsWith('recipe.')) {
            // Résultat de recette
            content = formatRecipeResult(data.result);
        } else {
            // Format générique pour d'autres types
            content = `<div class="result-generic">${JSON.stringify(data.result, null, 2)}</div>`;
        }
    } else {
        // Résultat simple (texte)
        content = `<div class="result-message">${data.result || 'Commande exécutée avec succès'}</div>`;
    }
    
    // Mettre à jour et afficher
    resultElement.innerHTML = content;
    resultElement.classList.remove('d-none');
    resultElement.classList.add('highlight');
}

/**
 * Formate le résultat d'une vérification de stock
 * @param {Object} stockInfo - Informations de stock
 * @returns {string} HTML formaté
 */
function formatStockResult(stockInfo) {
    if (!stockInfo) return '<div class="text-muted">Aucune information disponible</div>';
    
    let html = '<div class="stock-result">';
    
    if (stockInfo.current !== undefined) {
        const level = (stockInfo.current / stockInfo.max) * 100;
        let statusClass = 'success';
        
        if (level < 20) {
            statusClass = 'danger';
        } else if (level < 50) {
            statusClass = 'warning';
        }
        
        html += `
            <div class="mb-2">Niveau actuel: <strong>${stockInfo.current} ${stockInfo.unit}</strong></div>
            <div class="progress mb-2">
                <div class="progress-bar bg-${statusClass}" role="progressbar" 
                    style="width: ${level}%" aria-valuenow="${level}" 
                    aria-valuemin="0" aria-valuemax="100">
                    ${Math.round(level)}%
                </div>
            </div>
            <div class="small text-muted">Capacité max: ${stockInfo.max} ${stockInfo.unit}</div>
        `;
        
        if (stockInfo.last_updated) {
            const date = new Date(stockInfo.last_updated * 1000).toLocaleString();
            html += `<div class="small text-muted mt-1">Dernière mise à jour: ${date}</div>`;
        }
    } else {
        html += '<div class="text-muted">Données de stock non disponibles</div>';
    }
    
    html += '</div>';
    return html;
}

/**
 * Formate le résultat d'une vérification d'équipement
 * @param {Object} equipmentInfo - Informations d'équipement
 * @returns {string} HTML formaté
 */
function formatEquipmentResult(equipmentInfo) {
    if (!equipmentInfo) return '<div class="text-muted">Aucune information disponible</div>';
    
    let html = '<div class="equipment-result">';
    
    if (equipmentInfo.status) {
        let statusClass = '';
        let statusText = '';
        
        switch (equipmentInfo.status.toLowerCase()) {
            case 'ok':
            case 'operational':
            case 'ready':
                statusClass = 'success';
                statusText = 'Opérationnel';
                break;
            case 'warning':
            case 'maintenance':
                statusClass = 'warning';
                statusText = 'Maintenance recommandée';
                break;
            case 'error':
            case 'failure':
                statusClass = 'danger';
                statusText = 'Défaillance détectée';
                break;
            default:
                statusClass = 'info';
                statusText = equipmentInfo.status;
        }
        
        html += `<div class="alert alert-${statusClass} mb-3">${statusText}</div>`;
        
        if (equipmentInfo.temperature !== undefined) {
            html += `<div>Température: <strong>${equipmentInfo.temperature}°C</strong></div>`;
        }
        
        if (equipmentInfo.details) {
            html += '<div class="mt-2"><strong>Détails:</strong></div>';
            html += '<ul>';
            for (const [key, value] of Object.entries(equipmentInfo.details)) {
                html += `<li>${key}: ${value}</li>`;
            }
            html += '</ul>';
        }
    } else {
        html += '<div class="text-muted">État de l\'équipement non disponible</div>';
    }
    
    html += '</div>';
    return html;
}

/**
 * Formate le résultat d'une recherche de recette
 * @param {Object} recipeInfo - Informations de recette
 * @returns {string} HTML formaté
 */
function formatRecipeResult(recipeInfo) {
    if (!recipeInfo) return '<div class="text-muted">Aucune information disponible</div>';
    
    let html = '<div class="recipe-result">';
    
    if (recipeInfo.name) {
        html += `<h5>${recipeInfo.name}</h5>`;
        
        if (recipeInfo.ingredients && recipeInfo.ingredients.length > 0) {
            html += '<div class="mt-2"><strong>Ingrédients:</strong></div>';
            html += '<ul class="ingredients-list">';
            recipeInfo.ingredients.forEach(ing => {
                let text = ing.name;
                if (ing.quantity) {
                    text += ` (${ing.quantity}${ing.unit ? ' ' + ing.unit : ''})`;
                }
                html += `<li>${text}</li>`;
            });
            html += '</ul>';
        }
        
        if (recipeInfo.instructions && recipeInfo.instructions.length > 0) {
            html += '<div class="mt-2"><strong>Instructions:</strong></div>';
            html += '<ol class="instructions-list">';
            recipeInfo.instructions.forEach(step => {
                html += `<li>${step}</li>`;
            });
            html += '</ol>';
        }
    } else {
        html += '<div class="text-muted">Recette non disponible</div>';
    }
    
    html += '</div>';
    return html;
}

/**
 * Demande une confirmation pour exécuter une commande
 * @param {Object} data - Données de la commande
 */
function requestConfirmation(data) {
    // Stocker la commande courante
    currentCommand = data;
    
    // Préparer le contenu de confirmation
    const confirmationElement = document.getElementById('confirmationCommand');
    if (confirmationElement) {
        let content = `<div class="command-type"><strong>${data.display_category}</strong> › ${data.display_name}</div>`;
        
        if (Object.keys(data.params).length > 0) {
            content += '<div class="command-params mt-2">';
            for (const [key, value] of Object.entries(data.params)) {
                content += `<span class="badge bg-light text-dark me-1">${key}: ${value}</span>`;
            }
            content += '</div>';
        }
        
        confirmationElement.innerHTML = content;
    }
    
    // Afficher la modale
    const modal = new bootstrap.Modal(document.getElementById('confirmationModal'));
    modal.show();
}

/**
 * Affiche une erreur
 * @param {string} title - Titre de l'erreur
 * @param {string} message - Message d'erreur
 */
function showError(title, message) {
    // Créer une alerte temporaire
    const alertElement = document.createElement('div');
    alertElement.className = 'alert alert-danger alert-dismissible fade show position-fixed top-0 start-50 translate-middle-x mt-3';
    alertElement.innerHTML = `
        <strong>${title}</strong><br>
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    // Ajouter au document
    document.body.appendChild(alertElement);
    
    // Supprimer après un délai
    setTimeout(() => {
        if (alertElement.parentNode) {
            const bsAlert = new bootstrap.Alert(alertElement);
            bsAlert.close();
        }
    }, 5000);
}

/**
 * Joue un son
 * @param {string} soundName - Nom du son à jouer
 */
function playSound(soundName) {
    if (sounds[soundName]) {
        sounds[soundName].play();
    }
}

/**
 * Démarre l'écoute vocale
 */
function startListening() {
    if (isListening) return;
    
    const listenButton = document.getElementById('listenButton');
    if (listenButton) {
        listenButton.classList.remove('btn-success');
        listenButton.classList.add('btn-danger', 'pulse');
        listenButton.querySelector('i').classList.remove('bi-mic-fill');
        listenButton.querySelector('i').classList.add('bi-mic-mute-fill');
    }
    
    socket.emit('start_listening');
    isListening = true;
    updateStatus('Écoute en cours...', 'info');
}

/**
 * Arrête l'écoute vocale
 */
function stopListening() {
    if (!isListening) return;
    
    const listenButton = document.getElementById('listenButton');
    if (listenButton) {
        listenButton.classList.remove('btn-danger', 'pulse');
        listenButton.classList.add('btn-success');
        listenButton.querySelector('i').classList.remove('bi-mic-mute-fill');
        listenButton.querySelector('i').classList.add('bi-mic-fill');
    }
    
    socket.emit('stop_listening');
    isListening = false;
    updateStatus('Écoute arrêtée', 'info');
}

/**
 * Met à jour l'affichage de l'historique
 * @param {Array} history - Historique des commandes
 */
function updateHistory(history) {
    const historyElement = document.getElementById('historyList');
    if (!historyElement) return;
    
    let html = '';
    if (history.length === 0) {
        html = '<div class="text-center text-muted py-4">Aucune commande dans l\'historique</div>';
    } else {
        html = '<div class="list-group">';
        
        // Trier par horodatage décroissant
        const sortedHistory = [...history].sort((a, b) => b.timestamp - a.timestamp);
        
        sortedHistory.forEach(entry => {
            const time = new Date(entry.timestamp * 1000).toLocaleString();
            let statusClass = 'text-success';
            let statusIcon = 'bi-check-circle-fill';
            
            if (entry.status === 'error') {
                statusClass = 'text-danger';
                statusIcon = 'bi-x-circle-fill';
            } else if (entry.status === 'pending') {
                statusClass = 'text-warning';
                statusIcon = 'bi-hourglass-split';
            }
            
            html += `
                <div class="list-group-item">
                    <div class="d-flex justify-content-between align-items-center">
                        <h6 class="mb-1">${entry.command}</h6>
                        <small class="${statusClass}">
                            <i class="bi ${statusIcon}"></i>
                        </small>
                    </div>
                    <div class="small text-muted">${time}</div>
                    <div class="mt-2">
                        <small>Paramètres: ${JSON.stringify(entry.params)}</small>
                    </div>
                </div>
            `;
        });
        
        html += '</div>';
    }
    
    historyElement.innerHTML = html;
}
