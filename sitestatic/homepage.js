"use strict";

(function() {
  const input = document.getElementById('pkgsearch-field');
  const form = document.getElementById('pkgsearch-form');
  var list;

  function resetResults() {
    if (!list) return;
    list.style.display = "none";
    list.innerHTML = "";
  }

  function getCompleteList() {
    if (!list) {
      list = document.createElement("UL");
      list.setAttribute("class", "pkgsearch-typeahead"); // remove
      form.appendChild(list);
      setListLocation();
    }
    return list;
  }

  function onListClick(e) {
      let target = e.target;
      while (!target.getAttribute('data-value')) {
        target = target.parentNode;
      }
      input.value = target.getAttribute('data-value');
      form.submit();
  }

  function setListLocation() {
    if (!list) return;
    const rects = input.getClientRects()[0];
    list.style.top = (rects.top + rects.height) + "px";
    list.style.left = rects.left + "px";
  }

  function loadData(data) {
    const letter = data[0];
    const pkgs = data[1].slice(0, 10); // Show maximum of 10 results

    resetResults();

    if (pkgs.length === 0) {
      return;
    }

    const ul = getCompleteList();
    ul.style.display = "block";
    const fragment = document.createDocumentFragment();

    for (let i = 0; i < pkgs.length; i++) {
      const item = document.createElement("li");
      const text = pkgs[i].replace(letter, '<b>' + letter + '</b>');
      item.innerHTML = '<a href="#">' + text + '</a>';
      item.setAttribute('data-value', pkgs[i]);
      fragment.appendChild(item);
    }

    ul.appendChild(fragment);
    ul.addEventListener('click', onListClick);
  }

  function fetchData(letter) {
    fetch('/opensearch/packages/suggest?q=' + letter).then(function(response) {
      return response.json();
    }).then(function(data) {
      loadData(data);
    });
  }

  function onInputClick() {
    if (input.value === "") {
      resetResults();
      return;
    }
    fetchData(input.value);
  }

  function onKeyDown(e) {
    if (!list) return;

    const elem = document.querySelector(".pkgsearch-typeahead li.active");
    switch(e.keyCode) {
      case 13: // enter
        if (elem) {
          input.value = elem.getAttribute('data-value');
          form.submit();
        } else {
          form.submit();
        }
        e.preventDefault();
        break;
      case 38: // up
        if (elem && elem.previousElementSibling) {
          elem.className = "";
          elem.previousElementSibling.className = "active";
        }
        e.preventDefault();
        break;
      case 40: // down
        if (elem && elem.nextElementSibling) {
          elem.className = "";
          elem.nextElementSibling.className = "active";
        } else if (!elem && list.childElementCount !== 0) {
          list.children[0].className = "active";
        }
        e.preventDefault();
        break;
    }
  }

  // debounce https://davidwalsh.name/javascript-debounce-function
  function debounce(func, wait, immediate) {
    var timeout;
    return function() {
      var context = this, args = arguments;
      var later = function() {
        timeout = null;
        if (!immediate) func.apply(context, args);
      };
      var callNow = immediate && !timeout;
      clearTimeout(timeout);
      timeout = setTimeout(later, wait);
      if (callNow) func.apply(context, args);
    };
  }

  input.addEventListener("input", onInputClick);
  input.addEventListener("keydown", onKeyDown);
  window.addEventListener('resize', debounce(setListLocation, 150));
  document.addEventListener("click", resetResults);
}());
