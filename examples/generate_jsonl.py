import json
import random
from faker import Faker

fake = Faker()

output_file = "examples/example.jsonl"

event_types = ["signup", "purchase", "refund", "login", "logout"]

countries = ["Ghana", "Nigeria", "Kenya", "South Africa", "USA", "UK", "Germany", "India", "Brazil"]

# keep some users consistent for realism
user_ids = [random.randint(100, 200) for _ in range(30)]

def generate_amount(event_type):
    if event_type == "signup":
        return 0
    elif event_type == "purchase":
        return round(random.uniform(5, 500), 2)
    elif event_type == "refund":
        return round(random.uniform(-200, -5), 2)
    else:
        return 0

with open(output_file, "w", encoding="utf-8") as f:
    for i in range(150):  # >= 100 rows required
        event_type = random.choice(event_types)
        user_id = random.choice(user_ids)

        record = {
            "event_id": i + 1,
            "event_type": event_type,
            "user_id": user_id,
            "country": random.choice(countries),
            "amount": generate_amount(event_type),
            "currency": "USD",
            "device": random.choice(["mobile", "desktop", "tablet"]),
            "is_success": random.choice([True, True, True, False]),  # mostly success
            "session_id": fake.uuid4(),
            "timestamp": fake.date_time_this_year().isoformat()
        }

        # introduce realistic nulls
        if random.random() < 0.1:
            record["device"] = None

        if random.random() < 0.05:
            record["country"] = None

        f.write(json.dumps(record) + "\n")

print("Generated examples/example.jsonl with 150 event records")