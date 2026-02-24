/**
 * API and WebSocket service for connecting to AIDEN Labs backend
 */

const API_BASE = 'http://localhost:8000';
const WS_BASE = 'ws://localhost:8000';

/**
 * Fetch errors with pagination and filters
 */
export async function fetchErrors(page = 1, perPage = 20, deviceId = null, severity = null) {
    const params = new URLSearchParams({ page, per_page: perPage });
    if (deviceId) params.append('device_id', deviceId);
    if (severity) params.append('severity', severity);

    const response = await fetch(`${API_BASE}/api/errors?${params}`);
    if (!response.ok) throw new Error('Failed to fetch errors');
    return response.json();
}

/**
 * Fetch active (non-dismissed) errors for dashboard
 */
export async function fetchActiveErrors(page = 1, perPage = 20) {
    const params = new URLSearchParams({ page, per_page: perPage });
    const response = await fetch(`${API_BASE}/api/errors/active?${params}`);
    if (!response.ok) throw new Error('Failed to fetch active errors');
    return response.json();
}

/**
 * Fetch a single error by ID
 */
export async function fetchError(errorId) {
    const response = await fetch(`${API_BASE}/api/errors/${errorId}`);
    if (!response.ok) throw new Error('Error not found');
    return response.json();
}

/**
 * Fetch device list with stats
 */
export async function fetchDevices() {
    const response = await fetch(`${API_BASE}/api/devices`);
    if (!response.ok) throw new Error('Failed to fetch devices');
    return response.json();
}

/**
 * Fetch overall stats
 */
export async function fetchStats() {
    const response = await fetch(`${API_BASE}/api/stats`);
    if (!response.ok) throw new Error('Failed to fetch stats');
    return response.json();
}

/**
 * Fetch health status
 */
export async function fetchHealth() {
    const response = await fetch(`${API_BASE}/api/health`);
    if (!response.ok) throw new Error('Backend unavailable');
    return response.json();
}

/**
 * Dismiss a single error (marks as dismissed, still visible in history)
 */
export async function dismissError(errorId) {
    const response = await fetch(`${API_BASE}/api/errors/${errorId}/dismiss`, {
        method: 'POST'
    });
    if (!response.ok) throw new Error('Failed to dismiss error');
    return response.json();
}

/**
 * Dismiss all errors (marks all as dismissed, still visible in history)
 */
export async function dismissAllErrors() {
    const response = await fetch(`${API_BASE}/api/errors/dismiss-all`, {
        method: 'POST'
    });
    if (!response.ok) throw new Error('Failed to dismiss errors');
    return response.json();
}

/**
 * WebSocket connection manager
 */
export class WebSocketManager {
    constructor(onMessage, onConnect, onDisconnect) {
        this.ws = null;
        this.onMessage = onMessage;
        this.onConnect = onConnect;
        this.onDisconnect = onDisconnect;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 10;
        this.reconnectDelay = 2000;
        this.hasConnectedOnce = false;
    }

    connect() {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            return;
        }

        try {
            this.ws = new WebSocket(`${WS_BASE}/ws`);

            this.ws.onopen = () => {
                console.log('WebSocket connected');
                this.reconnectAttempts = 0;
                if (this.onConnect) this.onConnect(this.hasConnectedOnce);
                this.hasConnectedOnce = true;
            };

            this.ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    if (data.type === 'ping') {
                        this.ws.send('ping');
                    } else if (this.onMessage) {
                        this.onMessage(data);
                    }
                } catch (e) {
                    console.error('Error parsing WebSocket message:', e);
                }
            };

            this.ws.onclose = () => {
                console.log('WebSocket disconnected');
                if (this.onDisconnect) this.onDisconnect();
                this.attemptReconnect();
            };

            this.ws.onerror = (error) => {
                console.error('WebSocket error:', error);
            };
        } catch (error) {
            console.error('Failed to create WebSocket:', error);
            this.attemptReconnect();
        }
    }

    attemptReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            console.log(`Reconnecting... attempt ${this.reconnectAttempts}`);
            setTimeout(() => this.connect(), this.reconnectDelay);
        }
    }

    disconnect() {
        if (this.ws) {
            this.ws.close();
            this.ws = null;
        }
    }
}
