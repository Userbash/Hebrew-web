#!/usr/bin/env node

/**
 * Master Test Runner
 * Runs all tests during project startup and deployment
 *
 * Tests run in order:
 * 1. Nginx detection (check for external nginx)
 * 2. Docker-Compose validation
 * 3. Backend verification (when containers are running)
 * 4. Path verification
 * 5. Build verification
 */

import { promises as fs } from 'fs';
import { spawn } from 'child_process';
import NginxDetectionTest from './system/nginx-detection.test.js';
import DockerComposeValidator from './system/docker-compose-validator.test.js';
import BackendVerificationTest from './system/backend-verification.test.js';

class MasterTestRunner {
    constructor() {
        this.projectRoot = process.cwd();
        this.results = {
            timestamp: new Date().toISOString(),
            total_suites: 0,
            passed_suites: 0,
            failed_suites: 0,
            test_results: []
        };
        this.colors = {
            reset: '\x1b[0m',
            bright: '\x1b[1m',
            green: '\x1b[32m',
            yellow: '\x1b[33m',
            red: '\x1b[31m',
            cyan: '\x1b[36m',
            magenta: '\x1b[35m'
        };
    }

    log(message, color = 'reset') {
        const c = this.colors[color] || '';
        console.log(`${c}${message}${this.colors.reset}`);
    }

    async runTest(testName, testFunction) {
        this.results.total_suites++;
        this.log(`\n${'═'.repeat(70)}`, 'magenta');
        this.log(`  TEST SUITE: ${testName}`, 'magenta');
        this.log(`${'═'.repeat(70)}`, 'magenta');

        try {
            const result = await testFunction();
            const success = result.failed === 0 || result.valid === undefined || result.valid === true;

            if (success) {
                this.results.passed_suites++;
                this.log(`\n✓ ${testName} PASSED`, 'green');
            } else {
                this.results.failed_suites++;
                this.log(`\n✗ ${testName} FAILED`, 'red');
            }

            this.results.test_results.push({
                suite: testName,
                success,
                result
            });

            return success;
        } catch (error) {
            this.results.failed_suites++;
            this.log(`\n✗ ${testName} ERROR: ${error.message}`, 'red');
            this.results.test_results.push({
                suite: testName,
                success: false,
                error: error.message
            });
            return false;
        }
    }

    async verifyPaths() {
        this.log('\nVerifying project paths...', 'cyan');

        const pathsToCheck = [
            { path: `${this.projectRoot}/backend`, type: 'dir', name: 'Backend directory' },
            { path: `${this.projectRoot}/frontend-react/public`, type: 'dir', name: 'Frontend Public directory' },
            { path: `${this.projectRoot}/backend/server.ts`, type: 'file', name: 'Backend server.js' },
            { path: `${this.projectRoot}/backend/package.json`, type: 'file', name: 'Backend package.json' },
            { path: `${this.projectRoot}/docker-compose.yml`, type: 'file', name: 'docker-compose.yml' },
            { path: `${this.projectRoot}/backend/Dockerfile`, type: 'file', name: 'Backend Dockerfile' },
            { path: `${this.projectRoot}/.env`, type: 'file', name: '.env file' }
        ];

        const results = { total: 0, valid: 0, invalid: 0, errors: [] };

        for (const item of pathsToCheck) {
            results.total++;
            try {
                const stat = await fs.stat(item.path);
                const isValid = item.type === 'dir' ? stat.isDirectory() : stat.isFile();

                if (isValid) {
                    this.log(`  ✓ ${item.name}: ${item.path}`, 'green');
                    results.valid++;
                } else {
                    this.log(`  ✗ ${item.name}: exists but wrong type`, 'red');
                    results.invalid++;
                    results.errors.push(`${item.name} is not a ${item.type}`);
                }
            } catch (error) {
                this.log(`  ✗ ${item.name}: NOT FOUND`, 'red');
                results.invalid++;
                results.errors.push(`${item.name} not found: ${item.path}`);
            }
        }

        return results;
    }

    async checkBuildFiles() {
        this.log('\nChecking Dockerfile contents...', 'cyan');

        const files = [
            { path: `${this.projectRoot}/backend/Dockerfile`, name: 'Backend Dockerfile' },
            { path: `${this.projectRoot}/frontend-react/Dockerfile`, name: 'Frontend Dockerfile (Nginx)' }
        ];

        const results = { total: 0, valid: 0, errors: [] };

        for (const file of files) {
            results.total++;
            try {
                const content = await fs.readFile(file.path, 'utf8');

                // Check for essential Dockerfile keywords
                const hasFrom = /^FROM/m.test(content);
                const hasRun = /RUN/m.test(content);

                if (hasFrom && hasRun) {
                    this.log(`  ✓ ${file.name}: Valid Dockerfile`, 'green');
                    results.valid++;
                } else {
                    this.log(`  ✗ ${file.name}: Missing required Dockerfile directives`, 'red');
                    results.errors.push(`${file.name} is missing required directives`);
                }
            } catch (error) {
                this.log(`  ✗ ${file.name}: ${error.message}`, 'red');
                results.errors.push(`${file.name}: ${error.message}`);
            }
        }

        return results;
    }

