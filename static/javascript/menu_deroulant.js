class MenuDeroulant extends HTMLElement{
    constructor() {
    super();
    this.attachShadow({ mode: "open" });
  }

  connectedCallback() {
    const select = this.querySelector("select");
    if (!select) return;

    // Styles
    const style = document.createElement("style");
    style.textContent = `
        .select {
            position: relative;
            user-select: none;
            display: inline-block;
            vertical-align: middle;
            margin-bottom: 1.5rem;
            width : inherit;
          }
        
        .select select {
          display: none;
        }
          
        .select-selected {
          height: 2rem;
          background-color: var(--white);
          box-shadow: var(--shadow);
          border-radius: 2rem;
        }
          
        /* Custom select arrow */
        .select-selected:after {
          position: absolute;
          content: "";
          top: 0.9rem;
          right: 15px;
          width: 0;
          height: 0;
          border: 6px solid transparent;
          border-color: var(--mainPamps) transparent transparent transparent;
        }
          
        .select-selected.select-arrow-active {
          border-radius: 1rem 1rem 0 0;
        }
        
        /* Custom select arrow direction (open) */
        .select-selected.select-arrow-active:after {
          border-color: transparent transparent var(--mainPamps) transparent;
          top: 0.6rem;
        }
        
        .select-arrow-active + .select-items {
          max-height: 230px;
          box-shadow: var(--shadow);
          opacity: 1;
        }
        
        .select-search .select-arrow-active + .select-items {
          max-height: 270px;
          box-shadow: var(--shadow);
          opacity: 1;
        }
          
          /* Custom select items */
        .select-items option,.select-selected {
          color: var(--textBlack);
          font-size: 1rem;
          font-weight: 400;
          padding: 8px 16px;
          border: 1px solid transparent;
          border-color: transparent transparent rgba(0, 0, 0, 0.1) transparent;
          cursor: pointer;
          height : auto;

        }
          
          /* Style items (options): */
        .select-items {
          position: absolute;
          background-color: var(--white);
          top: 100%;
          left: 0;
          right: 0;
          z-index: 99;
          max-height: 0px;
          border-radius: 0 0 1rem 1rem;
          box-shadow: none;
          overflow: auto;
          clip-path: inset(0px -20px -20px -20px);
          opacity: 0;
          transition: max-height 0.3s, border 0.3s, opacity 1ms;
        }
        
        .select-items::-webkit-scrollbar {
          display: none;
        }
          
        .same-as-selected {
          font-weight: 600 !important;
        }
        
        .select-items option:hover {
          background-color: var(--mainPampsFade) !important;
        }
        
        /* Select with searchbar */
        .select-search-bar {
          position: sticky;
          top: 0;
          width: 100%;
          padding: 0!important;
        
          box-shadow: var(--smallerShadow)!important;
          border: 1px solid transparent;
          border-color: transparent transparent rgba(0, 0, 0, 0.1) transparent;
        }
        
        .select-search-clear {
          position: absolute;
          color: var(--mainPamps);
          font-weight:bolder;
          font-size: 1.2rem;
          line-height: 1.2rem;
          right: 0.7rem;
          top: 0.3rem;
        }
        
        .select-search-bar-input {
          width: -webkit-fill-available;
          border-radius: 0!important;
          box-shadow: none!important;
          color: var(--textBlack);
          font-size: 1rem;
          font-weight: 400;
          padding: 8px 16px!important;
          border: 1px solid transparent;
          border-color: transparent transparent rgba(0, 0, 0, 0.1) transparent;
          margin: 0 !important;
        }
        
        .select-search-bar-input:focus{
            border: none;
            outline: none;
        }
        
        .select-items .select-noResults:hover {
          background-color: var(--mainPampsFade)!important;
        }
        
        .select-noResults {
            display: none;
            cursor: default!important;
          
            color: var(--textblack);
            font-size: 1rem;
            font-weight: 400;
            padding : 8px 16px;
            border : 1px solid transparent;
            border-color: transparent transparent rgba(0,0,0,0.1) transparent;
            cursor: pointer;
        }
        
        .select-option {
            color: var(--textblack);
            font-size: 1rem;
            font-weight: 400;
            padding : 8px 16px;
            border : 1px solid transparent;
            border-color: transparent transparent rgba(0,0,0,0.1) transparent;
            cursor: pointer;
        }
        
        .select-option:hover{
            background-color: var(--mainPampsFade);
        }
    `;

    const noResultText = this.getAttribute("data-no-result-text") || "Aucun résultats";

    const container = document.createElement("div");
    const selectedDiv = document.createElement("div");
    selectedDiv.className = "select-selected";
    selectedDiv.textContent = select.options[select.selectedIndex]?.textContent || "Sélectionner";

    const optionsDiv = document.createElement("div");
    optionsDiv.className = "select-items";

    // Regular options
    Array.from(select.options).forEach((opt, idx) => {
      if (idx === 0) return;
      const optionDiv = document.createElement("div");
      optionDiv.className = "select-option";
      optionDiv.textContent = opt.textContent;
      optionDiv.dataset.value = opt.value;

      optionDiv.addEventListener("click", () => {
        select.selectedIndex = idx;
        selectedDiv.textContent = opt.textContent;

        optionsDiv.querySelectorAll(".same-as-selected").forEach(el => el.classList.remove("same-as-selected"));
        optionDiv.classList.add("same-as-selected");

        select.dispatchEvent(new Event("change", { bubbles: true }));

        optionsDiv.style.maxHeight = "0";
        optionsDiv.style.opacity = "0";
        selectedDiv.classList.remove("select-arrow-active");
      });

      optionsDiv.appendChild(optionDiv);
    });

    // Customizable "no results" option
    const noResultsDiv = document.createElement("div");
    noResultsDiv.className = "select-option select-noResults";
    noResultsDiv.textContent = noResultText;
    noResultsDiv.style.display = "none";

    // Allow clicking it like a real option
    noResultsDiv.addEventListener("click", () => {
      // Default: close dropdown
      optionsDiv.style.maxHeight = "0";
      optionsDiv.style.opacity = "0";
      selectedDiv.classList.remove("select-arrow-active");
        console.log("noResultsDiv clicked");
      // Dispatch a custom event so the developer can handle it
      this.dispatchEvent(
          new CustomEvent("no-result-click", {
            bubbles: true,
            composed: true, // <-- permet à l'événement de traverser le shadow DOM
          })
        );
    });

    optionsDiv.appendChild(noResultsDiv);

    // Open/close dropdown
    selectedDiv.addEventListener("click", (e) => {
      e.stopPropagation();
      const isOpen = selectedDiv.classList.toggle("select-arrow-active");
      optionsDiv.style.maxHeight = isOpen ? "230px" : "0";
      optionsDiv.style.opacity = isOpen ? "1" : "0";
    });


    // Close on outside click
    window.addEventListener("click", (e) => {
      if (!this.shadowRoot.contains(e.target)) {
        selectedDiv.classList.remove("select-arrow-active");
        optionsDiv.style.maxHeight = "0";
        optionsDiv.style.opacity = "0";
      }
    });

    container.className = "select";
    container.appendChild(selectedDiv);
    container.appendChild(optionsDiv);
    this.shadowRoot.append(style, container);

    select.style.display = "none";
  }
}
