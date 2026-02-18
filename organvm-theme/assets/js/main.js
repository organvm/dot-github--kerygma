// ORGANVM Ghost Theme — main.js
// Minimal JS: syntax highlighting via Prism.js (loaded from CDN if code blocks exist)

(function () {
    'use strict';

    // Load Prism.js for syntax highlighting if code blocks are present
    var codeBlocks = document.querySelectorAll('pre code');
    if (codeBlocks.length > 0) {
        var link = document.createElement('link');
        link.rel = 'stylesheet';
        link.href = 'https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/themes/prism-tomorrow.min.css';
        document.head.appendChild(link);

        var script = document.createElement('script');
        script.src = 'https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/prism.min.js';
        script.onload = function () {
            // Load common language plugins
            var languages = ['python', 'javascript', 'typescript', 'bash', 'yaml', 'json', 'rust', 'go'];
            languages.forEach(function (lang) {
                var langScript = document.createElement('script');
                langScript.src = 'https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/components/prism-' + lang + '.min.js';
                document.body.appendChild(langScript);
            });

            // Re-highlight after plugins load
            setTimeout(function () {
                Prism.highlightAll();
            }, 500);
        };
        document.body.appendChild(script);
    }
})();
