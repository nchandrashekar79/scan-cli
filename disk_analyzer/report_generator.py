"""HTML report generator - creates an interactive disk usage report."""

import json
import os
from typing import Dict

from disk_analyzer.config import Config

# ---------------------------------------------------------------------------
# CSS
# ---------------------------------------------------------------------------
CSS = """
:root {
    --bg: #0f172a;
    --surface: #1e293b;
    --surface-2: #334155;
    --border: #475569;
    --text: #f1f5f9;
    --text-muted: #94a3b8;
    --accent: #3b82f6;
    --accent-hover: #2563eb;
    --green: #22c55e;
    --red: #ef4444;
    --orange: #f59e0b;
    --radius: 12px;
    --shadow: 0 4px 24px rgba(0,0,0,0.3);
}
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: 'Segoe UI', system-ui, sans-serif; background: var(--bg);
       color: var(--text); line-height: 1.6; min-height: 100vh; }
.container { max-width: 1400px; margin: 0 auto; padding: 24px; }

/* Header */
header { text-align: center; padding: 40px 20px 30px; }
header h1 { font-size: 2.2rem; font-weight: 700; background: linear-gradient(135deg, #3b82f6, #8b5cf6);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
header p { color: var(--text-muted); margin-top: 8px; font-size: 1rem; }
header .scan-path { display: inline-block; background: var(--surface-2); padding: 4px 14px;
                    border-radius: 20px; font-size: 0.85rem; margin-top: 8px;
                    color: var(--text-muted); font-family: monospace; }

/* Stats Grid */
.stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
              gap: 16px; margin: 30px 0; }
.stat-card { background: var(--surface); border-radius: var(--radius); padding: 20px;
             border: 1px solid var(--border); transition: transform 0.2s, box-shadow 0.2s; }
.stat-card:hover { transform: translateY(-2px); box-shadow: var(--shadow); }
.stat-card .label { font-size: 0.8rem; text-transform: uppercase; letter-spacing: 1px;
                    color: var(--text-muted); }
.stat-card .value { font-size: 1.6rem; font-weight: 700; margin-top: 4px; }
.stat-card .sub { font-size: 0.8rem; color: var(--text-muted); margin-top: 2px; }

/* Charts Section */
.charts-section { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin: 30px 0; }
@media (max-width: 900px) { .charts-section { grid-template-columns: 1fr; } }
.chart-card { background: var(--surface); border-radius: var(--radius); padding: 20px;
              border: 1px solid var(--border); }
.chart-card h3 { font-size: 1rem; margin-bottom: 16px; color: var(--text-muted); }
.chart-card canvas { max-height: 350px; }

/* Treemap */
.treemap-container { background: var(--surface); border-radius: var(--radius); padding: 20px;
                     border: 1px solid var(--border); margin: 30px 0; }
.treemap-container h3 { font-size: 1rem; margin-bottom: 16px; color: var(--text-muted); }
#treemap { width: 100%; height: 500px; }
#treemap svg { width: 100%; height: 100%; }
.treemap-tooltip { position: absolute; background: var(--surface-2); color: var(--text);
                   padding: 8px 14px; border-radius: 8px; font-size: 0.85rem;
                   pointer-events: none; opacity: 0; transition: opacity 0.2s;
                   border: 1px solid var(--border); z-index: 100; }

/* Table Section */
.table-section { margin: 30px 0; }
.table-controls { display: flex; gap: 12px; align-items: center; margin-bottom: 16px;
                  flex-wrap: wrap; }
.table-controls input { flex: 1; min-width: 200px; padding: 10px 16px; border-radius: 8px;
                        border: 1px solid var(--border); background: var(--surface);
                        color: var(--text); font-size: 0.9rem; outline: none; }
.table-controls input:focus { border-color: var(--accent); }
.table-controls input::placeholder { color: var(--text-muted); }
.table-controls .file-count { color: var(--text-muted); font-size: 0.85rem;
                              white-space: nowrap; }
.table-wrapper { overflow-x: auto; border-radius: var(--radius);
                 border: 1px solid var(--border); background: var(--surface); }
table { width: 100%; border-collapse: collapse; font-size: 0.85rem; }
thead { background: var(--surface-2); position: sticky; top: 0; }
th { padding: 12px 16px; text-align: left; cursor: pointer; user-select: none;
     white-space: nowrap; font-weight: 600; }
th:hover { color: var(--accent); }
th .sort-icon { margin-left: 6px; opacity: 0.4; }
th.sorted .sort-icon { opacity: 1; }
td { padding: 10px 16px; border-top: 1px solid var(--border); max-width: 400px;
     overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
tr:hover td { background: rgba(59,130,246,0.08); }
.size-cell { text-align: right; font-family: monospace; white-space: nowrap; }
.path-cell { font-family: monospace; font-size: 0.8rem; color: var(--text-muted); }

/* No results */
.no-results { text-align: center; padding: 40px; color: var(--text-muted); }

/* Footer */
footer { text-align: center; padding: 30px; color: var(--text-muted); font-size: 0.8rem; }
"""

