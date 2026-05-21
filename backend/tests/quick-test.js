#!/usr/bin/env node

/**
 * Quick API smoke suite.
 * Uses cookie-based auth to match production behavior.
 */

import fetch from 'node-fetch';

const BASE_URL = 'http://127.0.0.1:3001/api';

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
            const sep = pair.indexOf('=');
            if (sep <= 0) continue;
            const name = pair.slice(0, sep).trim();
            const value = pair.slice(sep + 1).trim();
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

class APITest {
    constructor() {
        this.jar = new CookieJar();
        this.passed = 0;
        this.failed = 0;
        this.total = 0;
    }

    log(msg, color = 'reset') {
        console.log(`${colors[color]}${msg}${colors.reset}`);
    }

    assert(name, condition) {
        this.total++;
        if (condition) {
            this.passed++;
            this.log(`✓ ${name}`, 'green');
        } else {
            this.failed++;
            this.log(`✗ ${name}`, 'red');
        }
    }

    async request(method, endpoint, body = null) {
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
            const response = await fetch(`${BASE_URL}${endpoint}`, options);
            const setCookies = response.headers.raw()['set-cookie'] || [];
            this.jar.merge(setCookies);

            const text = await response.text();
            let data = null;
            try {
                data = text ? JSON.parse(text) : null;
            } catch {
                data = null;
            }

            return { status: response.status, data, ok: response.ok };
        } catch (error) {
            return { status: 0, data: null, error: error.message, ok: false };
        }
    }

    async section(title) {
        this.log(`\n${title}`, 'cyan');
    }

    summary() {
        this.log(`\n${'═'.repeat(60)}`, 'blue');
        this.log(`Tests: ${this.total} | Passed: ${this.passed} | Failed: ${this.failed}`, 'cyan');
        const percent = this.total > 0 ? Math.round((this.passed / this.total) * 100) : 0;
        this.log(`Success Rate: ${percent}%\n`, percent === 100 ? 'green' : 'yellow');
        this.log('═'.repeat(60), 'blue');
    }
}

async function runTests() {
    const test = new APITest();

    test.log('\n╔════════════════════════════════════════════════════════════╗', 'cyan');
    test.log('║      Hebrew AI 2025 - Quick API Test Suite                ║', 'cyan');
    test.log('╚════════════════════════════════════════════════════════════╝', 'cyan');

    try {
        await test.section('Health Check');
        const health = await test.request('GET', '/health');
        test.assert('Server is running', health.ok && health.data?.status === 'OK');

        await test.section('Authentication');
        const timestamp = Date.now();
        const email = `user${timestamp}@example.com`;
        const username = `user${timestamp}`;
        const password = 'StrongPass#2026';

        const reg = await test.request('POST', '/auth/register', {
            email,
            username,
            password,
            confirmPassword: password,
            firstName: 'Test',
            lastName: 'User',
        });

        test.assert('User registration', reg.status === 201 && typeof reg.data?.id === 'string');
        test.assert('Register does not leak token in JSON', !Object.prototype.hasOwnProperty.call(reg.data || {}, 'token'));

        const verify = await test.request('GET', '/auth/verify');
        test.assert('Token verification via cookies', verify.ok && verify.data?.authenticated === true);

        await test.request('POST', '/auth/logout');

        const login = await test.request('POST', '/auth/login', { email, password });
        test.assert('User login', login.ok && typeof login.data?.id === 'string');

        const wrong = await test.request('POST', '/auth/login', { email, password: 'WrongPass#2026' });
        test.assert('Wrong password is rejected', wrong.status === 401 || wrong.status === 423);

        await test.section('User Management');
        const profile = await test.request('GET', '/users/profile');
        test.assert('Get profile', profile.ok && profile.data?.user?.id === login.data?.id);

        const leaderboard = await test.request('GET', '/users/stats/leaderboard?limit=5');
        test.assert('Get leaderboard', leaderboard.ok && Array.isArray(leaderboard.data?.leaderboard));

        await test.section('Lessons');
        const lessons = await test.request('GET', '/lessons');
        test.assert('Get lessons', lessons.ok && Array.isArray(lessons.data?.lessons));

        if (Array.isArray(lessons.data?.lessons) && lessons.data.lessons.length > 0) {
            const lessonId = lessons.data.lessons[0].id;
            const getLesson = await test.request('GET', `/lessons/${lessonId}`);
            test.assert('Get single lesson', getLesson.ok);

            const complete = await test.request('POST', `/lessons/${lessonId}/complete`);
            test.assert('Complete lesson', complete.ok);
        }

        await test.section('Quizzes');
        const quizzes = await test.request('GET', '/quizzes');
        test.assert('Get quizzes', quizzes.ok && Array.isArray(quizzes.data?.quizzes));

        if (Array.isArray(quizzes.data?.quizzes) && quizzes.data.quizzes.length > 0) {
            const quizId = quizzes.data.quizzes[0].id;
            const submit = await test.request('POST', `/quizzes/${quizId}/submit`, {
                answers: [0],
            });

            // Valid outcomes:
            // - 200 if quiz has answer key and grading works.
            // - 400 when quiz is present but answer key shape/count does not match.
            test.assert('Submit quiz (graded or validation error)', submit.status === 200 || submit.status === 400);

            const attempts = await test.request('GET', `/quizzes/${quizId}/attempts`);
            test.assert('Get quiz attempts endpoint', attempts.status === 200 || attempts.status === 404);
        }

        await test.section('Dictionary');
        const dict = await test.request('GET', '/dictionary');
        test.assert('Get dictionary', dict.ok && Array.isArray(dict.data?.words));

        const search = await test.request('GET', '/dictionary?q=shalom');
        test.assert('Search dictionary', search.ok && Array.isArray(search.data?.words));

        await test.section('Progress');
        const progress = await test.request('GET', '/progress');
        test.assert('Get progress', progress.ok && !!progress.data?.progress);

        const summary = await test.request('GET', '/progress/stats/summary');
        test.assert('Get progress summary', summary.ok && !!summary.data?.stats);

        const comparison = await test.request('GET', '/progress/stats/comparison');
        test.assert('Get progress comparison', comparison.ok);

        test.summary();
        process.exit(test.failed > 0 ? 1 : 0);
    } catch (error) {
        test.log(`\nFatal Error: ${error.message}`, 'red');
        console.error(error);
        process.exit(1);
    }
}

runTests();
