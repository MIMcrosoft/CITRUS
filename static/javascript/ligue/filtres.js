(function () {
    "use strict";

    var forms = document.querySelectorAll("form[data-auto-submit]");

    forms.forEach(function (form) {
        form.querySelectorAll("select").forEach(function (select) {
            select.addEventListener("change", function () {
                form.submit();
            });
        });
    });
})();