# ---------------------------------------------------------------------------
# HTML Template
# ---------------------------------------------------------------------------
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Disk Storage Analyzer</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.7/dist/chart.umd.min.js"></script>
<script src="https://d3js.org/d3.v7.min.js"></script>
<style>
{STYLES}
</style>
</head>
<body>
<div class="container">

<header>
    <h1>💾 Disk Storage Analyzer</h1>
    <p>Interactive report to identify storage consumption</p>
    <span class="scan-path">📁 {SCAN_PATH}</span>
</header>

<!-- Stats -->
<div class="stats-grid" id="statsGrid"></div>

<!-- Treemap -->
<div class="treemap-container">
    <h3>📦 Folder Size Treemap (hover to explore, click to zoom)</h3>
    <div id="treemap"></div>
</div>

<!-- Charts -->
<div class="charts-section">
    <div class="chart-card">
        <h3>🧩 Storage by File Extension</h3>
        <canvas id="pieChart"></canvas>
    </div>
    <div class="chart-card">
        <h3>📊 Top 20 Folders by Size</h3>
        <canvas id="barChart"></canvas>
    </div>
</div>

<!-- Table -->
<div class="table-section">
    <div class="table-controls">
        <input type="text" id="searchBox" placeholder="🔍 Search files by name or path..." oninput="filterTable()" />
        <span class="file-count" id="fileCount"></span>
    </div>
    <div class="table-wrapper">
        <table>
            <thead>
                <tr>
                    <th onclick="sortTable('name')">Name <span class="sort-icon">↕</span></th>
                    <th onclick="sortTable('size')" class="sorted">Size <span class="sort-icon">↕</span></th>
                    <th onclick="sortTable('path')">Path <span class="sort-icon">↕</span></th>
                    <th onclick="sortTable('extension')">Type <span class="sort-icon">↕</span></th>
                    <th onclick="sortTable('modified')">Modified <span class="sort-icon">↕</span></th>
                </tr>
            </thead>
            <tbody id="fileTableBody"></tbody>
        </table>
    </div>
    <div id="noResults" class="no-results" style="display:none;">No files match your search.</div>
</div>

<footer>Generated by Disk Storage Analyzer &mdash; {SCAN_TIME}</footer>

</div>

<script>
// ===== DATA =====
const REPORT_DATA = {REPORT_DATA};

// ===== HELPERS =====
function fmtSize(bytes) {{
    if (bytes === 0) return '0 B';
    const units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB'];
    const k = 1024;
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    const val = (bytes / Math.pow(k, i)).toFixed(i > 0 ? 1 : 0);
    return val + ' ' + units[i];
}}

function fmtDate(iso) {{
    if (!iso) return '-';
    const d = new Date(iso);
    return d.toLocaleDateString() + ' ' + d.toLocaleTimeString([], {{hour:'2-digit',minute:'2-digit'}});
}}

// ===== STATS =====
function renderStats(summary, scanInfo) {{
    const grid = document.getElementById('statsGrid');
    grid.innerHTML = `
        <div class="stat-card"><div class="label">Total Size</div><div class="value">${{fmtSize(summary.total_size)}}</div><div class="sub">${{scanInfo.total_files_scanned.toLocaleString()}} files scanned</div></div>
        <div class="stat-card"><div class="label">Total Files</div><div class="value">${{summary.total_files.toLocaleString()}}</div><div class="sub">Across ${{scanInfo.total_folders.toLocaleString()}} folders</div></div>
        <div class="stat-card"><div class="label">Largest File</div><div class="value">${{fmtSize(summary.largest_file_size)}}</div><div class="sub" title="${{summary.largest_file}}">${{summary.largest_file_name}}</div></div>
        <div class="stat-card"><div class="label">Average File Size</div><div class="value">${{fmtSize(summary.average_file_size)}}</div><div class="sub">${{scanInfo.total_extensions}} file types found</div></div>
    `;
}}

