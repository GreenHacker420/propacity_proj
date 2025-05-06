import tempfile
from weasyprint import HTML
from jinja2 import Template
from ..api.models import AnalysisResults

REPORT_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Product Review Analysis Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        h1 { color: #2c3e50; }
        .summary { background: #f8f9fa; padding: 20px; border-radius: 5px; }
        .metric { margin: 10px 0; }
        .sentiment { margin-top: 30px; }
    </style>
</head>
<body>
    <h1>Product Review Analysis Report</h1>
    
    <div class="summary">
        <div class="metric">
            <strong>Total Reviews:</strong> {{ analysis.review_count }}
        </div>
        <div class="metric">
            <strong>Average Rating:</strong> {{ "%.2f"|format(analysis.average_rating) }}/5.0
        </div>
        <div class="metric">
            <strong>Positive Sentiment Ratio:</strong> 
            {{ "%.2f"|format(sentiment_ratio * 100) }}%
        </div>
    </div>
    
    <div class="sentiment">
        <h2>Sentiment Analysis</h2>
        <p>
            Out of {{ analysis.review_count }} reviews analyzed:
            <ul>
                <li>{{ positive_count }} were positive</li>
                <li>{{ negative_count }} were negative</li>
            </ul>
        </p>
    </div>
</body>
</html>
"""

async def generate_pdf_report(analysis: AnalysisResults) -> str:
    # Calculate sentiment statistics
    positive_count = sum(1 for score in analysis.sentiment_scores if score > 0.5)
    negative_count = len(analysis.sentiment_scores) - positive_count
    sentiment_ratio = positive_count / len(analysis.sentiment_scores) if analysis.sentiment_scores else 0
    
    # Render HTML template
    template = Template(REPORT_TEMPLATE)
    html_content = template.render(
        analysis=analysis,
        positive_count=positive_count,
        negative_count=negative_count,
        sentiment_ratio=sentiment_ratio
    )
    
    # Generate PDF
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
        HTML(string=html_content).write_pdf(tmp.name)
        return tmp.name 