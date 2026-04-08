from config.mistral_client import call_mistral


def get_day_plan(to_city, days, destinations_text, weather_text, extra=""):
    prompt = f"""
You are an expert travel itinerary planner.

Trip Details:
- Destination: {to_city}
- Duration: {days} days
- User preferences: {extra if extra else "general sightseeing"}

Already suggested destinations:
{destinations_text[:800]}

Weather condition:
{weather_text[:300]}

TASK:
Create a detailed day-by-day itinerary for {days} days in {to_city}.
Use the suggested destinations above and distribute them smartly across the days.
Do NOT repeat the same place in multiple days.

OUTPUT FORMAT (Plain text only, strictly follow this):

DAY 1:
Morning (9:00 AM - 12:00 PM):
- Place: [place name]
- Activity: [what to do there]
- Travel Tip: [how to reach from hotel or previous spot]
- Est. Cost: [INR amount or free]

Afternoon (12:00 PM - 4:00 PM):
- Place: [place name]
- Activity: [what to do there]
- Travel Tip: [how to reach from previous spot]
- Est. Cost: [INR amount or free]

Evening (4:00 PM - 8:00 PM):
- Place: [place name]
- Activity: [what to do there]
- Travel Tip: [how to reach from previous spot]
- Est. Cost: [INR amount or free]

Day Summary: [one motivating line summarizing the day experience]

DAY 2:
(same format...)

(continue for all {days} days)

RULES:
- Only suggest places IN {to_city}, not nearby cities
- Keep costs realistic for Indian travel
- Morning should always start fresh from hotel area
- Plain text only, no markdown, no emojis
- Every day MUST have all 3 time slots: Morning, Afternoon, Evening
- Day Summary is required at end of each day
"""
    return call_mistral(prompt)