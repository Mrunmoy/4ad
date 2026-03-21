/**
 * Four Against Darkness - Web Client
 */

// Game state
const state = {
    gameId: null,
    playerId: null,
    playerName: null,
    socket: null,
    gameData: null,
    selectedTarget: 0,
    clientErrors: [],
};

// DOM Elements
const screens = {
    lobby: document.getElementById('lobby'),
    setup: document.getElementById('setup'),
    game: document.getElementById('game'),
};

// Initialize
function init() {
    setupEventListeners();
    setupSocket();

    // If loaded via /game/<game_id>, auto-fill the join form
    const pathMatch = window.location && window.location.pathname
        ? window.location.pathname.match(/^\/game\/([^/]+)$/)
        : null;
    if (pathMatch && pathMatch[1]) {
        document.getElementById('join-game-id').value = pathMatch[1];
        document.getElementById('player-name').focus();
    }
}

function setupEventListeners() {
    // Lobby
    document.getElementById('create-game').addEventListener('click', createGame);
    document.getElementById('join-game').addEventListener('click', joinGame);
    
    // Setup
    document.getElementById('create-char').addEventListener('click', createCharacter);
    document.getElementById('start-game').addEventListener('click', startGame);
    
    // Game
    document.querySelectorAll('.dir-btn').forEach(btn => {
        btn.addEventListener('click', () => move(btn.dataset.dir));
    });
    document.getElementById('search-btn').addEventListener('click', searchRoom);
    document.getElementById('attack-btn').addEventListener('click', attack);
}

function setupSocket() {
    state.socket = io();
    
    state.socket.on('connect', () => {
        console.log('Connected to server');
    });
    
    state.socket.on('joined', (data) => {
        console.log('Joined game room:', data.game_id);
    });
    
    state.socket.on('character_created', (data) => {
        updatePlayerList();
    });
    
    state.socket.on('game_started', (data) => {
        state.gameData = data;
        showScreen('game');
        updateGameView();
    });
    
    state.socket.on('game_update', (data) => {
        state.gameData = data;
        updateGameView();
    });
    
    state.socket.on('combat_result', (data) => {
        showCombatResult(data);
    });
    
    state.socket.on('search_result', (data) => {
        showSearchResult(data);
    });
    
    state.socket.on('move_failed', (data) => {
        showMessage(data.message, 'error');
    });
}

// Screen Management
function showScreen(screenName) {
    // Clear client errors on screen transitions (lobby→setup→game)
    state.clientErrors = [];
    Object.values(screens).forEach(s => s.classList.remove('active'));
    screens[screenName].classList.add('active');
}

// API Calls
async function createGame() {
    try {
        const response = await fetch('/api/game/create', { method: 'POST' });
        const data = await response.json();
        state.gameId = data.game_id;
        
        // Auto-join as host player
        const playerName = document.getElementById('player-name').value.trim() || 'Host';
        const joinResponse = await fetch(`/api/game/${state.gameId}/join`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ player_name: playerName }),
        });
        const joinData = await joinResponse.json();
        if (!joinResponse.ok || joinData.error) {
            showMessage(`Failed to join game: ${joinData.error || joinResponse.statusText}`, 'error');
            return;
        }
        state.playerId = joinData.player_id;
        state.playerName = playerName;
        
        document.getElementById('game-id-display').textContent = state.gameId;
        showScreen('setup');
        
        // Show character creation
        document.getElementById('character-creation').classList.remove('hidden');
        
        // Join socket room
        state.socket.emit('join_game', { game_id: state.gameId });
        
        updatePlayerList();
        
    } catch (error) {
        showMessage('Failed to create game', 'error');
    }
}

async function joinGame() {
    const gameId = document.getElementById('join-game-id').value.trim();
    const playerName = document.getElementById('player-name').value.trim();
    
    if (!gameId || !playerName) {
        showMessage('Please enter game ID and your name', 'error');
        return;
    }
    
    try {
        const response = await fetch(`/api/game/${gameId}/join`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ player_name: playerName }),
        });
        
        const data = await response.json();
        if (data.error) {
            showMessage(data.error, 'error');
            return;
        }
        
        state.gameId = gameId;
        state.playerId = data.player_id;
        state.playerName = playerName;
        
        document.getElementById('game-id-display').textContent = state.gameId;
        showScreen('setup');
        
        // Show character creation
        document.getElementById('character-creation').classList.remove('hidden');
        
        // Join socket room
        state.socket.emit('join_game', { game_id: state.gameId });
        
        updatePlayerList();
        
    } catch (error) {
        showMessage('Failed to join game', 'error');
    }
}

