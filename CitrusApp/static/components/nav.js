//Get parameters from URL
function getParams() {
    var idx = document.URL.indexOf('?');
    var params = new Array();
    if (idx != -1) {
        var pairs = document.URL.substring(idx+1, document.URL.length).split('&');
        for (var i=0; i<pairs.length; i++) {
            nameVal = pairs[i].split('=');
            params[nameVal[0]] = nameVal[1];
        }
    }
    if (idx == -1) {
        params['animation'] = '0';
    }
    removeQueryParameter('exampleParam');
    return params;
}

function removeQueryParameter(param) {
    var url = window.location.protocol + "//" + window.location.host + window.location.pathname;
    window.history.replaceState({}, document.title, url);
}

function getBaseURL() {
    let currentURL = window.location.href;
    let lastSlashIndex = currentURL.lastIndexOf('/');
    let baseURL = currentURL.substring(0, lastSlashIndex+1);
  
    return baseURL;
  }
  



let params = getParams();
let loadAnimation = params['animation'];

//Page Loading Animation
function placeSelector(el) {
    const fromTop = el.getBoundingClientRect().top;
    const selector = document.getElementById("selector");
    selector.style.top = fromTop + "px";
}

//if reload or no info
if (loadAnimation == 0) {
    const primaryNav = document.getElementById("primaryNav");
    primaryNav.classList.add("skipTransition");
    primaryNav.classList.remove("hover");
    setTimeout(function() {
        primaryNav.classList.remove("skipTransition");
    }, 5);
    const activeEl = document.getElementsByClassName("navListItem active");
    placeSelector(activeEl[0]);
    setTimeout(function() {
        document.getElementsByClassName("pageContent")[0].classList.remove("hiden");
    }, 500);
}
//if from another page 
else if (loadAnimation == 1) {
    const activeEl = document.getElementsByClassName("navListItem active");
    placeSelector(activeEl[0]);
    document.getElementById("primaryNav").classList.remove("hover");
    setTimeout(function() {
        document.getElementsByClassName("pageContent")[0].classList.remove("hiden");
    }, 400);
    
}

//Navigate to animation
let transition = false;
function navTo(el, link, relative) {
    if (transition == false && !el.classList.contains("active")) {
        transition = true;
        const listItems = document.getElementsByClassName("navListItem");
        for (i=0; i<listItems.length-1; i++){
            listItems[i].classList.remove("active");
        }
        el.classList.add("active");
        document.getElementById("primaryNav").classList.add("hover");
        placeSelector(el);
        document.getElementsByClassName("pageContent")[0].classList.add("hiden");
        setTimeout(function() {
            if (relative == true) {
                let baseUrl = getBaseURL(window.location.href);
                window.location.href = baseUrl + link; 
            } else {
                window.location.href = link;     
            }
            
        }, 500);
        
    }
}