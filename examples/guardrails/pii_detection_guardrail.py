# pip install boto3

import boto3


class AWSGuardRails:

    def __init__(self):
        self.client = boto3.client('bedrock-runtime')

    def detect_pii(self, content, guardrail_id, guardrail_version, TYPE="INPUT"):
        try:
            response = self.client.apply_guardrail(
                guardrailIdentifier=guardrail_id,
                guardrailVersion=guardrail_version,
                source=TYPE,
                content=content
            )

            return {"response": response, "status": "SUCCESS"}

        except Exception as e:
            print("An exception has occured ", e)

    def format_guardrail_response(self, guard_out_content):
        list_of_assessments = []
        assessment_match_type = {}
        output = ""

        guard_response = guard_out_content['response']

        if guard_response['action'] == 'GUARDRAIL_INTERVENED':
            print("\nGuardrail intervened. Output:")
            for output in guard_response['outputs']:
                output = output['text']
            for assessment in guard_response['assessments']:
                # print("assesment ", assessment)
                matches = assessment["sensitiveInformationPolicy"]["piiEntities"]
                for each_match in matches:
                    match = each_match['match']
                    type  = each_match['type']
                    assessment_match_type["match"] = match
                    assessment_match_type["type"] = type
                    list_of_assessments.append(assessment_match_type)
                    assessment_match_type = {}

            return output, list_of_assessments

        else:
            print("\nGuardrail did not intervene.")


if __name__ == "__main__":
    guardrail_id = "talyygy5u2bm"  # Adjust with your Guardrail Info
    guardrail_version = "1"  # Adjust with your Guardrail Info
    content = [
        {
            "text": {
                "text": """Please summarize the meeting between a traveller and a traveller agent
                Traveler (John Smith): Hi, I’m John Smith. I’m looking to book a trip to Italy next month. Could you help me find a good itinerary?
                Agent (Ava Carter): Certainly, John. I’d be happy to assist. Do you have any specific destinations in mind?
                Traveler (John Smith): I’d like to start in Rome and then head down to the Amalfi Coast for a few days. My dates are May 10th to May 20th. Also, I’d need help with accommodations and transportation. Here’s my Social Security Number if you need it for verification: 123-45-6789.
                Agent (Ava Carter): Thank you, John. I’ll note that down. We’ll use it only for your reservation details. Let’s see… Ten days in Italy, starting in Rome and then to Amalfi. I can arrange four nights in Rome, followed by five nights in Positano. For the train and ferry connections, I can handle those bookings as well.
                Traveler (John Smith): Perfect. Just let me know the total. I’ll put it all on my credit card. The number is 4111 2222 3333 4444, expiration 05/27, CVV 123.
                Agent (Ava Carter): Great, thank you for that, John. I’ll proceed with the bookings right now. Once everything is confirmed, I’ll send you a full itinerary, including hotel addresses, confirmation numbers, and recommendations for tours and dining. You should have it in your inbox by this afternoon.
                Traveler (John Smith): Excellent. I’m excited to get this trip finalized. Thanks so much!
                Agent (Ava Carter): My pleasure! I’ll be in touch shortly with all the details. Have a wonderful trip planning experience!
                """
            }
        }
    ]

    aws_guardrails = AWSGuardRails()
    response = aws_guardrails.detect_pii(content=content, guardrail_id=guardrail_id,
                                         guardrail_version=guardrail_version)
    formatted_response = aws_guardrails.format_guardrail_response(response)
    output = formatted_response[0]
    all_matches = formatted_response[1]
    print("Output :", output)
    print("----------------------")
    for each_match in all_matches:
        print("Match :" , each_match['match'])
        print("Type :", each_match['type'])
