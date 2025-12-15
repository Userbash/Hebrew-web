/**
 * Frontend API Client
 * Handles all communication with the backend server
 */

class APIClient {
    constructor(baseURL = '') {
        this.baseURL = baseURL || '';
        this.token = localStorage.getItem('auth_token');
        this.timeout = 10000; // 10 seconds
    }

    /**
     * Internal fetch wrapper with error handling
     */
    async request(method, endpoint, options = {}) {
        const url = `${this.baseURL}/api${endpoint}`;
        const headers = {
            'Content-Type': 'application/json',
            ...options.headers
        };

        // Add auth token if available
        if (this.token) {
            headers.Authorization = `Bearer ${this.token}`;
        }

        const config = {
            method,
            headers,
            ...options
        };

        if (options.body && typeof options.body === 'object') {
            config.body = JSON.stringify(options.body);
        }

        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), this.timeout);

            const response = await fetch(url, {
                ...config,
                signal: controller.signal
            });

            clearTimeout(timeoutId);

            // Handle 401 Unauthorized - token expired
            if (response.status === 401) {
                this.logout();
                window.location.href = '/pages/login';
            }

            const data = await response.json();

            if (!response.ok) {
                const error = new Error(data.message || `HTTP ${response.status}`);
                error.status = response.status;
                error.response = data;
                throw error;
            }

            return data;
        } catch (error) {
            if (error.name === 'AbortError') {
                throw new Error('Request timeout');
            }
            throw error;
        }
    }

    /**
     * Set authentication token
     */
    setToken(token) {
        this.token = token;
        if (token) {
            localStorage.setItem('auth_token', token);
        } else {
            localStorage.removeItem('auth_token');
        }
    }

    /**
     * Logout - remove token
     */
    logout() {
        this.setToken(null);
    }

    /**
     * Get stored token
     */
    getToken() {
        return this.token;
    }

    // ═══════════════════════════════════════════════════════════════════════
    // AUTHENTICATION ENDPOINTS
    // ═══════════════════════════════════════════════════════════════════════

    async register(email, password, firstName = '', lastName = '') {
        const response = await this.request('POST', '/auth/register', {
            body: { email, password, firstName, lastName }
        });

        if (response.token) {
            this.setToken(response.token);
        }

        return response;
    }

    async login(email, password) {
        const response = await this.request('POST', '/auth/login', {
            body: { email, password }
        });

        if (response.token) {
            this.setToken(response.token);
        }

        return response;
    }

    async logout_request() {
        try {
            await this.request('POST', '/auth/logout');
        } finally {
            this.logout();
        }
    }

    async verifyToken() {
        return this.request('GET', '/auth/verify');
    }

    async refreshToken() {
        const response = await this.request('POST', '/auth/refresh');

        if (response.token) {
            this.setToken(response.token);
        }

        return response;
    }

    // ═══════════════════════════════════════════════════════════════════════
    // USER ENDPOINTS
    // ═══════════════════════════════════════════════════════════════════════

    async getProfile() {
        return this.request('GET', '/users/profile');
    }

    async updateProfile(firstName, lastName, avatar) {
        return this.request('PUT', '/users/profile', {
            body: { firstName, lastName, avatar }
        });
    }

    async getUser(userId) {
        return this.request('GET', `/users/${userId}`);
    }

    async getLeaderboard(limit = 10) {
        return this.request('GET', `/users/stats/leaderboard?limit=${limit}`);
    }

    // ═══════════════════════════════════════════════════════════════════════
    // LESSONS ENDPOINTS
    // ═══════════════════════════════════════════════════════════════════════

    async getLessons(difficulty = null) {
        const query = difficulty ? `?difficulty=${difficulty}` : '';
        return this.request('GET', `/lessons${query}`);
    }

    async getLesson(id) {
        return this.request('GET', `/lessons/${id}`);
    }

    async completeLesson(id) {
        return this.request('POST', `/lessons/${id}/complete`);
    }

    async createLesson(lessonData) {
        return this.request('POST', '/lessons', {
            body: lessonData
        });
    }

    async updateLesson(id, updates) {
        return this.request('PUT', `/lessons/${id}`, {
            body: updates
        });
    }

    // ═══════════════════════════════════════════════════════════════════════
    // QUIZZES ENDPOINTS
    // ═══════════════════════════════════════════════════════════════════════

    async getQuizzes(difficulty = null, lessonId = null) {
        let query = [];
        if (difficulty) query.push(`difficulty=${difficulty}`);
        if (lessonId) query.push(`lessonId=${lessonId}`);

        const queryString = query.length > 0 ? `?${query.join('&')}` : '';
        return this.request('GET', `/quizzes${queryString}`);
    }

    async getQuiz(id) {
        return this.request('GET', `/quizzes/${id}`);
    }

    async submitQuiz(id, answers) {
        return this.request('POST', `/quizzes/${id}/submit`, {
            body: { answers }
        });
    }

    async getQuizAttempts(id) {
        return this.request('GET', `/quizzes/${id}/attempts`);
    }

    async createQuiz(quizData) {
        return this.request('POST', '/quizzes', {
            body: quizData
        });
    }

    // ═══════════════════════════════════════════════════════════════════════
    // DICTIONARY ENDPOINTS
    // ═══════════════════════════════════════════════════════════════════════

    async searchDictionary(query, limit = 20) {
        const encodedQuery = encodeURIComponent(query);
        return this.request('GET', `/dictionary?q=${encodedQuery}&limit=${limit}`);
    }

    async getDictionaryWord(id) {
        return this.request('GET', `/dictionary/${id}`);
    }

    async getAllDictionaryWords(limit = 20) {
        return this.request('GET', `/dictionary?limit=${limit}`);
    }

    async addDictionaryWord(wordData) {
        return this.request('POST', '/dictionary', {
            body: wordData
        });
    }

    // ═══════════════════════════════════════════════════════════════════════
    // PROGRESS ENDPOINTS
    // ═══════════════════════════════════════════════════════════════════════

    async getProgress() {
        return this.request('GET', '/progress');
    }

    async getUserProgress(userId) {
        return this.request('GET', `/progress/${userId}`);
    }

    async getProgressSummary() {
        return this.request('GET', '/progress/stats/summary');
    }

    async getProgressComparison() {
        return this.request('GET', '/progress/stats/comparison');
    }

    // ═══════════════════════════════════════════════════════════════════════
    // UTILITY METHODS
    // ═══════════════════════════════════════════════════════════════════════

    /**
     * Check if user is authenticated
     */
    isAuthenticated() {
        return !!this.token;
    }

    /**
     * Get health status
     */
    async getHealth() {
        return fetch(`${this.baseURL}/api/health`).then(r => r.json());
    }

    /**
     * Get all endpoint schemas
     */
    async getSchema() {
        return this.request('GET', '/schema');
    }
}

// Create global API instance
const api = new APIClient();

// Export for module use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = APIClient;
}
