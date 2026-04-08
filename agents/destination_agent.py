from config.mistral_client import call_mistral

def get_destinations(user_request):
    prompt = f"""
You are an expert travel guide and destination specialist.

User request:
{user_request}

IMPORTANT CONTEXT:
- The user will travel directly to the DESTINATION city.
- Do NOT suggest places on the route or stopovers.

TASK:
1. Identify the DESTINATION city.
2. Decide how many places based on days:
   - 1-2 days: 3 to 4 places
   - 3-4 days: 5 to 6 places
   - 5+ days: 7 to 8 places

3. For EACH place provide ALL of the following:
   - Place name
   - Why visit: what makes it special or unique
   - Best time to visit this spot
   - One thing NOT to miss there
   - Approximate entry fee (free or INR amount)

OUTPUT FORMAT (Plain text only):

PLACES TO VISIT IN AND NEAR [DESTINATION CITY]:

1. Place Name
   Why Visit: [what makes it special]
   Best Time: [morning / evening / anytime]
   Don't Miss: [one specific highlight]
   Entry Fee: [free / approx INR]

(continue for all places)

ALSO ADD at the end:

LOCAL FOOD TO TRY:
- dish name: one line description
- dish name: one line description
- dish name: one line description

RULES:
- Be specific, not generic
- No emojis, no markdown, plain text only
"""
    return call_mistral(prompt)