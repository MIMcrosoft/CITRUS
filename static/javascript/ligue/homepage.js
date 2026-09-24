(function () {
    "use strict";

    var revealEls = document.querySelectorAll(".ligue-reveal");
    if (!revealEls.length) {
        return;
    }

    var prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (prefersReducedMotion || !("IntersectionObserver" in window)) {
        revealEls.forEach(function (el) {
            el.classList.add("is-visible");
        });
        return;
    }

    var observer = new IntersectionObserver(
        function (entries) {
            entries.forEach(function (entry) {
                if (entry.isIntersecting) {
                    entry.target.classList.add("is-visible");
                    observer.unobserve(entry.target);
                }
            });
        },
        { threshold: 0.15, rootMargin: "0px 0px -10% 0px" }
    );

    revealEls.forEach(function (el) {
        observer.observe(el);
    });
})();

(function () {
    "use strict";

    var tabs = document.querySelectorAll(".ligue-archives-tab");
    if (!tabs.length) {
        return;
    }

    var panels = document.querySelectorAll(".ligue-archives-panel");

    tabs.forEach(function (tab) {
        tab.addEventListener("click", function () {
            var division = tab.getAttribute("data-division");

            tabs.forEach(function (t) {
                var isActive = t === tab;
                t.classList.toggle("is-active", isActive);
                t.setAttribute("aria-selected", isActive ? "true" : "false");
            });

            panels.forEach(function (panel) {
                panel.classList.toggle("is-active", panel.getAttribute("data-division") === division);
            });
        });
    });
})();
