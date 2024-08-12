alert_stylesheet = """
    :host(.alert) {
        padding: 0 10px;
    }
"""

input_stylesheet = """
    :host {
        --current-background-color: transparent;
    }
"""

radio_button_stylesheet = """
    :host(.outline)
    .bk-btn.bk-btn-default.bk-active {
        box-shadow: inset 0px 3px 2px rgb(0 0 0 / 25%);
        font-weight: 400;
        font-size: 0.8rem;
        padding: 0.5rem 1rem;
    }
    :host(.outline) .bk-btn.bk-btn-default {
        font-weight: 400;
        font-size: 0.8rem;
        padding: 0.5rem 1rem;
    }
"""

button_stylesheet = """
    :host(.solid)
    .bk-btn.bk-btn-default {
        font-size: 0.9rem;
        font-weight: 300;
        padding: 0.35rem 1rem;
        background-color: #dbdfcd;
        color: #222;
    }
    :host(.solid)
    .bk-btn.bk-btn-primary {
        font-size: 0.9rem;
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

card_stylesheet = """
    .card-header,
    .accordion-header {
        border-bottom: 0.1rem solid #c0caca !important;
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
        margin: 0 40px;
    }
"""

sidebar_styles = {
    "border-bottom": "0.15rem solid #c0caca",
    "border-radius": "0.25rem",
    "max-height": "calc(100vh - 80px)",
    "min-height": "calc(100vh - 80px)",
    "overflow-y":"scroll",
    "margin":"-0.3rem 0.1rem",
    "padding":"0.5rem 0.1rem", 
}

input_button_styles = {
    "font-size": "50px",
    "--surface-color": "#498080",
    "--surface-text-color": "#ffffff"
}
