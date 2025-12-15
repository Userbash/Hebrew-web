#!/usr/bin/env node

/**
 * Quick API Test Suite - Hebrew AI 2025
 * Tests all major endpoints
 */

import fetch from 'node-fetch';

const BASE_URL = 'http://127.0.0.1:3001/api';

const colors = {
    reset: '\x1b[0m',
    green: '\x1b[32m',
    red: '\x1b[31m',
    yellow: '\x1b[33m',
    blue: '\x1b[34m',
    cyan: '\x1b[36m'
};

class APITest {
    constructor() {
        this.token = null;
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
        const options = {
            method,
            headers: { 'Content-Type': 'application/json' }
        };

        if (this.token) {
            options.headers.Authorization = `Bearer ${this.token}`;
        }

        if (body) {
            options.body = JSON.stringify(body);
        }

        try {
            const response = await fetch(`${BASE_URL}${endpoint}`, options);
            const data = await response.json();
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
        const percent = Math.round((this.passed / this.total) * 100);
        this.log(`Success Rate: ${percent}%\n`, percent === 100 ? 'green' : 'yellow');
        this.log('═'.repeat(60), 'blue');
    }
}

async function runTests() {
    const test = new APITest();

    test.log('\n╔════════════════════════════════════════════════════════════╗', 'cyan');
    test.log('║      Hebrew AI 2025 - Quick API Test Suite                 ║', 'cyan');
    test.log('╚════════════════════════════════════════════════════════════╝', 'cyan');

    try {
        // Health Check
        await test.section('Health Check');
        const health = await test.request('GET', '/health');
        test.assert('Server is running', health.ok && health.data.status === 'OK');

        // Registration
        await test.section('Authentication');
        const timestamp = Date.now();
        const reg = await test.request('POST', '/auth/register', {
            email: `user${timestamp}@example.com`,
            password: 'password123',
            firstName: 'Test',
            lastName: 'User'
        });
        test.assert('User registration', reg.ok && reg.data.user);
        if (reg.data.token) {
            test.token = reg.data.token;
        }

        // Login
        const login = await test.request('POST', '/auth/login', {
            email: `user${timestamp}@example.com`,
            password: 'password123'
        });
        test.assert('User login', login.ok && login.data.token);

        // Token verification
        const verify = await test.request('GET', '/auth/verify');
        test.assert('Token verification', verify.ok);

        // Users
        await test.section('User Management');
        const profile = await test.request('GET', '/users/profile');
        test.assert('Get profile', profile.ok && profile.data.user);

        const leaderboard = await test.request('GET', '/users/stats/leaderboard?limit=5');
        test.assert('Get leaderboard', leaderboard.ok && Array.isArray(leaderboard.data.leaderboard));

        // Lessons
        await test.section('Lessons');
        const lessons = await test.request('GET', '/lessons');
        test.assert('Get lessons', lessons.ok && Array.isArray(lessons.data.lessons));

        if (lessons.data.lessons.length > 0) {
            const lessonId = lessons.data.lessons[0].id;
            const getLesson = await test.request('GET', `/lessons/${lessonId}`);
            test.assert('Get single lesson', getLesson.ok);

            const complete = await test.request('POST', `/lessons/${lessonId}/complete`);
            test.assert('Complete lesson', complete.ok);
        }

        // Quizzes
        await test.section('Quizzes');
        const quizzes = await test.request('GET', '/quizzes');
        test.assert('Get quizzes', quizzes.ok && Array.isArray(quizzes.data.quizzes));

        if (quizzes.data.quizzes.length > 0) {
            const quizId = quizzes.data.quizzes[0].id;
            const getQuiz = await test.request('GET', `/quizzes/${quizId}`);
            test.assert('Get single quiz', getQuiz.ok);

            const submit = await test.request('POST', `/quizzes/${quizId}/submit`, {
                answers: [0, 1, 0]
            });
            test.assert('Submit quiz', submit.ok);
        }

        // Dictionary
        await test.section('Dictionary');
        const dict = await test.request('GET', '/dictionary');
        test.assert('Get dictionary', dict.ok && Array.isArray(dict.data.words));

        const search = await test.request('GET', '/dictionary?q=shalom');
        test.assert('Search dictionary', search.ok && Array.isArray(search.data.words));

        // Progress
        await test.section('Progress');
        const progress = await test.request('GET', '/progress');
        test.assert('Get progress', progress.ok && progress.data.progress);

        const summary = await test.request('GET', '/progress/stats/summary');
        test.assert('Get progress summary', summary.ok && summary.data.stats);

        const comparison = await test.request('GET', '/progress/stats/comparison');
        test.assert('Get progress comparison', comparison.ok);

        // Summary
        test.summary();
        process.exit(test.failed > 0 ? 1 : 0);

    } catch (error) {
        test.log(`\nFatal Error: ${error.message}`, 'red');
        console.error(error);
        process.exit(1);
    }
}

runTests();
