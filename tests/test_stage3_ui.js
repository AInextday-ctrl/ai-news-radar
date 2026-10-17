const fs = require('fs');
const vm = require('vm');

const appJs = fs.readFileSync('public/js/app.js', 'utf8');

// Minimal mock DOM environment
const context = {
    document: {
        documentElement: { lang: 'en', classList: { add: () => {}, remove: () => {} } },
        addEventListener: () => {},
        getElementById: (id) => ({
            innerHTML: '',
            innerText: '',
            value: '',
            style: {},
            classList: { add: () => {}, remove: () => {}, contains: () => false },
            setAttribute: () => {},
            getAttribute: () => '',
            appendChild: () => {},
            addEventListener: () => {}
        }),
        querySelectorAll: () => [],
        querySelector: () => null,
        createElement: (tag) => ({
            innerHTML: '',
            style: {},
            classList: { add: () => {}, remove: () => {} },
            setAttribute: () => {}
        })
    },
    localStorage: {
        getItem: () => null,
        setItem: () => {}
    },
    URLSearchParams: URLSearchParams,
    window: {
        addEventListener: () => {},
        location: { search: '' },
        matchMedia: () => ({ matches: false, addEventListener: () => {} })
    },
    setInterval: () => 1,
    clearInterval: () => {},
    setTimeout: () => 1,
    clearTimeout: () => {},
    navigator: { clipboard: { writeText: () => Promise.resolve() } },
    console: { log: console.log, warn: console.warn, error: console.error }
};

vm.createContext(context);
try {
    vm.runInContext(appJs, context);
    console.log('✅ app.js parsed and initialized in VM successfully!');
    
    // Test onPromptVarInput
    if (typeof context.onPromptVarInput === 'function') {
        console.log('✅ onPromptVarInput function exists!');
    } else {
        throw new Error('onPromptVarInput function missing');
    }

    // Test jumpToLLMWithPrompt
    if (typeof context.jumpToLLMWithPrompt === 'function') {
        console.log('✅ jumpToLLMWithPrompt function exists!');
    } else {
        throw new Error('jumpToLLMWithPrompt function missing');
    }

    // Test copyToolQuickstartCmd
    if (typeof context.copyToolQuickstartCmd === 'function') {
        console.log('✅ copyToolQuickstartCmd function exists!');
    } else {
        throw new Error('copyToolQuickstartCmd function missing');
    }

    // Test switchHomeToolFilter
    if (typeof context.switchHomeToolFilter === 'function') {
        console.log('✅ switchHomeToolFilter function exists!');
    } else {
        throw new Error('switchHomeToolFilter function missing');
    }

    console.log('🎉 ALL STAGE 3 UI FUNCTIONS VERIFIED IN VM!');
} catch (e) {
    console.error('❌ Stage 3 VM test failed:', e);
    process.exit(1);
}
