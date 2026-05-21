import eslint from '@eslint/js';
import globals from 'globals';

export default [
    { ignores: ['node_modules/**', 'public/**', 'dist/**'] },
    eslint.configs.recommended,
    {
        languageOptions: {
            ecmaVersion: 12, // or 'latest'
            sourceType: 'module',
            globals: {
                ...globals.node,
                // No browser globals needed for backend
            },
        },
        rules: {
            'indent': [
                'error',
                4
            ],
            'linebreak-style': [
                'error',
                'unix'
            ],
            'quotes': [
                'error',
                'single'
            ],
            'semi': [
                'error',
                'always'
            ],
            'no-unused-vars': [
                'warn',
                { 'argsIgnorePattern': '^_|^req|^res|^next' }
            ],
            'no-console': 'warn'
        }
    }
];