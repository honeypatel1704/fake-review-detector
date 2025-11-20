import pandas as pd

# Read in chunks
chunksize = 100000 
reader = pd.read_json(
    r"D:\Projects\Fake Review Detection\yelp_academic_dataset_review.json",
    lines=True,
    chunksize=chunksize
)

# Save first chunk to CSV in the same folder as this script
for i, chunk in enumerate(reader):
    chunk.to_csv(f"./reviews_part{i}.csv", index=False)  
    print(f"Saved chunk {i}")
    if i == 0:  
        break
