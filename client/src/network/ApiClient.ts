import type { GameState, CharacterState } from '../types';

/**
 * ApiClient — typed REST API client for all backend endpoints.
 */
class ApiClient {
  private baseUrl: string;
  private static instance: ApiClient;

  private constructor(baseUrl = '') {
    this.baseUrl = baseUrl;
  }

  static getInstance(): ApiClient {
    if (!ApiClient.instance) {
      ApiClient.instance = new ApiClient();
    }
    return ApiClient.instance;
  }

  // ---- Game lifecycle ----

  async createGame(): Promise<{ game_id: string; join_url: string }> {
    return this.post('/api/game/create');
  }

  async joinGame(
    gameId: string,
    playerName: string,
  ): Promise<{ player_id: string; player_name: string }> {
    return this.post(`/api/game/${gameId}/join`, { player_name: playerName });
  }

  async createCharacter(
    gameId: string,
    playerId: string,
    className: string,
    charName: string,
  ): Promise<CharacterState> {
    return this.post(`/api/game/${gameId}/character`, {
      player_id: playerId,
      class_name: className,
      char_name: charName,
    });
  }

  async startGame(gameId: string): Promise<GameState> {
    return this.post(`/api/game/${gameId}/start`);
  }

  async getGameStatus(gameId: string): Promise<GameState> {
    return this.get(`/api/game/${gameId}/status`);
  }

  // ---- Character data ----

  async getClasses(): Promise<string[]> {
    return this.get('/api/classes');
  }

  // ---- Shop ----

  async getShopInventory(): Promise<Record<string, unknown>> {
    return this.get('/api/equipment/shop');
  }

  async buyItem(
    gameId: string,
    playerId: string,
    characterId: string,
    itemId: string,
  ): Promise<CharacterState> {
    return this.post(`/api/game/${gameId}/buy`, {
      player_id: playerId,
      character_id: characterId,
      item_id: itemId,
    });
  }

  async sellItem(
    gameId: string,
    playerId: string,
    characterId: string,
    itemId: string,
    slot: string,
  ): Promise<CharacterState> {
    return this.post(`/api/game/${gameId}/sell`, {
      player_id: playerId,
      character_id: characterId,
      item_id: itemId,
      slot,
    });
  }

  // ---- Campaign ----

  async createCampaign(name: string): Promise<{ campaign_id: string; name: string }> {
    return this.post('/api/campaign/create', { name });
  }

  async getCampaign(campaignId: string): Promise<Record<string, unknown>> {
    return this.get(`/api/campaign/${campaignId}`);
  }

  async saveCampaign(
    campaignId: string,
    gameId: string,
    victory: boolean,
  ): Promise<{ saved: boolean }> {
    return this.post(`/api/campaign/${campaignId}/save`, {
      game_id: gameId,
      victory,
    });
  }

  // ---- HTTP helpers ----

  private async get<T>(path: string): Promise<T> {
    const res = await fetch(`${this.baseUrl}${path}`);
    if (!res.ok) {
      const err = await res.json().catch(() => ({ error: res.statusText }));
      throw new Error(err.error || `HTTP ${res.status}`);
    }
    return res.json() as Promise<T>;
  }

  private async post<T>(path: string, body?: Record<string, unknown>): Promise<T> {
    const res = await fetch(`${this.baseUrl}${path}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: body ? JSON.stringify(body) : undefined,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ error: res.statusText }));
      throw new Error(err.error || `HTTP ${res.status}`);
    }
    return res.json() as Promise<T>;
  }
}

export default ApiClient;