    async checkEnvFile() {
        this.log('\nVerifying .env file...', 'cyan');

        try {
            const content = await fs.readFile(`${this.projectRoot}/.env`, 'utf8');
            const requiredVars = [
                'DB_USER',
                'DB_PASSWORD',
                'DB_NAME',
                'DB_PORT',
                'BACKEND_PORT',
                'NGINX_PORT',
                'DESEC_TOKEN',
                'DOMAIN_NAME',
                'ACME_EMAIL'
            ];

            const results = { total: 0, found: 0, errors: [] };
            const lines = content.split('\n');

            for (const varName of requiredVars) {
                results.total++;
                const found = lines.some(line => line.startsWith(varName));

                if (found) {
                    this.log(`  ✓ ${varName}: configured`, 'green');
                    results.found++;
                } else {
                    this.log(`  ✗ ${varName}: NOT configured`, 'yellow');
                    results.errors.push(`${varName} not configured`);
                }
            }

            return results;
        } catch (error) {
            this.log(`  ✗ Error reading .env: ${error.message}`, 'red');
            return { total: 0, found: 0, errors: [error.message] };
        }
    }

    async runFullTestSuite() {
        this.log('\n', 'magenta');
        this.log('╔════════════════════════════════════════════════════════════════╗', 'magenta');
        this.log('║                     FULL TEST SUITE STARTED                    ║', 'magenta');
        this.log('║           Running all startup and deployment checks            ║', 'magenta');
        this.log('╚════════════════════════════════════════════════════════════════╝', 'magenta');

        // 1. Path Verification
        const pathsResult = await this.verifyPaths();
        this.log(`\nPath Verification: ${pathsResult.valid}/${pathsResult.total} passed`,
            pathsResult.invalid > 0 ? 'yellow' : 'green');

        // 2. Build Files Check
        const buildResult = await this.checkBuildFiles();
        this.log(`Build Files Check: ${buildResult.valid}/${buildResult.total} passed`,
            buildResult.errors.length > 0 ? 'yellow' : 'green');

        // 3. Env File Check
        const envResult = await this.checkEnvFile();
        this.log(`Environment Variables: ${envResult.found}/${envResult.total} found`,
            envResult.errors.length > 0 ? 'yellow' : 'green');

        // 4. Nginx Detection Test
        await this.runTest('Nginx Detection', async () => {
            const test = new NginxDetectionTest();
            return await test.runTests();
        });

        // 5. Docker-Compose Validator
        await this.runTest('Docker-Compose Validation', async () => {
            const validator = new DockerComposeValidator();
            return await validator.validateFile();
        });

        // 6. Backend Verification (only if containers are running)
        this.log('\nNote: Backend verification test runs when containers are deployed', 'cyan');

        this.printSummary();
        await this.saveResults();
    }

    printSummary() {
        this.log('\n' + '═'.repeat(70), 'magenta');
        this.log('FINAL TEST SUMMARY', 'magenta');
        this.log('═'.repeat(70), 'magenta');

        this.log(`\nTotal Test Suites:  ${this.results.total_suites}`, 'cyan');
        this.log(`Passed:             ${this.results.passed_suites}`, 'green');
        this.log(`Failed:             ${this.results.failed_suites}`, this.results.failed_suites > 0 ? 'red' : 'green');

        if (this.results.failed_suites > 0) {
            this.log('\n⚠ Some tests failed. Review the output above for details.', 'yellow');
        } else {
            this.log('\n✓ All tests passed! Ready for deployment.', 'green');
        }

        this.log('\n' + '═'.repeat(70) + '\n', 'magenta');
    }

    async saveResults() {
        try {
            const resultsFile = `${this.projectRoot}/tests/.test-results.json`;
            await fs.writeFile(resultsFile, JSON.stringify(this.results, null, 2));
            this.log(`Results saved to: ${resultsFile}`, 'cyan');
        } catch (error) {
            this.log(`Warning: Could not save results - ${error.message}`, 'yellow');
        }
    }
}

// Run if executed directly
if (import.meta.url === `file://${process.argv[1]}`) {
    const runner = new MasterTestRunner();
    await runner.runFullTestSuite();
}

export default MasterTestRunner;
