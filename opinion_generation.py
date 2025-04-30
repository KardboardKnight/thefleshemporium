import random

# Lists of possible attributes, feelings, and topics
attributes = [
    "interesting", "boring", "amazing", "terrible", "underrated", "overrated", "confusing", "innovative",
    "fascinating", "dull", "remarkable", "awful", "misunderstood", "overhyped", "puzzling", "groundbreaking",
    "unique", "forgettable", "exciting", "mediocre", "intriguing", "pointless", "refreshing", "uninspired"
]
feelings = ["love", "hate", "appreciate", "don't understand", "am neutral about", "am surprised by"]

def generate_opinion():
    attribute = random.choice(attributes)
    feeling = random.choice(feelings)
    return f"I think you are {attribute}, and I {feeling} that.\n"

if __name__ == "__main__":
    with open("opinion.txt", "w") as file:
        for i in range(255):
            file.write(generate_opinion())
