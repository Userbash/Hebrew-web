/**
 * API Tests
 * Comprehensive test suite for all endpoints
 * Run with: npm test
 */

import fetch from 'node-fetch';

const BASE_URL = 'http://127.0.0.1:3001';
const API_URL = `${BASE_URL}/api`;

// Colors for console output
const colors = {
    reset: '\x1b[0m',
    green: '\x1b[32m',
    red: '\x1b[31m',
    yellow: '\x1b[33m',
    blue: '\x1b[34m',
    cyan: '\x1b[36m'
};

class APITester {
    constructor() {
        this.token = null;
        this.userId = null;
        this.testCount = 0;
        this.passedCount = 0;
        this.failedCount = 0;
        this.results = [];
    }

    log(message, color = 'reset') {
        console.log(`${colors[color]}${message}${colors.reset}`);
    }

    async request(method, endpoint, body = null) {
        const url = `${API_URL}${endpoint}`;
        const options = {
            method,
            headers: {
                'Content-Type': 'application/json'
            }
        };

        if (this.token) {
            options.headers.Authorization = `Bearer ${this.token}`;
        }

        if (body) {
            options.body = JSON.stringify(body);
        }

        try {
            const response = await fetch(url, options);
            const data = await response.json();
            return { status: response.status, data };
        } catch (error) {
            return { status: 0, error: error.message };
        }
    }

    test(name, condition) {
        this.testCount++;
        const passed = condition === true;

        if (passed) {
            this.passedCount++;
            this.log(`  ✓ ${name}`, 'green');
        } else {
            this.failedCount++;
            this.log(`  ✗ ${name}`, 'red');
        }

        this.results.push({ name, passed, condition });
    }

    async section(title, fn) {
        this.log(`\n${title}`, 'cyan');
        await fn();
    }

    summary() {
        this.log('\n' + '═'.repeat(60), 'blue');
        this.log('\nTest Summary', 'blue');
        this.log(`  Total:  ${this.testCount}`, 'cyan');
        this.log(`  Passed: ${this.passedCount}`, 'green');
        this.log(`  Failed: ${this.failedCount}`, this.failedCount > 0 ? 'red' : 'green');

        const percentage = Math.round((this.passedCount / this.testCount) * 100);
        this.log(`  Success Rate: ${percentage}%\n`, percentage === 100 ? 'green' : 'yellow');

        if (this.failedCount > 0) {
            this.log('Failed Tests:', 'red');
            this.results
                .filter(r => !r.passed)
                .forEach(r => {
                    this.log(`  - ${r.name}`, 'red');
                });
        }

        this.log('═'.repeat(60) + '\n', 'blue');
    }
}

// Run tests
const tester = new APITester();

