from forecasting_engine import forecasting_engine
r = forecasting_engine.predict_and_recommend(
    rank=2000, 
    category='BC-B', 
    gender='GIRLS', 
    branch='ELECTRONICS AND COMMUNICATION ENGINEERING', 
    counselling_round='Phase 1', 
    region='SVU'
)
print(f'SVU+ECE+BC-B Results: {len(r)}')
for x in r[:5]:
    print(f'  {x["college_name"]} | {x["classification"]} | {x["admission_probability"]}%')
