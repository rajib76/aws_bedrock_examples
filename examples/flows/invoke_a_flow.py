import boto3

client_runtime = boto3.client('bedrock-agent-runtime')

transcipt="""
Traveler (John Smith): Hi, I’m John Smith. I’m looking to book a trip to Italy next month. Could you help me find a good itinerary?
Agent (Ava Carter): Certainly, John. I’d be happy to assist. Do you have any specific destinations in mind?
Traveler (John Smith): I’d like to start in Rome and then head down to the Amalfi Coast for a few days. My dates are May 10th to May 20th. Also, I’d need help with accommodations and transportation. Here’s my Social Security Number if you need it for verification: 123-45-6789.
Agent (Ava Carter): Thank you, John. I’ll note that down. We’ll use it only for your reservation details. Let’s see… Ten days in Italy, starting in Rome and then to Amalfi. I can arrange four nights in Rome, followed by five nights in Positano. For the train and ferry connections, I can handle those bookings as well.
Traveler (John Smith): Perfect. Just let me know the total. I’ll put it all on my credit card. The number is 4111 2222 3333 4444, expiration 05/27, CVV 123.
Agent (Ava Carter): Great, thank you for that, John. I’ll proceed with the bookings right now. Once everything is confirmed, I’ll send you a full itinerary, including hotel addresses, confirmation numbers, and recommendations for tours and dining. You should have it in your inbox by this afternoon.
Traveler (John Smith): Excellent. I’m excited to get this trip finalized. Thanks so much
Agent (Ava Carter): My pleasure! I’ll be in touch shortly with all the details. Have a wonderful trip planning experience!
"""

response = client_runtime.invoke_flow(
    flowIdentifier="XMMKB3V7WY", # Get the flow ID
    flowAliasIdentifier="U9WJ8EDSI0", # Get the flow alias id
    inputs=[
        {
            "content": {"document":str(transcipt)},
            "nodeName": "FlowInputNode",
            "nodeOutputName": "document"
        }
    ]
)

result = {}

for event in response.get("responseStream"):
    result.update(event)

if result['flowCompletionEvent']['completionReason'] == 'SUCCESS':
    print("Flow invocation was successful! The output of the &pf; is as follows:\n")
    print("result:\n\n" , result)
    print("content: \n\n", result['flowOutputEvent']['content']['document'])

else:
    print("The &pf; invocation completed because of the following reason:", result['flowCompletionEvent']['completionReason'])