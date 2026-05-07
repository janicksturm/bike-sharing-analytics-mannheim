
PLOTLY_TEMPLATE = "plotly_dark"
CHART_BG = "rgba(22,27,34,0)"
PAPER_BG = "rgba(22,27,34,0)"

# Apply consistent dark-theme styling to Plotly charts
def chart_layout(fig, height=320):
    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        paper_bgcolor=PAPER_BG,
        plot_bgcolor=CHART_BG,
        height=height,
        margin=dict(l=12, r=12, t=36, b=12),
        font=dict(family="Inter, sans-serif", color="#8b949e"),
        legend=dict(
            bgcolor="rgba(22,27,34,0.7)",
            bordercolor="rgba(48,54,61,0.5)",
            borderwidth=1,
        ),
    )
    fig.update_xaxes(
        showgrid=True, gridcolor="rgba(48,54,61,0.4)",
        zeroline=False, showline=False
    )
    fig.update_yaxes(
        showgrid=True, gridcolor="rgba(48,54,61,0.4)",
        zeroline=False, showline=False
    )
    return fig