// ===== TREEMAP (D3.js) =====
let currentTreemapRoot = null;
function renderTreemap(folders) {{
    const container = document.getElementById('treemap');
    container.innerHTML = '';
    const width = container.clientWidth || 900;
    const height = 500;

    // Build hierarchy: root -> drive letters -> folders
    const root = {{ name: 'root', children: [] }};
    const driveMap = {{}};

    for (const f of folders) {{
        const parts = f.path.split(/[/\\\\]/);
        const drive = parts[0] || 'Unknown';
        if (!driveMap[drive]) {{
            driveMap[drive] = {{ name: drive, children: [] }};
        }}
        driveMap[drive].children.push({{
            name: parts[parts.length-1] || f.path,
            path: f.path,
            size: f.total_size,
            value: f.total_size,
            fileCount: f.file_count
        }});
    }}

    for (const drive of Object.values(driveMap)) {{
        root.children.push(drive);
    }}

    const svg = d3.select('#treemap')
        .append('svg')
        .attr('viewBox', [0, 0, width, height]);

    const treemapLayout = d3.treemap()
        .size([width, height])
        .paddingOuter(3)
        .paddingInner(1)
        .tile(d3.treemapSquarify);

    const hierarchy = d3.hierarchy(root)
        .sum(d => d.value || 0)
        .sort((a, b) => (b.value || 0) - (a.value || 0));

    treemapLayout(hierarchy);

    const color = d3.scaleOrdinal(d3.schemeSet3);

    const cell = svg.selectAll('g')
        .data(hierarchy.leaves())
        .join('g')
        .attr('transform', d => `translate(${{d.x0}},${{d.y0}})`);

    cell.append('rect')
        .attr('width', d => Math.max(0, d.x1 - d.x0))
        .attr('height', d => Math.max(0, d.y1 - d.y0))
        .attr('fill', (d, i) => color(i % 12))
        .attr('stroke', 'var(--bg)')
        .attr('stroke-width', 2)
        .attr('rx', 4)
        .style('cursor', 'pointer')
        .on('mouseover', function(ev, d) {{
            d3.select(this).attr('opacity', 0.8);
            tooltip.style('opacity', 1)
                .html(`<strong>${{d.data.name}}</strong><br>Path: ${{d.data.path || d.data.name}}<br>Size: ${{fmtSize(d.value)}}<br>Files: ${{d.data.fileCount || 'N/A'}}`)
                .style('left', (ev.pageX + 12) + 'px')
                .style('top', (ev.pageY - 10) + 'px');
        }})
        .on('mouseout', function() {{
            d3.select(this).attr('opacity', 1);
            tooltip.style('opacity', 0);
        }});

    // Text labels - only show if big enough
    cell.append('text')
        .attr('x', 6)
        .attr('y', 16)
        .text(d => {{ const w = d.x1 - d.x0; return w > 80 ? d.data.name : ''; }})
        .attr('font-size', '11px')
        .attr('fill', '#1e293b')
        .attr('font-weight', '600')
        .style('pointer-events', 'none');

    cell.append('text')
        .attr('x', 6)
        .attr('y', 30)
        .text(d => {{ const w = d.x1 - d.x0; return w > 80 ? fmtSize(d.value) : ''; }})
        .attr('font-size', '10px')
        .attr('fill', '#334155')
        .style('pointer-events', 'none');

    const tooltip = d3.select('.treemap-container')
        .append('div')
        .attr('class', 'treemap-tooltip');
}}

// ===== PIE CHART (Chart.js) =====
let pieChartInstance = null;
function renderPieChart(extensions) {{
    const ctx = document.getElementById('pieChart').getContext('2d');
    if (pieChartInstance) pieChartInstance.destroy();
    const labels = extensions.map(e => e.extension);
    const data = extensions.map(e => e.total_size);
    const colors = d3.schemeSet3.slice(0, labels.length);
    pieChartInstance = new Chart(ctx, {{
        type: 'pie',
        data: {{
            labels,
            datasets: [{{
                data,
                backgroundColor: colors,
                borderColor: '#0f172a',
                borderWidth: 2
            }}]
        }},
        options: {{
            responsive: true,
            maintainAspectRatio: true,
            plugins: {{
                legend: {{ position: 'right', labels: {{ color: '#94a3b8', padding: 12 }} }},
                tooltip: {{
                    callbacks: {{
                        label: ctx => {{
                            const total = ctx.dataset.data.reduce((a,b)=>a+b,0);
                            const pct = ((ctx.raw / total) * 100).toFixed(1);
                            return ` ${{ctx.label}}: ${{fmtSize(ctx.raw)}} (${{pct}}%)`;
                        }}
                    }}
                }}
            }}
        }}
    }});
}}

