/**
 * Docker Compose Configuration Validator
 * Tests docker-compose.yml for:
 * - Syntax correctness
 * - Path validity
 * - Service definitions
 * - Volume configurations
 * - Network setup
 * - Build configuration
 */

import { promises as fs } from 'fs';
import { resolve } from 'path';
import YAML from 'yaml';

class DockerComposeValidator {
    constructor(composePath = 'docker-compose.yml') {
        this.composePath = composePath;
        this.projectRoot = process.cwd();
        this.results = {
            valid: true,
            warnings: [],
            errors: [],
            checks: {}
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

    async validateFile() {
        this.log('\n' + '═'.repeat(70), 'cyan');
        this.log('  DOCKER COMPOSE CONFIGURATION VALIDATOR', 'cyan');
        this.log('═'.repeat(70) + '\n', 'cyan');

        try {
            const content = await fs.readFile(this.composePath, 'utf8');
            this.log(`1. Parsing ${this.composePath}...`, 'bright');

            // Try to parse as YAML
            let config;
            try {
                config = YAML.parse(content);
                this.log('   ✓ YAML syntax is valid', 'green');
                this.results.checks.yaml_syntax = true;
            } catch (error) {
                this.log(`   ✗ YAML syntax error: ${error.message}`, 'red');
                this.results.valid = false;
                this.results.checks.yaml_syntax = false;
                this.results.errors.push(`YAML Syntax: ${error.message}`);
                return this.results;
            }

            // Validate version
            this.log('\n2. Validating docker-compose structure...', 'bright');
            if (config.version) {
                this.log(`   ✓ Version: ${config.version}`, 'green');
                this.results.checks.version = true;
            } else {
                this.log('   ✗ No version specified', 'yellow');
                this.results.warnings.push('No version specified in docker-compose.yml');
            }

            // Validate services
            if (config.services && Object.keys(config.services).length > 0) {
                this.log(`   ✓ Services defined: ${Object.keys(config.services).join(', ')}`, 'green');
                this.results.checks.services = true;
                this.results.services = Object.keys(config.services);
            } else {
                this.log('   ✗ No services defined', 'red');
                this.results.valid = false;
                this.results.errors.push('No services defined in docker-compose.yml');
            }

            // Validate volumes
            this.log('\n3. Validating volumes...', 'bright');
            await this.validateVolumes(config);

            // Validate services details
            this.log('\n4. Validating service configurations...', 'bright');
            await this.validateServices(config);

            // Validate build contexts
            this.log('\n5. Validating build contexts...', 'bright');
            await this.validateBuildContexts(config);

            // Validate networks
            this.log('\n6. Validating networks...', 'bright');
            if (config.networks) {
                this.log(`   ✓ Networks defined: ${Object.keys(config.networks).join(', ')}`, 'green');
                this.results.checks.networks = true;
            } else {
                this.log('   ✗ No networks defined', 'yellow');
            }

        } catch (error) {
            this.log(`   ✗ Error reading file: ${error.message}`, 'red');
            this.results.valid = false;
            this.results.errors.push(`File read error: ${error.message}`);
        }

        // Summary
        this.log('\n' + '─'.repeat(70), 'cyan');
        this.log('VALIDATION SUMMARY', 'bright');
        this.log('─'.repeat(70), 'cyan');

        if (this.results.valid) {
            this.log('✓ Docker-Compose configuration is VALID', 'green');
        } else {
            this.log('✗ Docker-Compose configuration has ERRORS', 'red');
        }

        if (this.results.errors.length > 0) {
            this.log('\nErrors:', 'red');
            this.results.errors.forEach(err => {
                this.log(`  ✗ ${err}`, 'red');
            });
        }

        if (this.results.warnings.length > 0) {
            this.log('\nWarnings:', 'yellow');
            this.results.warnings.forEach(warn => {
                this.log(`  ⚠ ${warn}`, 'yellow');
            });
        }

        this.log('\n' + '═'.repeat(70) + '\n', 'cyan');

        return this.results;
    }

    async validateVolumes(config) {
        if (!config.volumes) {
            this.log('   ⚠ No volumes defined at root level', 'yellow');
            this.results.warnings.push('No volumes defined');
            return;
        }

        this.log(`   Defined volumes: ${Object.keys(config.volumes).length}`, 'cyan');

        for (const [volumeName, volumeConfig] of Object.entries(config.volumes)) {
            if (volumeConfig && volumeConfig.driver_opts && volumeConfig.driver_opts.device) {
                const device = volumeConfig.driver_opts.device;
                const actualPath = device.replace('${DOCKER_DATA_PATH:-./data}', `${this.projectRoot}/data`);

                // Check if path exists or can be created
                try {
                    await fs.access(actualPath);
                    this.log(`   ✓ ${volumeName}: ${device}`, 'green');
                } catch (error) {
                    this.log(`   ⚠ ${volumeName}: path may need creation - ${device}`, 'yellow');
                    this.results.warnings.push(`Volume path for ${volumeName} may need creation`);
                }
            } else {
                this.log(`   ✓ ${volumeName}: managed volume`, 'green');
            }
        }

        this.results.checks.volumes = true;
    }

    async validateServices(config) {
        if (!config.services) return;

        for (const [serviceName, serviceConfig] of Object.entries(config.services)) {
            this.log(`\n   Service: ${serviceName}`, 'cyan');

            // Check image or build
            if (serviceConfig.image) {
                this.log(`     ✓ Image: ${serviceConfig.image}`, 'green');
            } else if (serviceConfig.build) {
                this.log(`     ✓ Build context: ${serviceConfig.build.context || serviceConfig.build}`, 'green');
            } else {
                this.log(`     ✗ No image or build definition`, 'red');
                this.results.valid = false;
            }

            // Check healthcheck
            if (serviceConfig.healthcheck) {
                this.log(`     ✓ Healthcheck configured`, 'green');
            } else if (['postgres', 'redis', 'elasticsearch', 'backend'].includes(serviceName)) {
                this.log(`     ⚠ No healthcheck (recommended for ${serviceName})`, 'yellow');
                this.results.warnings.push(`No healthcheck for ${serviceName}`);
            }

            // Check ports
            if (serviceConfig.ports && serviceConfig.ports.length > 0) {
                this.log(`     ✓ Ports: ${serviceConfig.ports.join(', ')}`, 'green');
            }

            // Check depends_on
            if (serviceConfig.depends_on && Object.keys(serviceConfig.depends_on).length > 0) {
                this.log(`     ✓ Depends on: ${Object.keys(serviceConfig.depends_on).join(', ')}`, 'green');
            }
        }

        this.results.checks.services_detail = true;
    }

    async validateBuildContexts(config) {
        if (!config.services) return;

        for (const [serviceName, serviceConfig] of Object.entries(config.services)) {
            if (serviceConfig.build && typeof serviceConfig.build === 'object' && serviceConfig.build.context) {
                const contextPath = resolve(this.projectRoot, serviceConfig.build.context);
                try {
                    await fs.access(contextPath);
                    this.log(`   ✓ ${serviceName}: ${serviceConfig.build.context}`, 'green');
                } catch (error) {
                    this.log(`   ✗ ${serviceName}: context path not found - ${serviceConfig.build.context}`, 'red');
                    this.results.valid = false;
                    this.results.errors.push(`Build context for ${serviceName} not found`);
                }

                // Check Dockerfile
                if (serviceConfig.build.dockerfile) {
                    const dockerfilePath = resolve(contextPath, serviceConfig.build.dockerfile);
                    try {
                        await fs.access(dockerfilePath);
                        this.log(`     ✓ Dockerfile: ${serviceConfig.build.dockerfile}`, 'green');
                    } catch (error) {
                        this.log(`     ✗ Dockerfile not found: ${serviceConfig.build.dockerfile}`, 'red');
                        this.results.valid = false;
                    }
                }
            }
        }

        this.results.checks.build_contexts = true;
    }
}

// Helper: Simple YAML parser (fallback if yaml module not available)
const SimpleYAMLParser = {
    parse: (content) => {
        try {
            const lines = content.split('\n');
            const result = {};
            let currentKey = null;
            let indent = 0;

            lines.forEach(line => {
                const match = line.match(/^(\s*)(\w+):\s*(.*)?$/);
                if (match) {
                    const [, spaces, key, value] = match;
                    currentKey = key;
                    result[key] = value || {};
                }
            });

            return result;
        } catch (error) {
            throw new Error(`YAML Parse Error: ${error.message}`);
        }
    }
};

// Run if executed directly
if (import.meta.url === `file://${process.argv[1]}`) {
    const validator = new DockerComposeValidator();
    const results = await validator.validateFile();
    process.exit(results.valid ? 0 : 1);
}

export default DockerComposeValidator;
