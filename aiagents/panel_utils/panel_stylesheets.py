alert_stylesheet = """
    :host(.alert) {
        padding: 0 10px;
    }
"""

input_stylesheet = """
    :host {
        --current-background-color: transparent;
    }
    input[type=file].bk-input {
        font-size: 0.7rem;
        background-color: #faf7f7;
        padding-top: 0.7rem;
    }
    .bk-input:not([type='file']) {
        font-size: 0.7rem;
        background-color: #faf7f7;
    }
    input[type=file]::file-selector-button {
        display: none;
    }
    input[type=file].bk-input::before {
        content: "Upload API Specification";
        font-size: 0.75rem;
        color: #333;
        border-radius: 5px;
        padding: 0.5rem;
        margin: 0.7rem;
        border: 0.09rem solid #939893;
        cursor: pointer; 
    }
"""

azure_input_stylesheet = """
    .bk-input:not([type='file]) {
        background-color: #f3eaea !important;
    }
"""

radio_button_stylesheet = """
    :host(.outline)
    .bk-btn.bk-btn-default.bk-active {
        box-shadow: inset 0px 3px 2px rgb(0 0 0 / 25%);
        font-weight: 500;
        font-size: 0.75rem;
        padding: 0.5rem 1rem;
    }
    :host(.outline) .bk-btn.bk-btn-default {
        font-weight: 500;
        font-size: 0.75rem;
        padding: 0.5rem 1rem;
    }
"""

button_stylesheet = """
    :host(.solid)
    .bk-btn.bk-btn-default {
        font-size: 0.85rem;
        font-weight: 300;
        padding: 0.35rem 1rem;
        background-color: #dbdfcd;
        color: #222;
    }
    :host(.solid)
    .bk-btn.bk-btn-primary {
        font-size: 0.85rem;
        font-weight: 300;
        padding: 0.35rem 1rem;
        background-color: #33645a;
    }
    .bk-btn-primary[disabled],
    .bk-btn-primary[disabled]:hover, 
    .bk-btn-primary[disabled]:focus,
    .bk-btn-primary[disabled]:active, 
    .bk-active.bk-btn-primary[disabled] {
        background-color: #226b47 !important; 
    }
    .bk-btn-default[disabled],
    .bk-btn-default[disabled]:hover, 
    .bk-btn-default[disabled]:focus,
    .bk-btn-default[disabled]:active, 
    .bk-active.bk-btn-default[disabled] {
        background-color: #ebede2 !important;
        color: #444;
    }
"""

markdown_stylesheet = """
    :host(.markdown) > div {
        width: 350px !important;
        min-width: 350px !important;
        margin: 0 auto;
    }
"""

chat_stylesheet = """
    :host(.markdown) > div > p {
        margin: 0.65rem 0;
    }
"""

card_stylesheet = """
    .card-header,
    .accordion-header {
        border: 0.01rem solid #8b9d9d;
        border-bottom: 0.12rem solid #346d6d !important;
        border-radius: 0.2rem !important;
    }
    ::-webkit-scrollbar {
        width:0.4rem;
        height:0.4rem;
    }
    ::-webkit-scrollbar-thumb,
    ::-webkit-scrollbar-corner {
        background-color: #dbdfcf;
        border-radius: 5px;
    }
    ::-webkit-scrollbar-track {
        border-radius: 10%;
        margin: 0.3rem; 
    }
    .bk-Row.chat-interface-input-container {
        margin: -0.5rem 40px;
        width: calc(100vw - 400px - 10.5rem);
    }
    textarea.bk-input:not([type='file']) {
        background-color: #f6f1f1;
        border-radius: 10px;
        border: 0.05rem solid #666;
        padding: 0.55rem 1.5rem;
        font-size: 0.85rem;
        margin-right: 3rem;
        margin-bottom: 0.25rem;
        width: calc(100vw - 400px - 10.5rem);
    }
"""

nl2api_stylesheet = """
    .card-header {
        margin-right: 0;
    }
"""

sidebar_styles = {
    "border-bottom": "0.15rem solid #c0caca",
    "border-radius": "0.25rem",
    "max-height": "calc(100vh - 4.45rem)",
    "min-height": "calc(100vh - 4.45rem)",
    "overflow-y":"auto",
    "margin":"-0.6rem 0 -0.6rem 0.05rem",
    "padding":"0.5rem 0.1rem",
    "background-color": "#fff",
}

input_button_styles = {
    "font-size": "50px",
    "--surface-color": "#498080",
    "--surface-text-color": "#ffffff",
    "background-color": "#f6f9f9"
}
