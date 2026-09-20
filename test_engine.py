"""
Test the forecasting engine directly to verify it returns results.
"""
from forecasting_engine import forecasting_engine

print("Testing ForecastingEngine...")
print("-" * 60)

# Test 1: OC Male AU CSE Rank 5000
print("\nTest 1: OC/Male/AU/CSE/Rank 5000/Phase 1")
results = forecasting_engine.predict_and_recommend(
    rank=5000,
    category="OC",
    gender="BOYS",
    branch="COMPUTER SCIENCE AND ENGINEERING",
    counselling_round="Phase 1",
    region="AU"
)
print(f"  Total Recommendations: {len(results)}")
if results:
    print(f"  Top College: {results[0]['college_name']}")
    print(f"  Top Probability: {results[0]['admission_probability']}%")
    print(f"  Classification: {results[0]['classification']}")
    print(f"  Expected Cutoff: {results[0]['expected_cutoff']}")
    
    # Count by classification
    from collections import Counter
    counts = Counter(r['classification'] for r in results)
    print(f"\n  Classification breakdown:")
    for cls, cnt in counts.items():
        print(f"    {cls}: {cnt}")

# Test 2: BC-B Female SVU ECE
print("\nTest 2: BC-B/GIRLS/SVU/ECE/Rank 2000/Phase 2")
results2 = forecasting_engine.predict_and_recommend(
    rank=2000,
    category="BC-B",
    gender="GIRLS",
    branch="ELECTRONICS AND COMMUNICATION ENGINEERING",
    counselling_round="Phase 2",
    region="SVU"
)
print(f"  Total Recommendations: {len(results2)}")
if results2:
    print(f"  Top College: {results2[0]['college_name']}")
    print(f"  Top Probability: {results2[0]['admission_probability']}%")
    print(f"  Classification: {results2[0]['classification']}")

# Test 3: SC Category
print("\nTest 3: SC/Male/AU/MECH/Rank 8000")
results3 = forecasting_engine.predict_and_recommend(
    rank=8000,
    category="SC",
    gender="BOYS",
    branch="MECHANICAL ENGINEERING",
    counselling_round="Phase 1",
    region="AU"
)
print(f"  Total Recommendations: {len(results3)}")
if results3:
    print(f"  Top College: {results3[0]['college_name']}")
    print(f"  Classification: {results3[0]['classification']}")

print("\n" + "=" * 60)
print("ForecastingEngine tests complete.")