async function createCharacter() {
    const className = document.getElementById('char-class').value;
    const charName = document.getElementById('char-name').value.trim();
    
    if (!className || !charName) {
        showMessage('Please select a class and enter a name', 'error');
        return;
    }
    
    try {
        const response = await fetch(`/api/game/${state.gameId}/character`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                player_id: state.playerId,
                class_name: className,
                char_name: charName,
            }),
        });
        
        const data = await response.json();
        if (data.error) {
            showMessage(data.error, 'error');
            return;
        }
        
        // Hide character creation, show start button if host
        document.getElementById('character-creation').classList.add('hidden');
        updatePlayerList();
        
        // Check if all players have characters
        checkCanStart();
        
    } catch (error) {
        showMessage('Failed to create character', 'error');
    }
}

async function startGame() {
    try {
        const response = await fetch(`/api/game/${state.gameId}/start`, {
            method: 'POST',
        });
        
        const data = await response.json();
        if (data.error) {
            showMessage(data.error, 'error');
            return;
        }
        
    } catch (error) {
        showMessage('Failed to start game', 'error');
    }
}

// Socket Actions
function move(direction) {
    state.socket.emit('move', {
        game_id: state.gameId,
        direction: direction,
    });
}

function searchRoom() {
    state.socket.emit('search_room', {
        game_id: state.gameId,
    });
}

function attack() {
    state.socket.emit('attack', {
        game_id: state.gameId,
        target: state.selectedTarget || 0,
    });
}

// UI Updates
async function updatePlayerList() {
    if (!state.gameId) return;
    
    try {
        const response = await fetch(`/api/game/${state.gameId}/status`);
        const data = await response.json();
        
        const container = document.getElementById('players-list');
        container.innerHTML = '<h3>Players</h3>';
        
        data.players.forEach(player => {
            const div = document.createElement('div');
            div.className = 'character-card';
            
            if (player.character) {
                const c = player.character;
                div.innerHTML = `
                    <h4>${c.name} (${player.name})</h4>
                    <p>${c.class_type} - Level ${c.level}</p>
                    <div class="stat-row">
                        <span class="stat-label">ATK:</span>
                        <span class="stat-value">${c.attack}</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">DEF:</span>
                        <span class="stat-value">${c.defense}</span>
                    </div>
                    <div class="stat-row">
                        <span class="stat-label">LIFE:</span>
                        <span class="stat-value">${c.life}/${c.max_life}</span>
                    </div>
                `;
            } else {
                div.innerHTML = `<p>${player.name} - Creating character...</p>`;
            }
            
            container.appendChild(div);
        });
        
        checkCanStart();
        
    } catch (error) {
        console.error('Failed to update player list:', error);
    }
}

function checkCanStart() {
    // Simple check - in real app would check if player is host
    const startBtn = document.getElementById('start-game');
    startBtn.classList.remove('hidden');
}

