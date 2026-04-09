import dash
from dash import html, dcc, dash_table
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
from dash_iconify import DashIconify
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import sqlalchemy
from datetime import datetime, timedelta
import numpy as np

# ---------- Database ----------
engine = sqlalchemy.create_engine(
    "mysql+mysqlconnector://prrsv_admin:SecureDBpass456!@localhost/prrsv_genomics"
)

def get_latest_eii():
    df = pd.read_sql("SELECT eii_value, created_at FROM eii_index ORDER BY id DESC LIMIT 1", engine)
    if df.empty:
        return 0.0, "No data"
    return float(df.iloc[0,0]), str(df.iloc[0,1])

def get_signals():
    df = pd.read_sql("SELECT signal_name, mean_value FROM eii_signals", engine)
    if df.empty:
        df = pd.DataFrame({
            'signal_name': ['Epitope Drift', 'Selection Pressure', 'Glycosylation Dynamics',
                            'Phylogenetic Instability', 'Distance Outliers'],
            'mean_value':[0,0,0,0,0]
        })
    df['signal_name'] = df['signal_name'].str.replace('([a-z])([A-Z])', r'\1 \2', regex=True)
    return df

def get_trend():
    df = pd.read_sql("SELECT created_at, eii_value FROM eii_index ORDER BY created_at", engine)
    if df.empty:
        df = pd.DataFrame({'created_at':[datetime.now()], 'eii_value':[0]})
    return df

# ---------- App ----------
# Custom theme combining DARKLY and custom styles
app = dash.Dash(
    __name__, 
    external_stylesheets=[
        dbc.themes.DARKLY,
        'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css',
        'https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap'
    ]
)
app.title = "PRRSV ORF5 - Evolutionary Intelligence Dashboard"