(async () => {
    try {
        tester.log('\n╔════════════════════════════════════════════════════════════╗', 'cyan');
        tester.log('║           Hebrew AI 2025 - API Test Suite                  ║', 'cyan');
        tester.log('╚════════════════════════════════════════════════════════════╝\n', 'cyan');

        // ═════════════════════════════════════════════════════════════════════
        // HEALTH CHECK
        // ═════════════════════════════════════════════════════════════════════

        await tester.section('Health Check', async () => {
            const { status, data } = await tester.request('GET', '/health');
            tester.test('Server is running', status === 200);
            tester.test('Health status is OK', data.status === 'OK');
        });

        // ═════════════════════════════════════════════════════════════════════
        // AUTHENTICATION TESTS
        // ═════════════════════════════════════════════════════════════════════

        await tester.section('Authentication', async () => {
            // Register
            const { status: regStatus, data: regData } = await tester.request('POST', '/auth/register', {
                email: 'test@example.com',
                password: 'password123',
                firstName: 'Test',
                lastName: 'User'
            });

            tester.test('Register successful', regStatus === 201);
            tester.test('Register returns user', regData.user !== undefined);
            tester.test('Register returns token', regData.token !== undefined);

            if (regData.token) {
                tester.token = regData.token;
                tester.userId = regData.user.id;
            }

            // Try to register again (should fail)
            const { status: dupStatus } = await tester.request('POST', '/auth/register', {
                email: 'test@example.com',
                password: 'password456',
                firstName: 'Another',
                lastName: 'User'
            });

            tester.test('Cannot register duplicate email', dupStatus === 409);

            // Login
            const { status: loginStatus, data: loginData } = await tester.request('POST', '/auth/login', {
                email: 'test@example.com',
                password: 'password123'
            });

            tester.test('Login successful', loginStatus === 200);
            tester.test('Login returns token', loginData.token !== undefined);

            // Wrong password
            const { status: wrongPassStatus } = await tester.request('POST', '/auth/login', {
                email: 'test@example.com',
                password: 'wrongpassword'
            });

            tester.test('Login fails with wrong password', wrongPassStatus === 401);

            // Verify token
            const { status: verifyStatus } = await tester.request('GET', '/auth/verify');
            tester.test('Token verification successful', verifyStatus === 200);
        });

        // ═════════════════════════════════════════════════════════════════════
        // USER TESTS
        // ═════════════════════════════════════════════════════════════════════

        await tester.section('User Management', async () => {
            // Get profile
            const { status: profileStatus, data: profileData } = await tester.request('GET', '/users/profile');
            tester.test('Get profile successful', profileStatus === 200);
            tester.test('Profile contains user data', profileData.user !== undefined);
            tester.test('Profile does not contain password', profileData.user.password === undefined);

            // Update profile
            const { status: updateStatus } = await tester.request('PUT', '/users/profile', {
                firstName: 'Updated',
                lastName: 'Name'
            });

            tester.test('Update profile successful', updateStatus === 200);

            // Get leaderboard
            const { status: leaderStatus, data: leaderData } = await tester.request('GET', '/users/stats/leaderboard?limit=5');
            tester.test('Get leaderboard successful', leaderStatus === 200);
            tester.test('Leaderboard returns array', Array.isArray(leaderData.leaderboard));
        });

        // ═════════════════════════════════════════════════════════════════════
        // LESSONS TESTS
        // ═════════════════════════════════════════════════════════════════════

        await tester.section('Lessons', async () => {
            // Get all lessons
            const { status: lessonsStatus, data: lessonsData } = await tester.request('GET', '/lessons');
            tester.test('Get all lessons successful', lessonsStatus === 200);
            tester.test('Returns lessons array', Array.isArray(lessonsData.lessons));
            tester.test('Has lessons', lessonsData.lessons.length > 0);

            if (lessonsData.lessons.length > 0) {
                const lessonId = lessonsData.lessons[0].id;

                // Get single lesson
                const { status: singleStatus } = await tester.request('GET', `/lessons/${lessonId}`);
                tester.test('Get single lesson successful', singleStatus === 200);

                // Complete lesson
                const { status: completeStatus } = await tester.request('POST', `/lessons/${lessonId}/complete`);
                tester.test('Complete lesson successful', completeStatus === 200);
            }

            // Get by difficulty
            const { status: diffStatus } = await tester.request('GET', '/lessons?difficulty=beginner');
            tester.test('Filter by difficulty successful', diffStatus === 200);
        });

        // ═════════════════════════════════════════════════════════════════════
        // QUIZZES TESTS
        // ═════════════════════════════════════════════════════════════════════

        await tester.section('Quizzes', async () => {
            // Get all quizzes
            const { status: quizzesStatus, data: quizzesData } = await tester.request('GET', '/quizzes');
            tester.test('Get all quizzes successful', quizzesStatus === 200);
            tester.test('Returns quizzes array', Array.isArray(quizzesData.quizzes));
            tester.test('Has quizzes', quizzesData.quizzes.length > 0);

            if (quizzesData.quizzes.length > 0) {
                const quizId = quizzesData.quizzes[0].id;
                const quiz = quizzesData.quizzes[0];

                // Get single quiz
                const { status: singleStatus } = await tester.request('GET', `/quizzes/${quizId}`);
                tester.test('Get single quiz successful', singleStatus === 200);

                // Submit quiz with correct answers
                const answers = [0, 1, 1]; // Adjust based on actual questions
                const { status: submitStatus, data: submitData } = await tester.request(
                    'POST',
                    `/quizzes/${quizId}/submit`,
                    { answers }
                );

                tester.test('Submit quiz successful', submitStatus === 200);
                tester.test('Returns attempt results', submitData.attempt !== undefined);
                tester.test('Returns score', submitData.attempt.score !== undefined);

                // Get attempts
                const { status: attemptsStatus } = await tester.request('GET', `/quizzes/${quizId}/attempts`);
                tester.test('Get quiz attempts successful', attemptsStatus === 200);
            }
        });

        // ═════════════════════════════════════════════════════════════════════
        // DICTIONARY TESTS
        // ═════════════════════════════════════════════════════════════════════

        await tester.section('Dictionary', async () => {
            // Get all words
            const { status: allStatus, data: allData } = await tester.request('GET', '/dictionary');
            tester.test('Get all words successful', allStatus === 200);
            tester.test('Returns words array', Array.isArray(allData.words));
            tester.test('Has words', allData.words.length > 0);

            // Search dictionary
            const { status: searchStatus, data: searchData } = await tester.request('GET', '/dictionary?q=shalom');
            tester.test('Search dictionary successful', searchStatus === 200);
            tester.test('Search returns results', Array.isArray(searchData.words));

            // Get single word
            if (allData.words.length > 0) {
                const wordId = allData.words[0].id;
                const { status: singleStatus } = await tester.request('GET', `/dictionary/${wordId}`);
                tester.test('Get single word successful', singleStatus === 200);
            }
        });

        // ═════════════════════════════════════════════════════════════════════
        // PROGRESS TESTS
        // ═════════════════════════════════════════════════════════════════════

        await tester.section('Progress Tracking', async () => {
            // Get user progress
            const { status: progressStatus, data: progressData } = await tester.request('GET', '/progress');
            tester.test('Get progress successful', progressStatus === 200);
            tester.test('Progress contains xp data', progressData.progress.xpTotal !== undefined);

            // Get progress summary
            const { status: summaryStatus, data: summaryData } = await tester.request('GET', '/progress/stats/summary');
            tester.test('Get progress summary successful', summaryStatus === 200);
            tester.test('Summary contains level', summaryData.stats.currentLevel !== undefined);
            tester.test('Summary contains xp', summaryData.stats.currentXp !== undefined);

            // Get comparison
            const { status: compStatus } = await tester.request('GET', '/progress/stats/comparison');
            tester.test('Get progress comparison successful', compStatus === 200);
        });

        // ═════════════════════════════════════════════════════════════════════
        // ERROR HANDLING TESTS
        // ═════════════════════════════════════════════════════════════════════

        await tester.section('Error Handling', async () => {
            // Non-existent endpoint
            const { status: notFoundStatus } = await tester.request('GET', '/nonexistent');
            tester.test('404 for non-existent route', notFoundStatus === 404);

            // Missing auth
            const savedToken = tester.token;
            tester.token = null;

            const { status: unAuthStatus } = await tester.request('GET', '/users/profile');
            tester.test('401 for unauthenticated request', unAuthStatus === 401);

            tester.token = savedToken;

            // Invalid JSON
            const { status: invalidStatus } = await tester.request('POST', '/auth/login', {
                // Missing required fields
            });

            tester.test('400 for invalid request', invalidStatus === 400);
        });

        // Print summary
        tester.summary();

        process.exit(tester.failedCount > 0 ? 1 : 0);

    } catch (error) {
        tester.log(`\n${colors.red}Fatal Error: ${error.message}${colors.reset}`);
        console.error(error);
        process.exit(1);
    }
})();
