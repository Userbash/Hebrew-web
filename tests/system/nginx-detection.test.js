/**
 * Nginx Port Detection and External Nginx Handling Tests
 * Runs on project launch to check for external nginx on standard ports
 *
 * Ports checked:
 * - 80 (HTTP)
 * - 443 (HTTPS)
 */

import { promises as fs } from 'fs';
import { spawn } from 'child_process';

class NginxDetectionTest {
    constructor() {
        this.ports = [80, 443];
        this.results = {
            nginx_found: false,
            external_nginx: false,
            ports_in_use: [],
            recommendations: []
        };
        this.colors = {
            reset: '\x1b[0m',
            bright: '\x1b[1m',
            green: '\x1b[32m',
            yellow: '\x1b[33m',
            red: '\x1b[31m',
            cyan: '\x1b[36m'
        };
    }

    log(message, color = 'reset') {
        const c = this.colors[color] || '';
        console.log(`${c}${message}${this.colors.reset}`);
    }

    async checkPort(port) {
        return new Promise((resolve) => {
            const nc = spawn('nc', ['-zv', 'localhost', String(port)], {
                timeout: 2000,
                stdio: 'pipe'
            });

            let timeout = setTimeout(() => {
                nc.kill();
                resolve(false);
            }, 2000);

            nc.on('close', (code) => {
                clearTimeout(timeout);
                // nc returns 0 if port is open, non-zero if closed
                resolve(code === 0);
            });

            nc.on('error', () => {
                clearTimeout(timeout);
                resolve(false);
            });
        });
    }

    async checkPortWithNetstat(port) {
        return new Promise((resolve) => {
            const netstat = spawn('ss', ['-tuln'], { stdio: 'pipe' });
            let output = '';

            netstat.stdout.on('data', (data) => {
                output += data.toString();
            });

            netstat.on('close', () => {
                const portInUse = output.includes(`:${port}`);
                resolve(portInUse);
            });

            netstat.on('error', () => {
                resolve(false);
            });

            setTimeout(() => {
                netstat.kill();
                resolve(false);
            }, 3000);
        });
    }

    async detectNginxProcess() {
        return new Promise((resolve) => {
            const ps = spawn('ps', ['aux'], { stdio: 'pipe' });
            let output = '';

            ps.stdout.on('data', (data) => {
                output += data.toString();
            });

            ps.on('close', () => {
                const hasNginx = output.includes('nginx');
                resolve(hasNginx);
            });

            ps.on('error', () => {
                resolve(false);
            });
        });
    }

    async runTests() {
        this.log('\n' + '═'.repeat(70), 'cyan');
        this.log('  NGINX DETECTION AND EXTERNAL NGINX CHECK', 'cyan');
        this.log('═'.repeat(70) + '\n', 'cyan');

        // Check for running nginx process
        this.log('1. Checking for running Nginx process...', 'bright');
        const nginxRunning = await this.detectNginxProcess();
        if (nginxRunning) {
            this.log('   ✓ Nginx process detected on system', 'green');
            this.results.nginx_found = true;
        } else {
            this.log('   ✗ No Nginx process detected', 'yellow');
        }

        // Check standard ports
        this.log('\n2. Checking standard HTTP/HTTPS ports...', 'bright');
        for (const port of this.ports) {
            this.log(`   Checking port ${port}...`, 'cyan');
            const portInUse = await this.checkPortWithNetstat(port);

            if (portInUse) {
                this.log(`   ✓ Port ${port} is in use`, 'yellow');
                this.results.ports_in_use.push(port);
                this.results.external_nginx = true;
            } else {
                this.log(`   ✗ Port ${port} is free`, 'green');
            }
        }

        // Generate recommendations
        this.log('\n3. Recommendations:', 'bright');
        if (this.results.external_nginx) {
            this.log('   ⚠  EXTERNAL NGINX DETECTED!', 'red');
            this.log('   Ports in use: ' + this.results.ports_in_use.join(', '), 'yellow');
            this.results.recommendations = [
                '✓ External Nginx detected on ports: ' + this.results.ports_in_use.join(', '),
                '✓ Docker-Compose will run WITHOUT internal Nginx',
                '✓ Configure external Nginx to proxy to Docker containers:',
                '  - Backend API: http://localhost:3001',
                '  - Frontend: http://localhost:3000',
                '',
                'Example Nginx configuration:',
                '  upstream backend { server localhost:3001; }',
                '  upstream frontend { server localhost:3000; }',
                '',
                '  server {',
                '    listen 80;',
                '    server_name _;',
                '',
                '    location /api/ {',
                '      proxy_pass http://backend;',
                '      proxy_set_header Host $host;',
                '      proxy_set_header X-Real-IP $remote_addr;',
                '    }',
                '',
                '    location / {',
                '      proxy_pass http://frontend;',
                '      proxy_set_header Host $host;',
                '    }',
                '  }'
            ];
        } else {
            this.results.recommendations = [
                '✓ No external Nginx detected',
                '✓ Docker-Compose will run WITH internal Nginx',
                '✓ All services will be available through Nginx reverse proxy',
                '✓ Access application at: http://localhost'
            ];
        }

        this.results.recommendations.forEach(rec => {
            const color = rec.includes('⚠') ? 'red' : rec.includes('✓') ? 'green' : 'cyan';
            this.log('   ' + rec, color);
        });

        // Configuration decision
        this.log('\n4. Configuration Decision:', 'bright');
        const configFile = this.results.external_nginx
            ? 'docker-compose.minimal.yml'
            : 'docker-compose.yml';

        this.log(`   Using: ${configFile}`, 'green');
        this.results.config_file = configFile;

        // Save results
        await this.saveResults();

        this.log('\n' + '═'.repeat(70) + '\n', 'cyan');

        return this.results;
    }

    async saveResults() {
        const resultsFile = '/var/home/sanya/Hebrew-web/tests/.nginx-detection-results.json';
        try {
            await fs.writeFile(
                resultsFile,
                JSON.stringify(this.results, null, 2)
            );
            this.log(`Results saved to: ${resultsFile}`, 'cyan');
        } catch (error) {
            this.log(`Warning: Could not save results - ${error.message}`, 'yellow');
        }
    }
}

// Run tests if executed directly
if (import.meta.url === `file://${process.argv[1]}`) {
    const test = new NginxDetectionTest();
    const results = await test.runTests();
    process.exit(results.external_nginx ? 1 : 0);
}

export default NginxDetectionTest;
