# Example Output

This folder contains sample output from the Trust-Aware Web Audit Tool.

| File | Description |
|------|-------------|
| **sample-report.html** | Full HTML report (executive summary, scores, quick wins, issues by category). Open in a browser to view. |
| **sample-report.json** | Same audit as JSON (for API consumers). |

## Regenerate samples

After installing dependencies, you can regenerate example output:

```bash
# From project root
python cli.py https://example.com --max-pages 3 --output examples/sample-report.html
```

For JSON, run the web app and visit:
`http://127.0.0.1:8000/audit/json?url=https://example.com&max_pages=3`