# Custom CSS for enhanced styling
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
            /* Custom CSS with Inter font */
            * {
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            }
            
            :root {
                --primary-color: #6366f1;
                --primary-light: #818cf8;
                --primary-dark: #4f46e5;
                --secondary-color: #10b981;
                --warning-color: #f59e0b;
                --danger-color: #ef4444;
                --dark-bg: #0f172a;
                --card-bg: #1e293b;
                --card-border: rgba(255, 255, 255, 0.08);
                --text-primary: #f8fafc;
                --text-secondary: #94a3b8;
            }
            
            body {
                background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
                min-height: 100vh;
                margin: 0;
                padding: 0;
            }
            
            /* Modern Glass Morphism Cards */
            .glass-card {
                background: rgba(30, 41, 59, 0.7);
                backdrop-filter: blur(20px);
                -webkit-backdrop-filter: blur(20px);
                border: 1px solid var(--card-border);
                border-radius: 20px;
                box-shadow: 
                    0 10px 25px rgba(0, 0, 0, 0.3),
                    inset 0 1px 0 rgba(255, 255, 255, 0.1);
                transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.1);
                overflow: hidden;
            }
            
            .glass-card:hover {
                transform: translateY(-8px);
                box-shadow: 
                    0 20px 40px rgba(0, 0, 0, 0.4),
                    0 8px 30px rgba(99, 102, 241, 0.2),
                    inset 0 1px 0 rgba(255, 255, 255, 0.1);
                border-color: rgba(99, 102, 241, 0.3);
            }
            
            /* Premium Header */
            .premium-header {
                background: linear-gradient(
                    135deg,
                    rgba(15, 23, 42, 0.95) 0%,
                    rgba(30, 41, 59, 0.95) 50%,
                    rgba(15, 23, 42, 0.95) 100%
                );
                border-bottom: 1px solid rgba(99, 102, 241, 0.3);
                position: relative;
                padding: 1.5rem 0;
                margin-bottom: 2rem;
                width: 100%;
            }
            
            .premium-header::before {
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                height: 1px;
                background: linear-gradient(90deg, 
                    transparent, 
                    var(--primary-color), 
                    transparent
                );
            }
            
            .premium-header::after {
                content: '';
                position: absolute;
                bottom: -1px;
                left: 0;
                right: 0;
                height: 1px;
                background: linear-gradient(90deg, 
                    transparent, 
                    rgba(99, 102, 241, 0.2), 
                    transparent
                );
            }
            
            .header-content {
                display: flex;
                align-items: center;
                justify-content: space-between;
                flex-wrap: wrap;
                gap: 1.5rem;
            }
            
            .logo-container {
                display: flex;
                align-items: center;
                gap: 1rem;
            }
            
            .logo-icon {
                width: 48px;
                height: 48px;
                background: linear-gradient(135deg, var(--primary-color), var(--primary-dark));
                border-radius: 12px;
                display: flex;
                align-items: center;
                justify-content: center;
                box-shadow: 0 4px 15px rgba(99, 102, 241, 0.3);
            }
            
            .logo-icon i {
                font-size: 24px;
                color: white;
            }
            
            .header-text {
                flex: 1;
                min-width: 300px;
            }
            
            .system-status {
                display: flex;
                align-items: center;
                gap: 0.5rem;
                padding: 0.5rem 1rem;
                background: rgba(16, 185, 129, 0.1);
                border: 1px solid rgba(16, 185, 129, 0.3);
                border-radius: 10px;
                backdrop-filter: blur(10px);
            }
            
            .status-dot {
                width: 8px;
                height: 8px;
                background: var(--secondary-color);
                border-radius: 50%;
                animation: pulse 2s infinite;
            }
            
            @keyframes pulse {
                0%, 100% { opacity: 1; }
                50% { opacity: 0.5; }
            }
            
            /* Modern Metrics */
            .metric-card {
                height: 100%;
                padding: 1.5rem;
                display: flex;
                flex-direction: column;
            }
            
            .metric-value {
                font-size: 2.8rem;
                font-weight: 800;
                background: linear-gradient(135deg, var(--primary-color), var(--secondary-color));
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
                line-height: 1;
                margin: 0.5rem 0;
            }
            
            .metric-label {
                font-size: 0.875rem;
                font-weight: 600;
                color: var(--text-secondary);
                text-transform: uppercase;
                letter-spacing: 0.05em;
                display: flex;
                align-items: center;
                gap: 0.5rem;
                margin-bottom: 0.5rem;
            }
            
            .metric-trend {
                display: flex;
                align-items: center;
                gap: 0.5rem;
                font-size: 0.875rem;
                font-weight: 500;
                margin-top: auto;
            }
            
            /* Trend indicators */
            .trend-up {
                color: var(--secondary-color);
                background: rgba(16, 185, 129, 0.1);
                padding: 0.25rem 0.75rem;
                border-radius: 20px;
                display: inline-flex;
                align-items: center;
                gap: 0.25rem;
            }
            
            .trend-down {
                color: var(--danger-color);
                background: rgba(239, 68, 68, 0.1);
                padding: 0.25rem 0.75rem;
                border-radius: 20px;
                display: inline-flex;
                align-items: center;
                gap: 0.25rem;
            }
            
            .trend-stable {
                color: var(--warning-color);
                background: rgba(245, 158, 11, 0.1);
                padding: 0.25rem 0.75rem;
                border-radius: 20px;
                display: inline-flex;
                align-items: center;
                gap: 0.25rem;
            }
            
            /* Data Table Styling */
            .modern-table {
                border: none;
                background: transparent;
            }
            
            .modern-table .dash-table-container .dash-spreadsheet-container {
                background: transparent !important;
            }
            
            .modern-table .dash-table-container .dash-spreadsheet-container table {
                border-collapse: separate;
                border-spacing: 0;
            }
            
            .modern-table .dash-header {
                background: rgba(99, 102, 241, 0.1) !important;
                border: none !important;
                color: var(--text-primary) !important;
                font-weight: 600 !important;
                padding: 1rem !important;
            }
            
            .modern-table .dash-cell {
                background: transparent !important;
                border: none !important;
                border-bottom: 1px solid rgba(255, 255, 255, 0.05) !important;
                padding: 1rem !important;
                color: var(--text-secondary) !important;
            }
            
            /* Enhanced Footer */
            .premium-footer {
                background: linear-gradient(
                    180deg,
                    transparent 0%,
                    rgba(15, 23, 42, 0.8) 100%
                );
                padding: 2rem 0;
                margin-top: 3rem;
                position: relative;
                border-top: 1px solid rgba(99, 102, 241, 0.2);
            }
            
            .premium-footer::before {
                content: '';
                position: absolute;
                top: 0;
                left: 50%;
                transform: translateX(-50%);
                width: 200px;
                height: 1px;
                background: linear-gradient(90deg, 
                    transparent, 
                    var(--primary-color), 
                    transparent
                );
            }
            
            /* Chart containers */
            .chart-container {
                padding: 1.5rem;
                height: 100%;
            }
            
            /* Scrollbar styling */
            ::-webkit-scrollbar {
                width: 8px;
                height: 8px;
            }
            
            ::-webkit-scrollbar-track {
                background: rgba(255, 255, 255, 0.05);
                border-radius: 4px;
            }
            
            ::-webkit-scrollbar-thumb {
                background: var(--primary-color);
                border-radius: 4px;
            }
            
            ::-webkit-scrollbar-thumb:hover {
                background: var(--primary-light);
            }
            
            /* Responsive adjustments */
            @media (max-width: 768px) {
                .header-content {
                    flex-direction: column;
                    align-items: flex-start;
                }
                
                .system-status {
                    align-self: flex-start;
                }
                
                .metric-value {
                    font-size: 2rem;
                }
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

# ---------- Layout ----------
app.layout = html.Div([
    # Premium Header
    html.Div([
        dbc.Container(fluid=True, children=[
            html.Div([
                # Logo and Title Section
                html.Div([
                    html.Div([
                        html.Div([
                            html.I(className="fas fa-dna fa-lg")
                        ], className="logo-icon"),
                        html.Div([
                            html.H1([
                                html.Span("PRRSV", style={"color": "#6366f1", "fontWeight": "800"}),
                                html.Span(" ORF5", style={"color": "#f8fafc", "fontWeight": "800"}),
                                html.Span(" Evolution", style={
                                    "background": "linear-gradient(135deg, #6366f1 0%, #10b981 100%)",
                                    "-webkit-background-clip": "text",
                                    "-webkit-text-fill-color": "transparent",
                                    "backgroundClip": "text",
                                    "fontWeight": "800"
                                })
                            ], style={"margin": "0", "fontSize": "2rem", "lineHeight": "1.2"}),
                            html.P("Advanced Evolutionary Intelligence Monitoring System", 
                                  style={"margin": "0", "color": "#94a3b8", "fontSize": "0.95rem"})
                        ], style={"flex": "1"})
                    ], className="logo-container"),
                    
                    # System Status
                    html.Div([
                        html.Span(className="status-dot"),
                        html.Span("LIVE", style={"fontWeight": "600", "color": "#10b981"}),
                        html.Span("•", style={"color": "#64748b", "margin": "0 0.5rem"}),
                        html.Span("Auto-refresh", style={"color": "#94a3b8", "fontSize": "0.875rem"})
                    ], className="system-status")
                ], className="header-content")
            ])
        ])
    ], className="premium-header"),
    
    # Main Content
    dbc.Container(fluid=True, children=[
        # Key Metrics Row
        dbc.Row([
            dbc.Col([
                html.Div([
                    html.Div([
                        html.Div([
                            html.Div([
                                html.I(className="fas fa-chart-line", style={"color": "#6366f1"})
                            ], style={"marginBottom": "1rem"}),
                            html.Div([
                                html.Div([
                                    html.Span("CURRENT EII", className="metric-label"),
                                    html.H2(id="latest-eii-value", className="metric-value"),
                                    html.P(id="latest-eii-timestamp", 
                                          style={"color": "#64748b", "fontSize": "0.875rem", "margin": "0"})
                                ]),
                                dbc.Progress(id="eii-progress", value=0, 
                                           style={
                                               "height": "6px", 
                                               "background": "rgba(255,255,255,0.05)",
                                               "marginTop": "1rem",
                                               "borderRadius": "3px"
                                           })
                            ])
                        ], className="metric-card")
                    ], className="glass-card")
                ])
            ], md=3),
            
            dbc.Col([
                html.Div([
                    html.Div([
                        html.Div([
                            html.Div([
                                html.I(className="fas fa-atom", style={"color": "#10b981"})
                            ], style={"marginBottom": "1rem"}),
                            html.Div([
                                html.Span("DOMINANT SIGNAL", className="metric-label"),
                                html.H3(id="dominant-signal", style={
                                    "fontSize": "1.8rem",
                                    "fontWeight": "700",
                                    "color": "#f8fafc",
                                    "margin": "0.5rem 0",
                                    "minHeight": "2.5rem"
                                }),
                                html.P("Primary evolutionary driver", 
                                      style={"color": "#64748b", "fontSize": "0.875rem", "margin": "0"})
                            ])
                        ], className="metric-card")
                    ], className="glass-card")
                ])
            ], md=3),
            
            dbc.Col([
                html.Div([
                    html.Div([
                        html.Div([
                            html.Div([
                                html.I(className="fas fa-trend-up", style={"color": "#f59e0b"})
                            ], style={"marginBottom": "1rem"}),
                            html.Div([
                                html.Span("TREND STATUS", className="metric-label"),
                                html.Div([
                                    html.H3(id="trend-status", style={
                                        "fontSize": "1.8rem",
                                        "fontWeight": "700",
                                        "color": "#f8fafc",
                                        "margin": "0.5rem 0"
                                    }),
                                    html.Span(id="trend-icon", className="trend-stable")
                                ], style={"display": "flex", "alignItems": "center", "gap": "0.5rem", "flexWrap": "wrap"}),
                                html.P(id="trend-description", 
                                      style={"color": "#64748b", "fontSize": "0.875rem", "margin": "0"})
                            ])
                        ], className="metric-card")
                    ], className="glass-card")
                ])
            ], md=3),
            
            dbc.Col([
                html.Div([
                    html.Div([
                        html.Div([
                            html.Div([
                                html.I(className="fas fa-sync-alt", style={"color": "#8b5cf6"})
                            ], style={"marginBottom": "1rem"}),
                            html.Div([
                                html.Span("DATA FRESHNESS", className="metric-label"),
                                html.H3(id="data-freshness", style={
                                    "fontSize": "1.8rem",
                                    "fontWeight": "700",
                                    "color": "#f8fafc",
                                    "margin": "0.5rem 0"
                                }),
                                html.Div([
                                    html.Span(id="refresh-time", 
                                            style={"color": "#94a3b8", "fontSize": "0.875rem"}),
                                    html.Span(" • ", style={"color": "#64748b", "margin": "0 0.25rem"}),
                                    html.Span("Next: ", style={"color": "#94a3b8", "fontSize": "0.875rem"}),
                                    html.Span(id="next-refresh", 
                                            style={"color": "#10b981", "fontSize": "0.875rem", "fontWeight": "500"})
                                ])
                            ])
                        ], className="metric-card")
                    ], className="glass-card")
                ])
            ], md=3),
        ], className="mb-4", style={"rowGap": "1rem"}),
        
        # Charts Row
        dbc.Row([
            dbc.Col([
                html.Div([
                    dbc.Card([
                        dbc.CardHeader([
                            html.Div([
                                html.H5("📈 Evolutionary Trajectory", style={"margin": "0", "fontWeight": "600"}),
                                html.Small("30-day EII evolution with predictive analysis", 
                                         style={"color": "#94a3b8", "fontSize": "0.875rem"})
                            ])
                        ], style={
                            "background": "rgba(99, 102, 241, 0.05)",
                            "borderBottom": "1px solid rgba(255,255,255,0.05)",
                            "padding": "1.25rem"
                        }),
                        dbc.CardBody([
                            dcc.Graph(id="trend-chart", style={"height": "380px"})
                        ], style={"padding": "0"})
                    ], className="glass-card", style={"height": "100%"})
                ])
            ], lg=8),
            
            dbc.Col([
                html.Div([
                    dbc.Card([
                        dbc.CardHeader([
                            html.Div([
                                html.H5("🧬 Signal Composition", style={"margin": "0", "fontWeight": "600"}),
                                html.Small("Current evolutionary signal distribution", 
                                         style={"color": "#94a3b8", "fontSize": "0.875rem"})
                            ])
                        ], style={
                            "background": "rgba(16, 185, 129, 0.05)",
                            "borderBottom": "1px solid rgba(255,255,255,0.05)",
                            "padding": "1.25rem"
                        }),
                        dbc.CardBody([
                            dcc.Graph(id="signal-chart", style={"height": "380px"})
                        ], style={"padding": "0"})
                    ], className="glass-card", style={"height": "100%"})
                ])
            ], lg=4),
        ], className="mb-4", style={"rowGap": "1rem"}),
        
        # Data Table Row
        dbc.Row([
            dbc.Col([
                html.Div([
                    dbc.Card([
                        dbc.CardHeader([
                            html.Div([
                                html.H5("📊 Signal Intelligence Matrix", style={"margin": "0", "fontWeight": "600"}),
                                html.Small("Detailed evolutionary signal analysis with risk assessment", 
                                         style={"color": "#94a3b8", "fontSize": "0.875rem"})
                            ])
                        ], style={
                            "background": "rgba(245, 158, 11, 0.05)",
                            "borderBottom": "1px solid rgba(255,255,255,0.05)",
                            "padding": "1.25rem"
                        }),
                        dbc.CardBody([
                            dash_table.DataTable(
                                id="signal-table",
                                columns=[
                                    {"name": "Evolutionary Signal", "id": "signal_name"},
                                    {"name": "Intensity", "id": "mean_value", "type": "numeric", 
                                     "format": {"specifier": ".4f"}},
                                    {"name": "Impact", "id": "impact_level"},
                                    {"name": "Risk", "id": "risk_level"},
                                    {"name": "Trend", "id": "trend"}
                                ],
                                style_table={"overflowX": "auto", "borderRadius": "10px"},
                                style_cell_conditional=[
                                    {'if': {'column_id': 'signal_name'}, 'textAlign': 'left'},
                                    {'if': {'column_id': 'mean_value'}, 'textAlign': 'center'},
                                    {'if': {'column_id': 'impact_level'}, 'textAlign': 'center'},
                                    {'if': {'column_id': 'risk_level'}, 'textAlign': 'center'},
                                    {'if': {'column_id': 'trend'}, 'textAlign': 'center'}
                                ],
                                style_data_conditional=[
                                    {
                                        'if': {'filter_query': '{risk_level} = "High"'},
                                        'backgroundColor': 'rgba(239, 68, 68, 0.1)',
                                        'borderLeft': '4px solid #ef4444'
                                    },
                                    {
                                        'if': {'filter_query': '{risk_level} = "Medium"'},
                                        'backgroundColor': 'rgba(245, 158, 11, 0.1)',
                                        'borderLeft': '4px solid #f59e0b'
                                    },
                                    {
                                        'if': {'filter_query': '{risk_level} = "Low"'},
                                        'backgroundColor': 'rgba(16, 185, 129, 0.1)',
                                        'borderLeft': '4px solid #10b981'
                                    },
                                    {
                                        'if': {'column_id': 'mean_value', 'filter_query': '{mean_value} > 0.7'},
                                        'color': '#ef4444',
                                        'fontWeight': '600'
                                    },
                                    {
                                        'if': {'column_id': 'mean_value', 'filter_query': '{mean_value} > 0.4 && {mean_value} <= 0.7'},
                                        'color': '#f59e0b',
                                        'fontWeight': '500'
                                    },
                                    {
                                        'if': {'column_id': 'mean_value', 'filter_query': '{mean_value} <= 0.4'},
                                        'color': '#10b981',
                                        'fontWeight': '500'
                                    }
                                ],
                                style_header={
                                    'backgroundColor': 'rgba(99, 102, 241, 0.1)',
                                    'fontWeight': '600',
                                    'color': '#f8fafc',
                                    'border': 'none',
                                    'padding': '1rem',
                                    'fontSize': '0.875rem'
                                },
                                style_cell={
                                    'backgroundColor': 'transparent',
                                    'color': '#94a3b8',
                                    'border': 'none',
                                    'padding': '0.875rem',
                                    'fontSize': '0.875rem',
                                    'fontFamily': "'Inter', sans-serif"
                                },
                                page_size=10,
                                sort_action='native',
                                filter_action='native'
                            )
                        ], style={"padding": "1.25rem"})
                    ], className="glass-card")
                ])
            ], width=12),
        ], className="mb-4"),
        
        # Premium Footer
        html.Div([
            dbc.Container(fluid=True, children=[
                dbc.Row([
                    dbc.Col([
                        html.Div([
                            html.Div([
                                html.I(className="fas fa-shield-alt", 
                                      style={"color": "#6366f1", "fontSize": "1.5rem", "marginRight": "0.75rem"})
                            ], style={"marginBottom": "1rem"}),
                            html.H6("PRRSV Evolutionary Intelligence Platform", 
                                   style={"color": "#f8fafc", "fontWeight": "600", "marginBottom": "0.5rem"}),
                            html.P([
                                "© 2025 Scientific Monitoring System v2.4.1 | ",
                                html.Span("Production • Stable", 
                                         style={"color": "#10b981", "fontWeight": "500"})
                            ], style={"color": "#94a3b8", "fontSize": "0.875rem", "marginBottom": "0.25rem"}),
                            html.P([
     html.Span(
        "Developed for advanced virology research • ",
        style={"color": "#64748b"}
    ),
    html.Span(
        "Powered by AI CONCEPTS LIMITED, Nigeria • PRRSV Evolutionary Intelligence Platform",
        style={"color": "#10b981", "fontWeight": "500"}
    )
], style={"color": "#94a3b8", "fontSize": "0.875rem", "marginBottom": "0.25rem"})

                        ], style={"textAlign": "center"})
                    ], width=12)
                ])
            ])
        ], className="premium-footer")
    ], style={"maxWidth": "100%", "padding": "0 1rem"}),

    # Hidden components for auto-refresh
    dcc.Interval(id="interval-refresh", interval=60*1000, n_intervals=0),
    dcc.Store(id='last-update-time')
])

# ---------- Callbacks ----------
@app.callback(
    [Output("latest-eii-value", "children"),
     Output("latest-eii-timestamp", "children"),
     Output("dominant-signal", "children"),
     Output("trend-status", "children"),
     Output("trend-icon", "children"),
     Output("trend-icon", "className"),
     Output("trend-description", "children"),
     Output("data-freshness", "children"),
     Output("refresh-time", "children"),
     Output("next-refresh", "children"),
     Output("eii-progress", "value"),
     Output("trend-chart", "figure"),
     Output("signal-chart", "figure"),
     Output("signal-table", "data")],
    [Input("interval-refresh", "n_intervals"),
     Input("interval-refresh", "n_intervals")]
)
def update_dashboard(n_intervals, _):
    # Get data
    eii_value, ts = get_latest_eii()
    df_sig = get_signals()
    df_trend = get_trend()
    
    # Format timestamp
    try:
        timestamp = pd.to_datetime(ts).strftime("%b %d, %Y %H:%M:%S")
    except:
        timestamp = ts
    
    # Calculate dominant signal
    if df_sig.empty or df_sig['mean_value'].isna().all():
        dom_signal = "N/A"
    else:
        dom_signal = df_sig.loc[df_sig['mean_value'].idxmax(), 'signal_name']
    
    # Calculate trend with enhanced logic
    if len(df_trend) < 2:
        trend_status = "Stable"
        trend_icon = "→"
        trend_class = "trend-stable"
        trend_desc = "Insufficient data for trend analysis"
    else:
        # Calculate percentage change over last 7 days
        recent = df_trend.tail(7)
        if len(recent) >= 2:
            start_val = recent.iloc[0]['eii_value']
            end_val = recent.iloc[-1]['eii_value']
            pct_change = ((end_val - start_val) / start_val * 100) if start_val != 0 else 0
            
            if pct_change > 10:
                trend_status = "Rising"
                trend_icon = "↗"
                trend_class = "trend-up"
                trend_desc = f"+{pct_change:.1f}% over last 7 days"
            elif pct_change < -10:
                trend_status = "Falling"
                trend_icon = "↘"
                trend_class = "trend-down"
                trend_desc = f"{pct_change:.1f}% over last 7 days"
            else:
                trend_status = "Stable"
                trend_icon = "→"
                trend_class = "trend-stable"
                trend_desc = f"{abs(pct_change):.1f}% change over last 7 days"
        else:
            trend_status = "Stable"
            trend_icon = "→"
            trend_class = "trend-stable"
            trend_desc = "Monitoring stability"
    
    # Data freshness
    try:
        last_update = pd.to_datetime(ts)
        time_diff = datetime.now() - last_update
        minutes_diff = time_diff.total_seconds() / 60
        
        if minutes_diff < 1:
            freshness = "Just now"
        elif minutes_diff < 60:
            freshness = f"{int(minutes_diff)} min ago"
        else:
            freshness = f"{int(minutes_diff/60)} hr ago"
    except:
        freshness = "Unknown"
    
    # Refresh times
    current_time = datetime.now().strftime("%H:%M:%S")
    next_time = (datetime.now() + timedelta(minutes=1)).strftime("%H:%M")
    
    # Calculate progress bar
    eii_progress = min(100, max(0, eii_value * 100))
    
    # Create enhanced trend chart
    fig_trend = go.Figure()
    
    if not df_trend.empty:
        # Add main area trace
        fig_trend.add_trace(go.Scatter(
            x=df_trend['created_at'],
            y=df_trend['eii_value'],
            mode='lines',
            name='EII Value',
            line=dict(color='#6366f1', width=3, shape='spline'),
            fill='tozeroy',
            fillcolor='rgba(99, 102, 241, 0.1)',
            hovertemplate='<b>EII: %{y:.4f}</b><br>%{x|%b %d, %Y}<extra></extra>'
        ))
        
        # Add recent points
        recent_points = df_trend.tail(10)
        fig_trend.add_trace(go.Scatter(
            x=recent_points['created_at'],
            y=recent_points['eii_value'],
            mode='markers',
            name='Recent Points',
            marker=dict(
                color='#10b981',
                size=8,
                line=dict(width=2, color='white')
            ),
            hovertemplate='<b>EII: %{y:.4f}</b><br>%{x|%b %d, %Y %H:%M}<extra></extra>'
        ))
        
        # Add 7-day moving average if enough data
        if len(df_trend) >= 7:
            df_trend['ma7'] = df_trend['eii_value'].rolling(window=7, min_periods=1).mean()
            fig_trend.add_trace(go.Scatter(
                x=df_trend['created_at'],
                y=df_trend['ma7'],
                mode='lines',
                name='7-Day MA',
                line=dict(color='#f59e0b', width=2, dash='dash'),
                hovertemplate='<b>7-Day MA: %{y:.4f}</b><br>%{x|%b %d, %Y}<extra></extra>'
            ))
    
    # Update trend chart layout
    fig_trend.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#94a3b8', family="'Inter', sans-serif"),
        xaxis=dict(
            gridcolor='rgba(255,255,255,0.05)',
            title=dict(text="Date", font=dict(color='#94a3b8')),
            tickfont=dict(color='#64748b')
        ),
        yaxis=dict(
            gridcolor='rgba(255,255,255,0.05)',
            title=dict(text="EII Value", font=dict(color='#94a3b8')),
            tickfont=dict(color='#64748b')
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            bgcolor='rgba(0,0,0,0)',
            font=dict(color='#94a3b8')
        ),
        hoverlabel=dict(
            bgcolor='rgba(30, 41, 59, 0.95)',
            font=dict(color='white')
        ),
        margin=dict(l=0, r=0, t=30, b=0)
    )
    
    # Create enhanced donut chart for signals
    fig_donut = go.Figure()
    
    if not df_sig.empty and 'mean_value' in df_sig.columns:
        # Use vibrant color palette
        colors = ['#6366f1', '#10b981', '#f59e0b', '#8b5cf6', '#ef4444']
        
        fig_donut.add_trace(go.Pie(
            labels=df_sig['signal_name'],
            values=df_sig['mean_value'],
            hole=.6,
            marker=dict(colors=colors),
            textinfo='label+percent',
            textposition='outside',
            textfont=dict(color='#94a3b8', size=12),
            hovertemplate="<b>%{label}</b><br>Value: %{value:.4f}<br>Contribution: %{percent}<extra></extra>",
            pull=[0.1 if i == df_sig['mean_value'].idxmax() else 0 for i in range(len(df_sig))]
        ))
    
    fig_donut.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#94a3b8', family="'Inter', sans-serif"),
        showlegend=False,
        margin=dict(t=0, b=0, l=0, r=0),
        annotations=[dict(
            text=f"Total<br>{df_sig['mean_value'].sum():.3f}",
            x=0.5, y=0.5,
            font=dict(size=18, color='#f8fafc'),
            showarrow=False
        )] if not df_sig.empty else []
    )
    
    # Prepare enhanced table data
    if not df_sig.empty:
        # Add impact levels
        df_sig['impact_level'] = pd.cut(df_sig['mean_value'], 
                                       bins=[-0.1, 0.3, 0.6, 1.1],
                                       labels=['Low', 'Medium', 'High'])
        
        # Add risk levels
        df_sig['risk_level'] = df_sig['impact_level']
        
        # Add trend indicators
        def get_trend_indicator(value):
            if value > 0.7:
                return "🔴 High"
            elif value > 0.4:
                return "🟡 Moderate"
            else:
                return "🟢 Low"
        
        df_sig['trend'] = df_sig['mean_value'].apply(get_trend_indicator)
        table_data = df_sig.to_dict('records')
    else:
        table_data = []
    
    return (
        f"{eii_value:.4f}",
        f"Updated: {timestamp}",
        dom_signal,
        trend_status,
        trend_icon,
        trend_class,
        trend_desc,
        freshness,
        current_time,
        next_time,
        eii_progress,
        fig_trend,
        fig_donut,
        table_data
    )

# ---------- Run ----------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8055, debug=False, dev_tools_ui=False)
