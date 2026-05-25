/* eslint-disable no-console */
/**
 * Full API contract test suite.
 * Validates the current backend behavior with cookie-based sessions.
 */

import fetch from 'node-fetch';

const BASE_URL = 'http://127.0.0.1:3001';
const API_URL = `${BASE_URL}/api`;

const colors = {
    reset: '\x1b[0m',
    green: '\x1b[32m',
    red: '\x1b[31m',
    yellow: '\x1b[33m',
    blue: '\x1b[34m',
    cyan: '\x1b[36m',
};

class CookieJar {
    constructor() {
        this.cookies = new Map();
    }

    merge(setCookieHeaders = []) {
        for (const header of setCookieHeaders) {
            const pair = header.split(';')[0];
            const idx = pair.indexOf('=');
            if (idx <= 0) continue;
            const name = pair.slice(0, idx).trim();
            const value = pair.slice(idx + 1).trim();
            if (value) {
                this.cookies.set(name, value);
            } else {
                this.cookies.delete(name);
            }
        }
    }

    toHeader() {
        return Array.from(this.cookies.entries())
            .map(([name, value]) => `${name}=${value}`)
            .join('; ');
    }
}

class APITester {
    constructor() {
        this.userId = null;
        this.jar = new CookieJar();
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
        const headers = { 'Content-Type': 'application/json' };
        const cookieHeader = this.jar.toHeader();
        if (cookieHeader) {
            headers.Cookie = cookieHeader;
        }

        const options = { method, headers };
        if (body) {
            options.body = JSON.stringify(body);
        }

        try {
            const response = await fetch(url, options);
            const setCookies = response.headers.raw()['set-cookie'] || [];
            this.jar.merge(setCookies);

            const text = await response.text();
            let data = null;
            try {
                data = text ? JSON.parse(text) : null;
            } catch {
                data = null;
            }

            return { status: response.status, data };
        } catch (error) {
            return { status: 0, error: error.message, data: null };
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

        const percentage = this.testCount > 0
            ? Math.round((this.passedCount / this.testCount) * 100)
            : 0;
        this.log(`  Success Rate: ${percentage}%\n`, percentage === 100 ? 'green' : 'yellow');

        if (this.failedCount > 0) {
            this.log('Failed Tests:', 'red');
            this.results
                .filter((r) => !r.passed)
                .forEach((r) => {
                    this.log(`  - ${r.name}`, 'red');
                });
        }

        this.log('═'.repeat(60) + '\n', 'blue');
    }
}

const tester = new APITester();

(async () => {
    try {
        tester.log('\n╔════════════════════════════════════════════════════════════╗', 'cyan');
        tester.log('║           Hebrew AI 2025 - API Test Suite                  ║', 'cyan');
        tester.log('╚════════════════════════════════════════════════════════════╝\n', 'cyan');

        const timestamp = Date.now();
        const email = `test${timestamp}@example.com`;
        const username = `testuser${timestamp}`;
        const password = process.env.TEST_PWD;

        await tester.section('Health Check', async () => {
            const { status, data } = await tester.request('GET', '/health');
            tester.test('Server is running', status === 200);
            tester.test('Health status is OK', data?.status === 'OK');
        });

        await tester.section('Authentication', async () => {
            const { status: regStatus, data: regData } = await tester.request('POST', '/auth/register', {
                email,
                username,
                password,
                confirmPassword: password,
                firstName: 'Test',
                lastName: 'User',
            });

            tester.test('Register successful', regStatus === 201);
            tester.test('Register returns user id', typeof regData?.id === 'string');
            tester.test('Register does not return access token', !Object.prototype.hasOwnProperty.call(regData || {}, 'token'));

            if (regData?.id) {
                tester.userId = regData.id;
            }

            const { status: verifyStatus, data: verifyData } = await tester.request('GET', '/auth/verify');
            tester.test('Session verification successful', verifyStatus === 200);
            tester.test('Session authenticated', verifyData?.authenticated === true);

            await tester.request('POST', '/auth/logout');

            const { status: loginStatus, data: loginData } = await tester.request('POST', '/auth/login', {
                email,
                password,
            });

            tester.test('Login successful', loginStatus === 200);
            tester.test('Login returns user id', typeof loginData?.id === 'string');

            const { status: wrongPassStatus } = await tester.request('POST', '/auth/login', {
                email,
                password: 'WrongPass#2026',
            });
            tester.test('Wrong password rejected', wrongPassStatus === 401 || wrongPassStatus === 423);
        });

        await tester.section('User Management', async () => {
            const { status: profileStatus, data: profileData } = await tester.request('GET', '/users/profile');
            tester.test('Get profile successful', profileStatus === 200);
            tester.test('Profile contains user data', typeof profileData?.user?.id === 'string');
            tester.test('Profile does not contain password', profileData?.user?.password === undefined);

            const { status: updateStatus } = await tester.request('PUT', '/users/profile', {
                firstName: 'Updated',
                lastName: 'Name',
            });
            tester.test('Update profile successful', updateStatus === 200);

            const { status: leaderStatus, data: leaderData } = await tester.request('GET', '/users/stats/leaderboard?limit=5');
            tester.test('Get leaderboard successful', leaderStatus === 200);
            tester.test('Leaderboard returns array', Array.isArray(leaderData?.leaderboard));
        });

        await tester.section('Lessons', async () => {
            const { status: lessonsStatus, data: lessonsData } = await tester.request('GET', '/lessons');
            tester.test('Get all lessons successful', lessonsStatus === 200);
            tester.test('Returns lessons array', Array.isArray(lessonsData?.lessons));

            if (Array.isArray(lessonsData?.lessons) && lessonsData.lessons.length > 0) {
                const lessonId = lessonsData.lessons[0].id;

                const { status: singleStatus } = await tester.request('GET', `/lessons/${lessonId}`);
                tester.test('Get single lesson successful', singleStatus === 200);

                const { status: completeStatus, data: completeData } = await tester.request('POST', `/lessons/${lessonId}/complete`);
                tester.test('Complete lesson successful', completeStatus === 200);
                tester.test('Lesson completion returns xpEarned', typeof completeData?.xpEarned === 'number');
            }

            const { status: diffStatus } = await tester.request('GET', '/lessons?difficulty=beginner');
            tester.test('Filter by difficulty successful', diffStatus === 200);
        });

        await tester.section('Quizzes', async () => {
            const { status: quizzesStatus, data: quizzesData } = await tester.request('GET', '/quizzes');
            tester.test('Get all quizzes successful', quizzesStatus === 200);
            tester.test('Returns quizzes array', Array.isArray(quizzesData?.quizzes));

            if (Array.isArray(quizzesData?.quizzes) && quizzesData.quizzes.length > 0) {
                const quizId = quizzesData.quizzes[0].id;

                const { status: singleStatus } = await tester.request('GET', `/quizzes/${quizId}`);
                tester.test('Get single quiz successful', singleStatus === 200);

                const { status: submitStatus, data: submitData } = await tester.request('POST', `/quizzes/${quizId}/submit`, {
                    answers: [0],
                });

                tester.test('Submit quiz returns contract status', submitStatus === 200 || submitStatus === 400);

                if (submitStatus === 200) {
                    tester.test('Submit returns attempt payload', !!submitData?.attempt);
                    tester.test('Submit returns numeric score', typeof submitData?.attempt?.score === 'number');
                }

                const { status: attemptsStatus, data: attemptsData } = await tester.request('GET', `/quizzes/${quizId}/attempts`);
                tester.test('Get quiz attempts endpoint', attemptsStatus === 200);
                tester.test('Quiz attempts is array', Array.isArray(attemptsData?.attempts));
            }
        });

        await tester.section('Dictionary', async () => {
            const { status: dictStatus, data: dictData } = await tester.request('GET', '/dictionary');
            tester.test('Get dictionary successful', dictStatus === 200);
            tester.test('Dictionary returns array', Array.isArray(dictData?.words));

            const { status: searchStatus, data: searchData } = await tester.request('GET', '/dictionary?q=shalom');
            tester.test('Dictionary search successful', searchStatus === 200);
            tester.test('Dictionary search returns array', Array.isArray(searchData?.words));
        });

        await tester.section('Progress', async () => {
            const { status: progressStatus, data: progressData } = await tester.request('GET', '/progress');
            tester.test('Get progress successful', progressStatus === 200);
            tester.test('Progress contains payload', !!progressData?.progress);

            const { status: summaryStatus, data: summaryData } = await tester.request('GET', '/progress/stats/summary');
            tester.test('Get summary successful', summaryStatus === 200);
            tester.test('Summary contains quiz stats', typeof summaryData?.stats?.quizzesCompleted === 'number');

            const { status: comparisonStatus } = await tester.request('GET', '/progress/stats/comparison');
            tester.test('Get comparison successful', comparisonStatus === 200);
        });

        tester.summary();
        process.exit(tester.failedCount > 0 ? 1 : 0);
    } catch (error) {
        tester.log(`\nFatal Error: ${error.message}`, 'red');
        process.exit(1);
    }
})();
