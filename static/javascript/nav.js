
function getParams() {
    let idx = document.URL.indexOf('?');
    let params = new Array();
    if (idx != -1) {
        let pairs = document.URL.substring(idx+1, document.URL.length).split('&');
        for (let i=0; i<pairs.length; i++) {
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
    let url = window.location.protocol + "//" + window.location.host + window.location.pathname;
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

//Moving selector to element
function placeSelector(el) {
    const elRect = el.getBoundingClientRect();
    const selector = document.getElementById("selector");
    const selectorRect = selector.getBoundingClientRect();

    const elCenterY = elRect.top + elRect.height / 2;
    const selectorHeight = selectorRect.height;
    const selectorCenterY = selectorHeight / 2;

    const topPosition = elCenterY - selectorCenterY;

    selector.style.top = `${topPosition}px`;
}

//--ANIMATIONS--


if (window.matchMedia("(max-width: 768px)").matches) {
    //--Mobile--
    if (loadAnimation == 0) {
        document.getElementById("pageCover").style.animation = "1ms forwards quickHide";
        const activeEl = document.getElementsByClassName("navListItem active");
        placeSelector(activeEl[0]);
        setTimeout(function() {
            document.getElementsByClassName("pageContent")[0].classList.remove("hidden");
        }, 500);
    }

    //if from another page using nav
    else if (loadAnimation == 1) {
        const cover = document.getElementById("pageCover");
        cover.style.animation = "1.5s forwards fullToHiddenMobile";
        const activeEl = document.getElementsByClassName("navListItem active");
        placeSelector(activeEl[0]);
        setTimeout(function() {
            document.getElementsByClassName("pageContent")[0].classList.remove("hidden");
        }, 400);
    }

    //if from connection page
    else if (loadAnimation == 2) {
        document.getElementById("primaryNav").classList.remove("hover");
        const cover = document.getElementById("pageCover");
        cover.style.animation = "1.5s forwards fullToHiddenMobile";
        const activeEl = document.getElementsByClassName("navListItem active");
        placeSelector(activeEl[0]);
        setTimeout(function() {
            document.getElementsByClassName("pageContent")[0].classList.remove("hidden");
        }, 2200);   
    }

    //Quitting using nav
    let transition = false;
    function navTo(el, link, relative) {
        if (transition == false && !el.classList.contains("active")) {
            transition = true;
            const cover = document.getElementById("pageCover");
            placeSelector(el);
            setTimeout(function() {
               cover.style.animation = "0.5s forwards fadeIn"; 
            }, 250);
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
    
    function toggleNav(hamburger) {
        hamburger.classList.toggle("close");
        hamburger.parentNode.classList.toggle("open");
    }
} else {
    //--Desktop--
    //if reload or no info
    if (loadAnimation == 0) {
        document.getElementById("pageCover").style.animation = "1ms forwards quickHide";
        const primaryNav = document.getElementById("primaryNav");
        primaryNav.classList.add("skipTransition");
        primaryNav.classList.remove("hover");
        setTimeout(function() {
            primaryNav.classList.remove("skipTransition");
        }, 5);
        const activeEl = document.getElementsByClassName("navListItem active");
        placeSelector(activeEl[0]);
        setTimeout(function() {
            document.getElementsByClassName("pageContent")[0].classList.remove("hidden");
        }, 500);
    }

    //if from another page using nav
    else if (loadAnimation == 1) {
        document.getElementById("pageCover").style.display="none";
        const activeEl = document.getElementsByClassName("navListItem active");
        placeSelector(activeEl[0]);
        document.getElementById("primaryNav").classList.remove("hover");
        setTimeout(function() {
            document.getElementsByClassName("pageContent")[0].classList.remove("hidden");
        }, 400);
        
    }

    //if from connection page
    else if (loadAnimation == 2) {
        document.getElementById("primaryNav").classList.remove("hover");
        const cover = document.getElementById("pageCover");
        cover.style.animation = "1.8s forwards fullToHidden";
        const activeEl = document.getElementsByClassName("navListItem active");
        placeSelector(activeEl[0]);
        setTimeout(function() {
            document.getElementsByClassName("pageContent")[0].classList.remove("hidden");
        }, 2200);
        
    }

    //Quitting using nav
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
            document.getElementsByClassName("pageContent")[0].classList.add("hidden");
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

    //Quitting using disconnect
    function disconnect(sendToLink) {
        //DISCONNECT CODE HERE

        //Page closing animation
        if (transition == false) {
            transition = true;
            document.getElementById("primaryNav").classList.add("hover");
            const cover = document.getElementById("pageCover");
            cover.style.animation = "1.5s forwards hiddenToFull";
            setTimeout(function() {
                window.location.href = sendToLink;  
            }, 1500);
        }
    }
}