# from config.mistral_client import call_mistral

# def get_transport(from_city, to_city, transport_type):
#     prompt = f"""
# Suggest best {transport_type} options from {from_city} to {to_city}.

# Include:
# - Approximate travel time
# - Approximate cost

# RULES:
# - Keep suggestions realistic
# - Plain text only
# """

#     return call_mistral(prompt)
from config.mistral_client import call_mistral

def get_transport(from_city, to_city, transport_type):
    prompt = f"""
You are a real-world transport planning agent.

Trip Details:
From: {from_city}
To: {to_city}
Preferred Transport: {transport_type}

CRITICAL RULES (FOLLOW STRICTLY):
- Do NOT assume every city has a railway station.
- If the source city does NOT have a railway station:
  - Clearly state: "No railway station in {from_city}"
  - First suggest travel by BUS to the nearest railway station city
  - Then suggest TRAIN from that railway station to destination
- Do NOT invent station codes or train numbers.
- Avoid hallucinated transport routes.
- Give step-by-step travel instructions.
- Provide approximate travel time and cost.
- End with a FINAL RECOMMENDATION.
- Plain text only.

OUTPUT FORMAT (IMPORTANT):

Transport Availability:
- Direct Train: Available / Not Available (with reason)

If Not Available:
Step 1: Bus from source to nearest railway station city
Step 2: Train from nearest railway station to destination

Also suggest:
- Direct Bus option (if available)

Now generate the transport plan realistically.
"""

    return call_mistral(prompt)
