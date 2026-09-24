(function () {
    "use strict";

    var navbar = document.querySelector(".ligue-navbar");
    if (!navbar) {
        return;
    }

    var toggle = navbar.querySelector(".ligue-navbar__toggle");
    var menu = navbar.querySelector(".ligue-navbar__menu");
    var dropdownItems = Array.prototype.slice.call(
        navbar.querySelectorAll(".ligue-navbar__item--dropdown")
    );
    var desktopQuery = window.matchMedia("(width >= 64rem)");

    function closeDropdown(item) {
        item.classList.remove("is-open");
        var link = item.querySelector(".ligue-navbar__link");
        if (link) {
            link.setAttribute("aria-expanded", "false");
        }
    }

    function closeAllDropdowns(except) {
        dropdownItems.forEach(function (item) {
            if (item !== except) {
                closeDropdown(item);
            }
        });
    }

    function closeMenu() {
        if (!menu || !toggle) {
            return;
        }
        menu.classList.remove("is-open");
        toggle.setAttribute("aria-expanded", "false");
        closeAllDropdowns();
    }

    if (toggle && menu) {
        toggle.addEventListener("click", function () {
            var isOpen = menu.classList.toggle("is-open");
            toggle.setAttribute("aria-expanded", String(isOpen));
            if (!isOpen) {
                closeAllDropdowns();
            }
        });
    }

    dropdownItems.forEach(function (item) {
        var link = item.querySelector(".ligue-navbar__link");
        if (!link) {
            return;
        }
        link.addEventListener("click", function () {
            var willOpen = !item.classList.contains("is-open");
            closeAllDropdowns(item);
            item.classList.toggle("is-open", willOpen);
            link.setAttribute("aria-expanded", String(willOpen));
        });
    });

    document.addEventListener("click", function (event) {
        if (!navbar.contains(event.target)) {
            closeMenu();
        }
    });

    document.addEventListener("keydown", function (event) {
        if (event.key === "Escape") {
            closeMenu();
        }
    });

    desktopQuery.addEventListener("change", function () {
        closeMenu();
    });
})();
