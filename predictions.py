import pandas as pd
from final_recommend_eng import SHLRecommendationEngine

print("=" * 80)
print("GENERATING TEST PREDICTIONS")
print("=" * 80)

# Load test queries
test_df = pd.read_csv('Test_file.csv')
print(f"\n📊 Loaded {len(test_df)} test queries\n")

# Initialize engine
engine = SHLRecommendationEngine()

# Generate predictions
all_predictions = []

for i, query in enumerate(test_df['Query'], 1):
    print(f"[{i}/{len(test_df)}] Processing query...")
    print(f"   Query: {query[:80]}...")
    
    # Get recommendations
    recommendations = engine.get_recommendations(query, top_k=10)
    
    if recommendations:
        print(f"   ✅ Generated {len(recommendations)} recommendations")
        
        for rec in recommendations:
            all_predictions.append({
                'Query': query,
                'Assessment_url': rec['url']
            })
    else:
        print(f"   ⚠️  WARNING: No recommendations found!")
        print(f"   This query will have 0 predictions in output.")

print(f"\n{'=' * 80}")
print(f"SUMMARY")
print(f"{'=' * 80}")

# Save predictions
pred_df = pd.DataFrame(all_predictions)
pred_df.to_csv('test_predictions.csv', index=False)

print(f"\n✅ Saved {len(pred_df)} predictions to test_predictions.csv")

# Check coverage
queries_with_predictions = pred_df['Query'].nunique()
print(f"📊 Coverage: {queries_with_predictions}/{len(test_df)} queries have predictions")

if queries_with_predictions < len(test_df):
    print(f"\n⚠️  WARNING: {len(test_df) - queries_with_predictions} queries have NO predictions!")
    
    # Find queries with no predictions
    predicted_queries = set(pred_df['Query'].unique())
    all_queries = set(test_df['Query'].unique())
    missing = all_queries - predicted_queries
    
    print(f"\nQueries with NO predictions:")
    for q in missing:
        print(f"   - {q[:100]}...")

# Show sample
print(f"\n{'=' * 80}")
print("SAMPLE PREDICTIONS:")
print(f"{'=' * 80}\n")
print(pred_df.head(15))

print(f"\n✅ Done! File ready for submission: test_predictions.csv")