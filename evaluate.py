#!/usr/bin/env python3
"""
Final Evaluation Script - Assignment Compliant
Computes Mean Recall@10 as specified in assignment
"""
import pandas as pd
from final_recommend_eng import SHLRecommendationEngine
import json


def normalize_url(url: str) -> str:
    """Normalize URL for comparison."""
    return url.strip().lower()


def main():
    print("="*80)
    print("FINAL EVALUATION - MEAN RECALL@10")
    print("="*80)
    
    # Load training data
    print("\n📂 Loading Train_file.csv...")
    train = pd.read_csv("Train_file.csv")
    train['Assessment_url'] = train['Assessment_url'].apply(normalize_url)
    
    print(f"✅ Loaded {len(train)} training examples")
    print(f"   From {train['Query'].nunique()} unique queries")
    
    # Initialize engine
    print("\n🚀 Initializing recommendation engine...")
    engine = SHLRecommendationEngine()
    
    # Generate predictions for each query
    print("\n" + "="*80)
    print("GENERATING PREDICTIONS")
    print("="*80)
    
    all_predictions = []
    query_metrics = []
    
    for query_num, query in enumerate(train['Query'].unique(), 1):
        print(f"\n📝 Query {query_num}: {query[:70]}...")
        
        # Get ground truth
        ground_truth = set(train[train['Query'] == query]['Assessment_url'])
        print(f"   Ground truth: {len(ground_truth)} assessments")
        
        # Get recommendations
        recommendations = engine.get_recommendations(query, top_k=10)
        pred_urls = [normalize_url(rec['url']) for rec in recommendations]
        
        print(f"   Predicted: {len(pred_urls)} assessments")
        
        # Calculate Recall@10
        matched = set(pred_urls[:10]) & ground_truth
        recall_at_10 = len(matched) / len(ground_truth) if ground_truth else 0.0
        
        print(f"   ✅ Matched: {len(matched)}/{len(ground_truth)}")
        print(f"   📊 Recall@10: {recall_at_10:.2%}")
        
        # Store predictions in required format
        for url in pred_urls:
            all_predictions.append({
                'Query': query,
                'Assessment_url': url
            })
        
        # Store metrics
        query_metrics.append({
            'query_num': query_num,
            'query': query[:100],
            'ground_truth_count': len(ground_truth),
            'matched_count': len(matched),
            'recall_at_10': recall_at_10
        })
        
        # Show what matched
        if matched:
            print(f"   ✓ Matched URLs:")
            for url in list(matched)[:3]:
                print(f"     - .../{url.split('/')[-2] if '/' in url else url}")
    
    # Calculate Mean Recall@10
    print("\n" + "="*80)
    print("FINAL RESULTS")
    print("="*80)
    
    mean_recall_10 = sum(m['recall_at_10'] for m in query_metrics) / len(query_metrics)
    
    print(f"\n🎯 MEAN RECALL@10: {mean_recall_10:.4f} ({mean_recall_10*100:.2f}%)")
    print(f"\n📊 Per-Query Breakdown:")
    print("-" * 80)
    
    for m in query_metrics:
        status = "✅" if m['recall_at_10'] >= 0.5 else "⚠️" if m['recall_at_10'] > 0 else "❌"
        print(f"{status} Query {m['query_num']}: {m['matched_count']}/{m['ground_truth_count']} = {m['recall_at_10']:.0%}")
    
    # Save predictions in assignment format
    pred_df = pd.DataFrame(all_predictions)
    pred_df.to_csv('predictions.csv', index=False)
    print(f"\n💾 Predictions saved to: predictions.csv")
    print(f"   Format: Query | Assessment_url (Assignment compliant)")
    
    # Save detailed results
    results = {
        'mean_recall_at_10': mean_recall_10,
        'total_queries': len(query_metrics),
        'per_query_metrics': query_metrics
    }
    
    with open('evaluation_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"📈 Detailed metrics saved to: evaluation_results.json")
    
    # Analysis
    print("\n" + "="*80)
    print("ANALYSIS")
    print("="*80)
    
    high_recall = sum(1 for m in query_metrics if m['recall_at_10'] >= 0.5)
    some_recall = sum(1 for m in query_metrics if 0 < m['recall_at_10'] < 0.5)
    zero_recall = sum(1 for m in query_metrics if m['recall_at_10'] == 0)
    
    print(f"\n📊 Performance Distribution:")
    print(f"   ✅ High Recall (≥50%): {high_recall}/{len(query_metrics)} queries")
    print(f"   ⚠️  Some Recall (1-49%): {some_recall}/{len(query_metrics)} queries")
    print(f"   ❌ Zero Recall (0%): {zero_recall}/{len(query_metrics)} queries")
    
    if mean_recall_10 < 0.3:
        print(f"\n⚠️  Low recall detected. Possible reasons:")
        print(f"   1. Training assessments may be pre-packaged solutions (correctly excluded)")
        print(f"   2. Need stronger semantic matching for technical terms")
        print(f"   3. Training data may use different assessment versions")
    elif mean_recall_10 < 0.5:
        print(f"\n✅ Decent recall. Room for improvement:")
        print(f"   1. Fine-tune TF-IDF weights")
        print(f"   2. Add more domain-specific keywords")
        print(f"   3. Improve training boost factors")
    else:
        print(f"\n🎉 Great performance! System is working well.")
    
    print("\n" + "="*80)


if __name__ == "__main__":
    main()