"use strict";

document.addEventListener('DOMContentLoaded', function () {
    var hamburger = document.getElementById('hamburger');
    var hamburgerState = false;

    hamburger.onclick = function () {
        hamburgerState = !hamburgerState;

        if (hamburgerState) {
            hamburger.classList.add('open');
        } else {
            hamburger.classList.remove('open');
        }
    };
}, false);