function updateGameView() {
    const data = state.gameData;
    if (!data) return;
    
    // Update room display
    if (data.dungeon && data.dungeon.party_room) {
        const roomNum = data.dungeon.party_room;
        const roomImg = document.getElementById('room-image');
        roomImg.src = `/static/images/room_${String(roomNum).padStart(2, '0')}.png`;
        roomImg.onerror = () => {
            roomImg.src = '/static/images/room_01.png';
        };
        
        document.getElementById('room-number').textContent = `Room ${roomNum}`;
        
        // Update available exits
        const room = data.dungeon.rooms[roomNum];
        if (room) {
            document.querySelectorAll('.dir-btn').forEach(btn => {
                const dir = btn.dataset.dir;
                btn.disabled = !room.exits[dir];
            });
        }
    }
    
    // Update party list
    const partyList = document.getElementById('party-list');
    partyList.innerHTML = '';
    
    data.players.forEach(player => {
        if (player.character) {
            const c = player.character;
            const div = document.createElement('div');
            div.className = 'character-card';
            const lifePercent = (c.life / c.max_life) * 100;
            div.innerHTML = `
                <h4>${c.name}</h4>
                <p>${c.class_type}</p>
                <div class="stat-row">
                    <span>ATK ${c.attack} | DEF ${c.defense}</span>
                </div>
                <div class="life-bar">
                    <div class="life-fill ${lifePercent < 30 ? 'low' : ''}" style="width: ${lifePercent}%"></div>
                </div>
                <div class="stat-row">
                    <span class="stat-value">${c.life}/${c.max_life} HP</span>
                </div>
            `;
            partyList.appendChild(div);
        }
    });
    
    // Update combat panel
    const combatPanel = document.getElementById('combat-panel');
    if (data.combat_active && data.monsters.length > 0) {
        combatPanel.classList.remove('hidden');
        
        const monstersList = document.getElementById('monsters-list');
        monstersList.innerHTML = '';
        monstersList.setAttribute('role', 'listbox');
        monstersList.setAttribute('aria-label', 'Monster targets');

        data.monsters.forEach((monster, idx) => {
            const div = document.createElement('div');
            div.className = `monster-card ${monster.life <= 0 ? 'dead' : ''}`;
            div.setAttribute('role', 'option');
            div.innerHTML = `
                <strong>${monster.name}</strong> (Lvl ${monster.level})
                <br>Life: ${monster.life}/${monster.max_life}
            `;
            if (monster.life <= 0) {
                div.setAttribute('aria-disabled', 'true');
                div.setAttribute('aria-selected', 'false');
            } else {
                div.setAttribute('tabindex', '0');
                div.setAttribute('aria-selected', idx === state.selectedTarget ? 'true' : 'false');
                div.addEventListener('click', () => {
                    state.selectedTarget = idx;
                    applyMonsterSelection(monstersList);
                });
                div.addEventListener('keydown', (e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                        e.preventDefault();
                        state.selectedTarget = idx;
                        applyMonsterSelection(monstersList);
                    }
                });
                if (idx === state.selectedTarget) {
                    div.classList.add('selected');
                }
            }
            monstersList.appendChild(div);
        });

        // Clamp selectedTarget to a living monster
        const selected = data.monsters[state.selectedTarget];
        if (!selected || selected.life <= 0) {
            state.selectedTarget = data.monsters.findIndex(m => m.life > 0);
            if (state.selectedTarget < 0) state.selectedTarget = 0;
            applyMonsterSelection(monstersList);
        }
    } else {
        combatPanel.classList.add('hidden');
        state.selectedTarget = 0;
    }
    
    renderMessageLog(data);
}

function showCombatResult(data) {
    if (data.error) {
        showMessage(data.error, 'error');
        return;
    }
    
    const msg = data.hit 
        ? `${data.attacker} hits for ${data.damage} damage!`
        : `${data.attacker} misses!`;
    
    showMessage(msg, data.hit ? 'success' : 'info');
}

function showSearchResult(data) {
    if (data.error) {
        showMessage(data.error, 'error');
        return;
    }
    
    const messages = {
        hidden_treasure: 'Hidden treasure found!',
        clue: 'A clue is discovered...',
        nothing: 'Nothing found',
    };
    
    showMessage(messages[data.result] || 'Search complete', 'info');
}

function applyMonsterSelection(monstersList) {
    monstersList.querySelectorAll('.monster-card').forEach((c, i) => {
        c.classList.toggle('selected', i === state.selectedTarget);
        c.setAttribute('aria-selected', i === state.selectedTarget ? 'true' : 'false');
    });
}

function renderMessageLog(data) {
    const messagesDiv = document.getElementById('messages');
    messagesDiv.innerHTML = '';
    data.message_log.forEach(msg => {
        const div = document.createElement('div');
        div.className = 'message';
        div.textContent = msg;
        messagesDiv.appendChild(div);
    });
    state.clientErrors.forEach(msg => {
        const div = document.createElement('div');
        div.className = 'message message-error';
        div.textContent = msg;
        messagesDiv.appendChild(div);
    });
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

function showMessage(text, type = 'info') {
    // Persist client-side errors in state so they survive updateGameView re-renders
    if (type === 'error') {
        state.clientErrors.push(text);
        if (state.clientErrors.length > 20) {
            state.clientErrors = state.clientErrors.slice(-20);
        }
        // Re-render message log immediately so the error appears without waiting for game_update
        if (state.gameData) {
            renderMessageLog(state.gameData);
        }
    }

    // Show toast (all types)
    let toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toast-container';
        toastContainer.style.position = 'fixed';
        toastContainer.style.top = '20px';
        toastContainer.style.right = '20px';
        toastContainer.style.zIndex = '9999';
        toastContainer.setAttribute('role', 'log');
        toastContainer.setAttribute('aria-live', 'polite');
        document.body.appendChild(toastContainer);
    }
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    if (type === 'error') {
        toast.setAttribute('role', 'alert');
        toast.setAttribute('aria-live', 'assertive');
    } else {
        toast.setAttribute('role', 'status');
        toast.setAttribute('aria-live', 'polite');
    }
    toast.setAttribute('aria-atomic', 'true');
    toast.textContent = text;
    toastContainer.appendChild(toast);

    // Auto-remove after 3 seconds
    setTimeout(() => {
        toast.classList.add('toast-fade');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// Start the app
init();
