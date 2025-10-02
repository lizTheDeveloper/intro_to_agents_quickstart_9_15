# DataAnalysisAgent README

## Getting Started
1. Navigate to working directory: `cd dataanalysisagent`
2. View analysis template: `cat analysis_template.md`
3. Run example analysis: `python main.py`

## Sample Workflow
```sh
# 1. Research data analysis techniques
python main.py --analyze "regression analysis" "https://example.com/data.csv" "output/report.txt"

# 2. Manage files
ls .           # List files
python main.py --read "data.csv" > content.txt
python main.py --write "output.txt" < results.txt
```

## Validation Process
1. All analyses cross-check 3+ references
2. Uses government/educational sources where possible
3. Documentation stored in `methodology.txt`

## Audit Trail
All operations logged in `analysis_log.txt`