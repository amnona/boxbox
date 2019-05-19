"""
BOX BOX aws skill for alexa
written by amnonim@gmail.com
Requires the following triggers:
Alexa skill kit trigger

Requires the following triggers:
AWS Systerms manager
Amazon cloudwatch logs

uses the boxit role

For additional samples, visit the Alexa Skills Kit Getting Started guide at
http://amzn.to/1LGWsLG
"""

from __future__ import print_function
import boto3


# --------------- Helpers that build all of the responses ----------------------

def build_speechlet_response(title, output, reprompt_text, should_end_session):
    return {
        'outputSpeech': {
            'type': 'PlainText',
            'text': output
        },
        'card': {
            'type': 'Simple',
            'title': "SessionSpeechlet - " + title,
            'content': "SessionSpeechlet - " + output
        },
        'reprompt': {
            'outputSpeech': {
                'type': 'PlainText',
                'text': reprompt_text
            }
        },
        'shouldEndSession': should_end_session
    }


def build_response(session_attributes, speechlet_response):
    return {
        'version': '1.0',
        'sessionAttributes': session_attributes,
        'response': speechlet_response
    }


# --------------- Functions that control the skill's behavior ------------------

def get_welcome_response():
    """ If we wanted to initialize the session to have some attributes we could
    add those here
    """

    session_attributes = {}
    card_title = "Welcome to box box"
    speech_output = "I am box box. I will help you to keep track of foods in your fridge. " \
                    "You can add a box with food by saying something like:  " \
                    "add fish to box number 4. " \
                    "Or you can ask me where a specific food is by saying:" \
                    "What is in box number 3. " \
                    "You can also get a list of all the items by saying: " \
                    "What is in the fridge?"
    # If the user either does not reply to the welcome message or says something
    # that is not understood, they will be prompted again with this text.
    reprompt_text = "What should i do?" \
                    "you can add a box to the fridge by saying something like: " \
                    "add fish to box number 4. " \
                    "Or you can ask me where a specific food is by saying:" \
                    "What is in box number 3. " \
                    "You can also get a list of all the items by saying: " \
                    "What is in the fridge?"

    should_end_session = False
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))


def handle_session_end_request():
    card_title = "Session Ended"
    speech_output = "Box it will miss you! "
    # Setting this to true ends the session and exits the skill.
    should_end_session = True
    return build_response({}, build_speechlet_response(
        card_title, speech_output, None, should_end_session))


def query_box(intent, session):
    '''what is in box {boxnum}
    '''
    card_title = intent['name']
    session_attributes = {}
    should_end_session = True

    if 'boxnum' not in intent['slots']:
        speech_output = "i didn't get the box number the food is in"
        reprompt_text = "Please say the box number"
        return build_response(session_attributes, build_speechlet_response(card_title, speech_output, reprompt_text, False))
    print('query_box')
    print(intent['slots'])
    print(intent['slots']['boxnum'])
    boxnum = intent['slots']['boxnum']['value']

    ssm = boto3.client('ssm')
    pname = '/boxit/box/%s' % boxnum
    try:
        res = ssm.get_parameter(Name=pname, WithDecryption=False)
    except:
        speech_output = "box %s is not in my fridge list" % boxnum
        reprompt_text = "Please say the box number"
        return build_response(session_attributes, build_speechlet_response(card_title, speech_output, reprompt_text, False))

    box_content = res['Parameter']['Value']
    box_date = res['Parameter']['LastModifiedDate'].date().strftime('%A %B %d')
    speech_output = "box %s contains %s from date %s" % (boxnum, box_content, box_date)
    reprompt_text = 'anything else?'
    return build_response(session_attributes, build_speechlet_response(card_title, speech_output, reprompt_text, False))


def inventory(intent, session):
    '''what is in box {boxnum}
    '''
    card_title = intent['name']
    session_attributes = {}
    should_end_session = True

    ssm = boto3.client('ssm')
    res = ssm.get_parameters_by_path(Path='/boxit/box')

    speech_output = []
    for cbox in res['Parameters']:
        boxnum = cbox['Name'].split('/')[-1]
        box_content = cbox['Value']
        if box_content == 'empty':
            print('box %s empty' % boxnum)
            continue
        box_date = cbox['LastModifiedDate'].date().strftime('%A %B %d')
        speech_output.append("box %s contains %s from date %s" % (boxnum, box_content, box_date))
    speech_output = '. '.join(speech_output)
    reprompt_text = 'anything else?'
    return build_response(session_attributes, build_speechlet_response(card_title, speech_output, reprompt_text, False))


