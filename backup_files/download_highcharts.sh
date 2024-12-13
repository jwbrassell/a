#!/bin/bash

# Create directories
mkdir -p app/static/src/highcharts/modules
mkdir -p app/static/src/highcharts/themes
mkdir -p app/static/src/highcharts/indicators

# Core files
curl -o app/static/src/highcharts/highcharts.js https://code.highcharts.com/highcharts.js
curl -o app/static/src/highcharts/highcharts-3d.js https://code.highcharts.com/highcharts-3d.js
curl -o app/static/src/highcharts/highcharts-more.js https://code.highcharts.com/highcharts-more.js

# Modules
modules=(
    "accessibility"
    "annotations"
    "annotations-advanced"
    "arrow-symbols"
    "boost"
    "boost-canvas"
    "broken-axis"
    "bullet"
    "coloraxis"
    "cylinder"
    "data"
    "datagrouping"
    "debugger"
    "dependency-wheel"
    "dotplot"
    "drag-panes"
    "draggable-points"
    "drilldown"
    "dumbbell"
    "export-data"
    "exporting"
    "funnel"
    "funnel3d"
    "gauge"
    "grid-axis"
    "heatmap"
    "histogram-bellcurve"
    "item-series"
    "lollipop"
    "marker-clusters"
    "networkgraph"
    "no-data-to-display"
    "offline-exporting"
    "oldie"
    "organization"
    "overlapping-datalabels"
    "parallel-coordinates"
    "pareto"
    "pathfinder"
    "pattern-fill"
    "price-indicator"
    "pyramid3d"
    "sankey"
    "series-label"
    "solid-gauge"
    "sonification"
    "static-scale"
    "stock"
    "streamgraph"
    "sunburst"
    "tilemap"
    "timeline"
    "treegrid"
    "treemap"
    "variable-pie"
    "variwide"
    "vector"
    "venn"
    "windbarb"
    "wordcloud"
    "xrange"
)

for module in "${modules[@]}"
do
    echo "Downloading module: $module"
    curl -o "app/static/src/highcharts/modules/${module}.js" "https://code.highcharts.com/modules/${module}.js"
done

# Themes
themes=(
    "dark-blue"
    "dark-green"
    "dark-unica"
    "gray"
    "grid-light"
    "sand-signika"
    "skies"
    "sunset"
)

for theme in "${themes[@]}"
do
    echo "Downloading theme: $theme"
    curl -o "app/static/src/highcharts/themes/${theme}.js" "https://code.highcharts.com/themes/${theme}.js"
done

# Stock indicators
indicators=(
    "indicators"
    "atr"
    "bollinger-bands"
    "cci"
    "chaikin"
    "cmf"
    "dmi"
    "ema"
    "ichimoku-kinko-hyo"
    "macd"
    "mfi"
    "momentum"
    "pivot-points"
    "price-channel"
    "price-envelopes"
    "psar"
    "roc"
    "rsi"
    "stochastic"
    "supertrend"
    "volume-by-price"
    "vwap"
    "wma"
    "zigzag"
)

for indicator in "${indicators[@]}"
do
    echo "Downloading indicator: $indicator"
    curl -o "app/static/src/highcharts/indicators/${indicator}.js" "https://code.highcharts.com/stock/indicators/${indicator}.js"
done

echo "Download complete!"
