/**
 * Legacy frontend API client.
 *
 * Current backend auth relies on HttpOnly cookies, so this client always sends
 * same-origin credentials and does not depend on tokens in JSON responses.
 */

class APIClient {
    constructor(baseURL = '') {
        this.baseURL = baseURL || '';
        this.token = null;
        this.timeout = 10000;
    }

    async request(method, endpoint, options = {}) {
        const url = `${this.baseURL}/api${endpoint}`;
        const headers = {
            'Content-Type': 'application/json',
            ...options.headers,
        };

        if (this.token) {
            headers.Authorization = `Bearer ${this.token}`;
        }

        const config = {
            method,
            headers,
            credentials: 'same-origin',
            ...options,
        };

        if (options.body && typeof options.body === 'object') {
            config.body = JSON.stringify(options.body);
        }

        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), this.timeout);

            const response = await fetch(url, {
                ...config,
                signal: controller.signal,
            });

            clearTimeout(timeoutId);

            if (response.status === 401) {
                this.logout();
                window.location.href = '/login';
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

    setToken(token) {
        this.token = token || null;
    }

    logout() {
        this.setToken(null);
    }

    getToken() {
        return this.token;
    }

    async register(email, password, confirmPassword, username, firstName = '', lastName = '') {
        return this.request('POST', '/auth/register', {
            body: { email, password, confirmPassword, username, firstName, lastName },
        });
    }

    async login(email, password) {
        return this.request('POST', '/auth/login', {
            body: { email, password },
        });
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
        return this.request('POST', '/auth/refresh');
    }

    async getProfile() {
        return this.request('GET', '/users/profile');
    }

    async updateProfile(firstName, lastName, avatar) {
        return this.request('PUT', '/users/profile', {
            body: { firstName, lastName, avatar },
        });
    }

    async getUser(userId) {
        return this.request('GET', `/users/${userId}`);
    }

    async getLeaderboard(limit = 10) {
        return this.request('GET', `/users/stats/leaderboard?limit=${limit}`);
    }

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
        return this.request('POST', '/lessons', { body: lessonData });
    }

    async updateLesson(id, updates) {
        return this.request('PUT', `/lessons/${id}`, { body: updates });
    }

    async getQuizzes(difficulty = null, lessonId = null) {
        const query = [];
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
            body: { answers },
        });
    }

    async getQuizAttempts(id) {
        return this.request('GET', `/quizzes/${id}/attempts`);
    }

    async createQuiz(quizData) {
        return this.request('POST', '/quizzes', {
            body: quizData,
        });
    }

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
            body: wordData,
        });
    }

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

    isAuthenticated() {
        return !!this.token;
    }

    async getHealth() {
        return fetch(`${this.baseURL}/api/health`).then((r) => r.json());
    }

    async getSchema() {
        return this.request('GET', '/schema');
    }
}

const api = new APIClient();

if (typeof module !== 'undefined' && module.exports) {
    module.exports = APIClient;
}
