import os
import sys
from app.services.process_large_csv import LargeCSVProcessor

def main():
    if len(sys.argv) != 2:
        print("Usage: python process_large_file.py <csv_file_path>")
        sys.exit(1)

    csv_file = sys.argv[1]
    if not os.path.exists(csv_file):
        print(f"Error: File {csv_file} does not exist")
        sys.exit(1)

    # Initialize processor
    processor = LargeCSVProcessor()

    # Process the file
    print(f"Processing {csv_file}...")
    results = processor.process_csv_in_chunks(csv_file)

    # Save results
    output_file = f"{os.path.splitext(csv_file)[0]}_analysis.json"
    processor.save_results(results, output_file)
    print(f"Analysis complete. Results saved to {output_file}")

    # Print summary
    summary = results['summary']
    print("\nAnalysis Summary:")
    print(f"Total Reviews: {summary['total_reviews']}")
    print(f"Average Sentiment: {summary['average_sentiment']:.2f}")
    print("\nSentiment Distribution:")
    for sentiment, count in summary['sentiment_distribution'].items():
        print(f"  {sentiment}: {count}")
    print("\nClassification Distribution:")
    for classification, count in summary['classification_distribution'].items():
        print(f"  {classification}: {count}")
    if summary['average_rating'] is not None:
        print(f"\nAverage Rating: {summary['average_rating']:.2f}")
    print("\nTop Keywords:")
    for keyword, count in list(summary['top_keywords'].items())[:10]:
        print(f"  {keyword}: {count}")

if __name__ == "__main__":
    main() 