// ===== BAR CHART (Chart.js) =====
let barChartInstance = null;
function renderBarChart(folders) {{
    const ctx = document.getElementById('barChart').getContext('2d');
    if (barChartInstance) barChartInstance.destroy();
    const top20 = folders.slice(0, 20);
    const labels = top20.map(f => {{
        const parts = f.path.split(/[/\\\\]/);
        return parts[parts.length-1] || f.path;
    }});
    const data = top20.map(f => f.total_size);
    barChartInstance = new Chart(ctx, {{
        type: 'bar',
        data: {{
            labels,
            datasets: [{{
                label: 'Folder Size',
                data,
                backgroundColor: '#3b82f6',
                borderRadius: 4,
                borderSkipped: false
            }}]
        }},
        options: {{
            responsive: true,
            maintainAspectRatio: true,
            indexAxis: 'y',
            plugins: {{
                legend: {{ display: false }},
                tooltip: {{
                    callbacks: {{
                        label: ctx => fmtSize(ctx.raw)
                    }}
                }}
            }},
            scales: {{
                x: {{
                    ticks: {{
                        color: '#94a3b8',
                        callback: v => fmtSize(v)
                    }},
                    grid: {{ color: '#334155' }}
                }},
                y: {{
                    ticks: {{ color: '#94a3b8', font: {{ size: 10 }} }},
                    grid: {{ display: false }}
                }}
            }}
        }}
    }});
}}

// ===== TABLE =====
let currentFiles = [];
let sortKey = 'size';
let sortAsc = false;

function sortTable(key) {{
    if (sortKey === key) {{
        sortAsc = !sortAsc;
    }} else {{
        sortKey = key;
        sortAsc = key === 'size';
    }}
    // Update sort indicators
    document.querySelectorAll('th').forEach(th => th.classList.remove('sorted'));
    const headers = document.querySelectorAll('th');
    headerMap = {{ 'name': 0, 'size': 1, 'path': 2, 'extension': 3, 'modified': 4 }};
    const idx = headerMap[key];
    if (headers[idx]) headers[idx].classList.add('sorted');
    renderTable();
}}

function filterTable() {{
    renderTable();
}}

function renderTable() {{
    const query = document.getElementById('searchBox').value.toLowerCase().trim();
    const tbody = document.getElementById('fileTableBody');
    const noResults = document.getElementById('noResults');

    let filtered = REPORT_DATA.files;
    if (query) {{
        filtered = filtered.filter(f =>
            f.name.toLowerCase().includes(query) ||
            f.path.toLowerCase().includes(query)
        );
    }}

    // Sort
    filtered.sort((a, b) => {{
        let va = a[sortKey], vb = b[sortKey];
        if (sortKey === 'size') {{
            return sortAsc ? va - vb : vb - va;
        }}
        va = (va || '').toLowerCase();
        vb = (vb || '').toLowerCase();
        if (va < vb) return sortAsc ? -1 : 1;
        if (va > vb) return sortAsc ? 1 : -1;
        return 0;
    }});

    document.getElementById('fileCount').textContent =
        `${{filtered.length.toLocaleString()}} of ${{REPORT_DATA.files.length.toLocaleString()}} files`;

    if (filtered.length === 0) {{
        tbody.innerHTML = '';
        noResults.style.display = 'block';
        return;
    }}
    noResults.style.display = 'none';

    let html = '';
    for (const f of filtered) {{
        html += `<tr>
            <td>${{f.name}}</td>
            <td class="size-cell">${{fmtSize(f.size)}}</td>
            <td class="path-cell" title="${{f.path}}">${{f.path}}</td>
            <td>${{f.extension}}</td>
            <td>${{fmtDate(f.modified)}}</td>
        </tr>`;
    }}
    tbody.innerHTML = html;
}}

// ===== INIT =====
document.addEventListener('DOMContentLoaded', () => {{
    renderStats(REPORT_DATA.summary, REPORT_DATA.scan_info);
    renderTreemap(REPORT_DATA.folders);
    renderPieChart(REPORT_DATA.extensions);
    renderBarChart(REPORT_DATA.folders);
    renderTable();
    window.addEventListener('resize', () => {{
        renderTreemap(REPORT_DATA.folders);
    }});
}});
</script>
</body>
</html>
"""


def generate_report(config: Config, data: Dict, scan_path: str) -> str:
    """
    Generate the HTML report file.

    Args:
        config: Application configuration.
        data: Aggregated report data (from aggregator.aggregate()).
        scan_path: The path that was scanned.

    Returns:
        Path to the generated HTML file.
    """
    import datetime

    report_data_json = json.dumps(data, ensure_ascii=False)

    html = (
        HTML_TEMPLATE.replace("{STYLES}", CSS)
        .replace("{SCAN_PATH}", scan_path)
        .replace("{SCAN_TIME}", datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
        .replace("{REPORT_DATA}", report_data_json)
    )

    output_path = config.output_file
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    return os.path.abspath(output_path)