def add_to_fridge(intent, session):
    card_title = intent['name']
    session_attributes = {}
    should_end_session = True

    if 'food' not in intent['slots']:
        speech_output = "i didn't get the food to add to the fridge"
        reprompt_text = "Please say the food to add"
        return build_response(session_attributes, build_speechlet_response(card_title, speech_output, reprompt_text, False))
    if 'boxnum' not in intent['slots']:
        speech_output = "i didn't get the box number the food is in"
        reprompt_text = "Please say the box number"
        return build_response(session_attributes, build_speechlet_response(card_title, speech_output, reprompt_text, False))
    print('add to fridge')
    print(intent['slots'])
    print(intent['slots']['food'])
    print(intent['slots']['boxnum'])

    if 'value' not in intent['slots']['food']:
        speech_output = "i didn't get the food name"
        reprompt_text = "Sorry"
        return build_response(session_attributes, build_speechlet_response(card_title, speech_output, reprompt_text, True))

    food = intent['slots']['food']['value']
    boxnum = intent['slots']['boxnum']['value']

    # use parameter store
    # looked at example at: https://medium.com/@nqbao/how-to-use-aws-ssm-parameter-store-easily-in-python-94fda04fea84
    print('----ssm-----')
    ssm = boto3.client('ssm')
    print('putting parameter')
    pname = '/boxit/box/%s' % boxnum
    ssm.put_parameter(Name=pname, Type='String', Value=food, Overwrite=True)
    # sdb = boto3.client('sdb')
    # response = sdb.create_domain(DomainName='boxit')
    # print(response)
    # response = sdb.list_domains()
    # print("Current domains: %s" % response['DomainNames'])
    # response = sdb.put_attributes(DomainName="boxit",ItemName="pita",Attributes=[
    #     {'Name': 'color', 'Value': color,'Replace': True},])
    # print(response)

    speech_output = "cool. i added food %s to box %s" % (food, boxnum)
    reprompt_text = "food added"
    print("food added")
    return build_response(session_attributes, build_speechlet_response(card_title, speech_output, reprompt_text, True))


def remove_box(intent, session):
    card_title = intent['name']
    session_attributes = {}
    should_end_session = True

    if 'boxnum' not in intent['slots']:
        speech_output = "i didn't get the box number to throw away"
        reprompt_text = "Please say the box number"
        return build_response(session_attributes, build_speechlet_response(card_title, speech_output, reprompt_text, False))
    print('remove_box')

    boxnum = intent['slots']['boxnum']['value']

    # use parameter store
    # looked at example at: https://medium.com/@nqbao/how-to-use-aws-ssm-parameter-store-easily-in-python-94fda04fea84
    print('----ssm-----')
    ssm = boto3.client('ssm')
    print('deleting parameter')
    pname = '/boxit/box/%s' % boxnum
    ssm.put_parameter(Name=pname, Type='String', Value='empty', Overwrite=True)

    speech_output = "i threw away box %s" % boxnum
    reprompt_text = "food removed"
    print("food removed")
    return build_response(session_attributes, build_speechlet_response(card_title, speech_output, reprompt_text, True))


def delete_all(intent, session):
    card_title = intent['name']
    session_attributes = {}
    should_end_session = True

    # use parameter store
    # looked at example at: https://medium.com/@nqbao/how-to-use-aws-ssm-parameter-store-easily-in-python-94fda04fea84
    print('----ssm-----')
    ssm = boto3.client('ssm')
    res = ssm.get_parameters_by_path(Path='/boxit/box')
    print('deleting all')

    num_boxes = 0
    for cbox in res['Parameters']:
        boxnum = cbox['Name'].split('/')[-1]
        pname = '/boxit/box/%s' % boxnum
        ssm.put_parameter(Name=pname, Type='String', Value='empty', Overwrite=True)
        num_boxes += 1
    speech_output = 'deleted %s boxes' % num_boxes

    reprompt_text = "all food removed"
    print("food removed")
    return build_response(session_attributes, build_speechlet_response(card_title, speech_output, reprompt_text, True))


def create_favorite_color_attributes(favorite_color):
    return {"favoriteColor": favorite_color}


