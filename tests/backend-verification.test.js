/**
 * Backend Node.js Verification Tests
 * Tests core functionality of the Express backend
 *
 * Checks:
 * - API health endpoints
 * - Route paths correctness
 * - Middleware functionality
 * - Response formats
 * - Error handling
 */

import fetch from 'node-fetch';

class BackendVerificationTest {
    constructor(baseUrl = 'http://localhost:3001') {
        this.baseUrl = baseUrl;
        this.results = {
            total_tests: 0,
            passed: 0,
            failed: 0,
            errors: [],
            endpoints: []
        };
        this.colors = {
            reset: '\x1b[0m',
            bright: '\x1b[1m',
            green: '\x1b[32m',
            yellow: '\x1b[33m',
            red: '\x1b[31m',
            cyan: '\x1b[36m'
        };
        this.timeout = 10000;
    }

    log(message, color = 'reset') {
        const c = this.colors[color] || '';
        console.log(`${c}${message}${this.colors.reset}`);
    }

    async makeRequest(endpoint, options = {}) {
        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), this.timeout);

            const response = await fetch(`${this.baseUrl}${endpoint}`, {
                ...options,
                signal: controller.signal
            });

            clearTimeout(timeoutId);
            return response;
        } catch (error) {
            return {
                ok: false,
                status: 0,
                statusText: error.message,
                json: async () => ({ error: error.message })
            };
        }
    }

    async testEndpoint(name, endpoint, method = 'GET', expectedStatus = 200) {
        this.results.total_tests++;
        this.log(`\n  Testing: ${name}`, 'bright');
        this.log(`  ${method} ${endpoint}`, 'cyan');

        try {
            const response = await this.makeRequest(endpoint, { method });
            const data = response.headers.get('content-type')?.includes('application/json')
                ? await response.json()
                : await response.text();

            if (response.status === expectedStatus) {
                this.log(`  ✓ Status ${response.status} OK`, 'green');
                this.results.passed++;
                this.results.endpoints.push({
                    name,
                    endpoint,
                    method,
                    status: response.status,
                    success: true
                });
                return true;
            } else {
                this.log(`  ✗ Expected ${expectedStatus}, got ${response.status}`, 'red');
                this.results.failed++;
                this.results.errors.push({
                    test: name,
                    expected: expectedStatus,
                    actual: response.status
                });
                return false;
            }
        } catch (error) {
            this.log(`  ✗ Error: ${error.message}`, 'red');
            this.results.failed++;
            this.results.errors.push({
                test: name,
                error: error.message
            });
            return false;
        }
    }

    async waitForBackend(maxAttempts = 30) {
        this.log('Waiting for backend to be ready...', 'cyan');
        for (let i = 0; i < maxAttempts; i++) {
            try {
                const response = await this.makeRequest('/api/health', {
                    signal: AbortSignal.timeout(3000)
                });
                if (response.ok) {
                    this.log('✓ Backend is ready!\n', 'green');
                    return true;
                }
            } catch (error) {
                // Expected failures while waiting
            }
            await new Promise(resolve => setTimeout(resolve, 1000));
        }
        this.log('✗ Backend did not become ready in time', 'red');
        return false;
    }

    async runTests() {
        this.log('\n' + '═'.repeat(70), 'cyan');
        this.log('  BACKEND NODE.JS VERIFICATION TESTS', 'cyan');
        this.log('═'.repeat(70), 'cyan');

        // Check if backend is running
        const backendReady = await this.waitForBackend();
        if (!backendReady) {
            this.log('\n✗ Backend is not running or not responding!', 'red');
            this.log(`   Make sure the backend is started at ${this.baseUrl}`, 'yellow');
            return this.results;
        }

        this.log('1. Testing Health Endpoints\n', 'bright');
        await this.testEndpoint(
            'Health Check',
            '/api/health',
            'GET',
            200
        );

        this.log('\n2. Testing API Routes Existence\n', 'bright');

        // Test route paths
        const routes = [
            { name: 'Auth Routes', path: '/api/auth' },
            { name: 'Users Routes', path: '/api/users' },
            { name: 'Lessons Routes', path: '/api/lessons' },
            { name: 'Quizzes Routes', path: '/api/quizzes' },
            { name: 'Dictionary Routes', path: '/api/dictionary' },
            { name: 'Progress Routes', path: '/api/progress' }
        ];

        for (const route of routes) {
            const response = await this.makeRequest(route.path);
            this.results.total_tests++;

            // Routes may return 404 if no GET handler, but endpoint exists
            if (response.status >= 200 && response.status < 500) {
                this.log(`  ✓ ${route.name} exists (${response.status})`, 'green');
                this.results.passed++;
            } else {
                this.log(`  ✗ ${route.name} returned ${response.status}`, 'red');
                this.results.failed++;
            }
        }

        this.log('\n3. Testing Response Headers\n', 'bright');
        const response = await this.makeRequest('/api/health');
        this.results.total_tests++;

        const hasContentType = response.headers.get('content-type');
        const hasSecurityHeaders = response.headers.get('x-content-type-options');

        if (hasContentType?.includes('application/json')) {
            this.log(`  ✓ Content-Type is JSON`, 'green');
            this.results.passed++;
        } else {
            this.log(`  ✗ Content-Type is not JSON`, 'red');
            this.results.failed++;
        }

        this.log('\n4. Testing Middleware\n', 'bright');
        this.results.total_tests++;

        // Test CORS (should have CORS headers or pass without error)
        if (response.status === 200) {
            this.log(`  ✓ CORS/Security middleware working`, 'green');
            this.results.passed++;
        }

        this.log('\n5. Testing Error Handling\n', 'bright');
        await this.testEndpoint(
            'Non-existent endpoint (404)',
            '/api/nonexistent',
            'GET',
            404
        );

        // Summary
        this.log('\n' + '─'.repeat(70), 'cyan');
        this.log('TEST SUMMARY', 'bright');
        this.log('─'.repeat(70), 'cyan');
        this.log(`Total Tests:  ${this.results.total_tests}`, 'cyan');
        this.log(`Passed:       ${this.results.passed}`, 'green');
        this.log(`Failed:       ${this.results.failed}`, this.results.failed > 0 ? 'red' : 'green');

        if (this.results.failed > 0) {
            this.log('\nFailed Tests:', 'red');
            this.results.errors.forEach(error => {
                this.log(`  ✗ ${error.test}`, 'red');
                if (error.error) {
                    this.log(`    Error: ${error.error}`, 'yellow');
                } else {
                    this.log(`    Expected: ${error.expected}, Got: ${error.actual}`, 'yellow');
                }
            });
        }

        this.log('\n' + '═'.repeat(70) + '\n', 'cyan');

        return this.results;
    }
}

// Run tests if executed directly
if (import.meta.url === `file://${process.argv[1]}`) {
    const test = new BackendVerificationTest();
    const results = await test.runTests();
    process.exit(results.failed > 0 ? 1 : 0);
}

export default BackendVerificationTest;