def set_color_in_session(intent, session):
    """ Sets the color in the session and prepares the speech to reply to the
    user.
    """

    card_title = intent['name']
    session_attributes = {}
    should_end_session = False

    if 'Color' in intent['slots']:
        favorite_color = intent['slots']['Color']['value']
        session_attributes = create_favorite_color_attributes(favorite_color)
        speech_output = "I now know your favorite color is " + \
                        favorite_color + \
                        ". You can ask me your favorite color by saying, " \
                        "what's my favorite color?"
        reprompt_text = "You can ask me your favorite color by saying, " \
                        "what's my favorite color?"
    else:
        speech_output = "I'm not sure what your favorite color is. " \
                        "Please try again."
        reprompt_text = "I'm not sure what your favorite color is. " \
                        "You can tell me your favorite color by saying, " \
                        "my favorite color is red."
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))


def get_color_from_session(intent, session):
    session_attributes = {}
    reprompt_text = None

    if session.get('attributes', {}) and "favoriteColor" in session.get('attributes', {}):
        favorite_color = session['attributes']['favoriteColor']
        speech_output = "Your favorite color is " + favorite_color + \
                        ". Goodbye."
        should_end_session = True
    else:
        speech_output = "I'm not sure what your favorite color is. " \
                        "You can say, my favorite color is red."
        should_end_session = False

    # Setting reprompt_text to None signifies that we do not want to reprompt
    # the user. If the user does not respond or says something that is not
    # understood, the session will end.
    return build_response(session_attributes, build_speechlet_response(
        intent['name'], speech_output, reprompt_text, should_end_session))


# --------------- Events ------------------

def on_session_started(session_started_request, session):
    """ Called when the session starts """

    print("on_session_started requestId=" + session_started_request['requestId'] + ", sessionId=" + session['sessionId'])


def on_launch(launch_request, session):
    """ Called when the user launches the skill without specifying what they
    want
    """

    print("on_launch requestId=" + launch_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # Dispatch to your skill's launch
    return get_welcome_response()


def on_intent(intent_request, session):
    """ Called when the user specifies an intent for this skill """

    print("on_intent requestId=" + intent_request['requestId'] +
          ", sessionId=" + session['sessionId'])

    intent = intent_request['intent']
    intent_name = intent_request['intent']['name']

    # Dispatch to your skill's intent handlers
    if intent_name == "MyColorIsIntent":
        return set_color_in_session(intent, session)
    elif intent_name == "WhatsMyColorIntent":
        return get_color_from_session(intent, session)
    elif intent_name == "AMAZON.HelpIntent":
        return get_welcome_response()
    elif intent_name == "AMAZON.CancelIntent" or intent_name == "AMAZON.StopIntent":
        return handle_session_end_request()
    elif intent_name == 'add_box':
        return add_to_fridge(intent, session)
    elif intent_name == 'query_box':
        return query_box(intent, session)
    elif intent_name == 'inventory':
        return inventory(intent, session)
    elif intent_name == 'remove_box':
        return remove_box(intent, session)
    elif intent_name == 'delete_all':
        return delete_all(intent, session)
    else:
        return build_response({}, build_speechlet_response("unknown command", "sorry, i don't know how to %s" % intent_name, "i didn't understand", True))
        # raise ValueError("Invalid intent %s" % intent_name)


def on_session_ended(session_ended_request, session):
    """ Called when the user ends the session.

    Is not called when the skill returns should_end_session=true
    """
    print("on_session_ended requestId=" + session_ended_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # add cleanup logic here


# --------------- Main handler ------------------

def lambda_handler(event, context):
    """ Route the incoming request based on type (LaunchRequest, IntentRequest,
    etc.) The JSON body of the request is provided in the event parameter.
    """
    print("event.session.application.applicationId=" +
          event['session']['application']['applicationId'])

    """
    Uncomment this if statement and populate with your skill's application ID to
    prevent someone else from configuring a skill that sends requests to this
    function.
    """
    # if (event['session']['application']['applicationId'] !=
    #         "amzn1.echo-sdk-ams.app.[unique-value-here]"):
    #     raise ValueError("Invalid Application ID")

    if event['session']['new']:
        on_session_started({'requestId': event['request']['requestId']},
                           event['session'])

    if event['request']['type'] == "LaunchRequest":
        return on_launch(event['request'], event['session'])
    elif event['request']['type'] == "IntentRequest":
        return on_intent(event['request'], event['session'])
    elif event['request']['type'] == "SessionEndedRequest":
        return on_session_ended(event['request'], event['session'])
