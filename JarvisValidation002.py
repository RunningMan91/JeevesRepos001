import json
import datetime
import time
import os
import dateutil.parser
import logging


logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


# --- Helpers that build all of the responses ---


def elicit_slot(session_attributes, intent_name, slots, slot_to_elicit, message):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'ElicitSlot',
            'intentName': intent_name,
            'slots': slots,
            'slotToElicit': slot_to_elicit,
            'message': message
        }
    }


def confirm_intent(session_attributes, intent_name, slots, message):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'ConfirmIntent',
            'intentName': intent_name,
            'slots': slots,
            'message': message
        }
    }


def close(session_attributes, fulfillment_state, message):
    response = {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'Close',
            'fulfillmentState': fulfillment_state,
            'message': message
        }
    }
    
    return response


def delegate(session_attributes, slots):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'Delegate',
            'slots': slots
        }
    }


# --- Helper Functions ---


def safe_int(n):
    """
    Safely convert n value to int.
    """
    if n is not None:
        return int(n)
      
    return n


def try_ex(func):
    """
    Call passed in function in try block. If KeyError is encountered return None.
    This function is intended to be used to safely access dictionary.
    Note that this function would have negative impact on performance.
    """
    try:
        return func()
    except KeyError:
        return None


# --- Insert your code here to improve your chatbot's functionality ---


def isvalid_car_type(car_type):
    car_types = ['economy', 'standard', 'midsize', 'full size', 'minivan', 'luxury']
    return car_type.lower() in car_types


def isvalid_city(city):
    valid_cities = ['sydney', 'brisbane', 'melbourne', 'perth', 'cairns', 'adelaide', 'darwin',
                    'gold coast', 'townsville', 'mount isa', 'kununurra', 'newcastle', 'mackay', 'hobart',
                    'launceston', 'cloncurry', 'paraburdoo', 'karratha', 'kalgoorlie boulder', 'learmonth',
                    'port macquarie', 'port hedland', 'canberra', 'coffs harbour', 'geraldton', 'ayers rock',
                    'alice springs', 'albury', 'hamilton island', 'sunshine coast']
    return city.lower() in valid_cities


def isvalid_room_type(room_type):
    room_types = ['queen', 'king', 'deluxe']
    return room_type.lower() in room_types


def isvalid_view_preference(view_preference):
    view_preferences = ['view', 'no view', 'either']
    return view_preference.lower() in view_preferences


def isvalid_departure_time(departure_time):
    departure_times = ['morning', 'afternoon']
    return departure_time.lower() in departure_times


def isvalid_cabin_class(cabin_class):
    cabin_classes = ['first class', 'first', 'business class', 'business', 'economy']
    return cabin_class.lower() in cabin_classes


def isvalid_date(date):
    try:
        dateutil.parser.parse(date)
        return True
    except ValueError:
        return False
    
    
def get_day_difference(later_date, earlier_date):
    later_datetime = dateutil.parser.parse(later_date).date()
    earlier_datetime = dateutil.parser.parse(earlier_date).date()
    return abs(later_datetime - earlier_datetime).days


def add_days(date, number_of_days):
    new_date = dateutil.parser.parse(date).date()
    new_date += datetime.timedelta(days=number_of_days)
    return new_date.strftime('%Y-%m-%d')


def build_validation_result(isvalid, violated_slot, message_content):
    return {
        'isValid': isvalid,
        'violatedSlot': violated_slot,
        'message': {'contentType': 'PlainText', 'content': message_content}
    }


def validate_book_car(slots):
    pickup_city = try_ex(lambda: slots['PickUpCity'])
    pickup_date = try_ex(lambda: slots['PickUpDate'])
    return_date = try_ex(lambda: slots['ReturnDate'])
    driver_age = safe_int(try_ex(lambda: slots['DriverAge']))
    car_type = try_ex(lambda: slots['CarType'])

    if pickup_city and not isvalid_city(pickup_city):
        return build_validation_result(
            False,
            'PickUpCity',
            'We currently do not support {} as a valid destination.  Can you try a different city?'.format(pickup_city)
        )

    if pickup_date:
        if not isvalid_date(pickup_date):
            return build_validation_result(False, 'PickUpDate', 'I did not understand your departure date.  When would you like to pick up your car rental?')
        if datetime.datetime.strptime(pickup_date, '%Y-%m-%d').date() <= datetime.date.today():
            return build_validation_result(False, 'PickUpDate', 'Reservations must be scheduled at least one day in advance.  Can you try a different date?')

    if return_date:
        if not isvalid_date(return_date):
            return build_validation_result(False, 'ReturnDate', 'I did not understand your return date.  When would you like to return your car rental?')

    if pickup_date and return_date:
        if dateutil.parser.parse(pickup_date) >= dateutil.parser.parse(return_date):
            return build_validation_result(False, 'ReturnDate', 'Your return date must be after your pick up date.  Can you try a different return date?')

        if get_day_difference(pickup_date, return_date) > 30:
            return build_validation_result(False, 'ReturnDate', 'You can reserve a car for up to thirty days.  Can you try a different return date?')

    if driver_age is not None and driver_age < 18:
        return build_validation_result(
            False,
            'DriverAge',
            'Your driver must be at least eighteen to rent a car.  Can you provide the age of a different driver?'
        )

    if car_type and not isvalid_car_type(car_type):
        return build_validation_result(
            False,
            'CarType',
            'I did not recognize that model.  What type of car would you like to rent?  '
            'Popular cars are economy, midsize, or luxury')

    return {'isValid': True}


def validate_hotel(slots):
    location = try_ex(lambda: slots['AU_Location'])
    checkin_date = try_ex(lambda: slots['CheckInDate'])
    nights = safe_int(try_ex(lambda: slots['Nights']))
    room_type = try_ex(lambda: slots['RoomType'])
    view_preference = try_ex(lambda: slots['ViewPreference'])

    if location and not isvalid_city(location):
        return build_validation_result(
            False,
            'AU_Location',
            'We currently do not support {} as a valid destination.  Can you try a different city?'.format(location)
        )

    if checkin_date:
        if not isvalid_date(checkin_date):
            return build_validation_result(False, 'CheckInDate', 'I did not understand your check in date.  When would you like to check in?')
        if datetime.datetime.strptime(checkin_date, '%Y-%m-%d').date() <= datetime.date.today():
            return build_validation_result(False, 'CheckInDate', 'Reservations must be scheduled at least one day in advance.  Can you try a different date?')

    if nights is not None and (nights < 1 or nights > 30):
        return build_validation_result(
            False,
            'Nights',
            'You can make a reservations for from one to thirty nights.  How many nights would you like to stay for?'
        )

    if room_type and not isvalid_room_type(room_type):
        return build_validation_result(False, 'RoomType', 'I did not recognize that room type.  Would you like to stay in a queen, king, or deluxe room?')

    if view_preference and not isvalid_view_preference(view_preference):
        return build_validation_result(False, 'ViewPreference', 'I did not recognize your room view preference.  Would you like to stay in room with a view, no view, or either?')
    
    return {'isValid': True}


def validate_flight(slots):
    au_departing = try_ex(lambda: slots['AU_Departing'])
    au_destination = try_ex(lambda: slots['AU_Destination'])
    flight_date = try_ex(lambda: slots['FlightDate'])
    departure_time = try_ex(lambda: slots['DepartureTime'])
    cabin_class = try_ex(lambda: slots['CabinClass'])
    
    if au_departing and not isvalid_city(au_departing):
        return build_validation_result(
            False,
            'AU_Departing',
            'We currently do not support {} as a valid departure location.  Can you try a different city?'.format(au_departing)
        )
    
    if au_destination and not isvalid_city(au_destination):
        return build_validation_result(
            False,
            'AU_Destination',
            'We currently do not support {} as a valid destination.  Can you try a different city?'.format(au_departing)
        )
    
    if flight_date:
        if not isvalid_date(flight_date):
            return build_validation_result(False, 'FlightDate', 'I did not understand your check in date.  When would you like to depart?')
        if datetime.datetime.strptime(flight_date, '%Y-%m-%d').date() <= datetime.date.today():
            return build_validation_result(False, 'FlightDate', 'Boarding passes must be scheduled at least one day in advance.  Can you try a different departure date?')

    if departure_time and not isvalid_departure_time(departure_time):
        return build_validation_result(False, 'DepartureTime', 'I did not understand that departure time. When would you like to depart: morning or afternoon?')

    if cabin_class and not isvalid_cabin_class(cabin_class):
        return build_validation_result(False, 'CabinClass', 'I did not recognize that cabin class.  Would you like to travel in first class, business class, or economy?')

    return {'isValid': True}


""" --- Functions that control the bot's behavior --- """


def book_hotel(intent_request):
    """
    Performs dialog management and fulfillment for booking a hotel.
    Beyond fulfillment, the implementation for this intent demonstrates the following:
    1) Use of elicitSlot in slot validation and re-prompting
    2) Use of sessionAttributes to pass information that can be used to guide conversation
    """

    au_location = try_ex(lambda: intent_request['currentIntent']['slots']['AU_Location'])
    checkin_date = try_ex(lambda: intent_request['currentIntent']['slots']['CheckInDate'])
    nights = safe_int(try_ex(lambda: intent_request['currentIntent']['slots']['Nights']))
    room_type = try_ex(lambda: intent_request['currentIntent']['slots']['RoomType'])
    view_preference = try_ex(lambda: intent_request['currentIntent']['slots']['ViewPreference'])
    session_attributes = intent_request['sessionAttributes'] if intent_request['sessionAttributes'] is not None else {}

    # Load confirmation history and track the current reservation.
    reservation = json.dumps({
        'ReservationType': 'Hotel',
        'AU_Location': au_location,
        'RoomType': room_type,
        'CheckInDate': checkin_date,
        'Nights': nights,
        'ViewPreference': view_preference
    })

    session_attributes['currentReservation'] = reservation

    if intent_request['invocationSource'] == 'DialogCodeHook':
        # Validate any slots which have been specified.  If any are invalid, re-elicit for their value
        validation_result = validate_hotel(intent_request['currentIntent']['slots'])
        if not validation_result['isValid']:
            slots = intent_request['currentIntent']['slots']
            slots[validation_result['violatedSlot']] = None

            return elicit_slot(
                session_attributes,
                intent_request['currentIntent']['name'],
                slots,
                validation_result['violatedSlot'],
                validation_result['message']
            )
        
        session_attributes['currentReservation'] = reservation
        return delegate(session_attributes, intent_request['currentIntent']['slots'])

    # Booking the hotel.  In a real application, this would likely involve a call to a backend service.
    logger.debug('bookHotel at={}'.format(reservation))
    del session_attributes['currentReservation']
    session_attributes['lastConfirmedReservation'] = reservation
    
    return close(
        session_attributes,
        'Fulfilled',
        {
            'contentType': 'PlainText',
            'content': 'Thanks, I have placed your reservation.'
        }
    )


def book_flight(intent_request):
    """
    Performs dialog management and fulfillment for booking a flight.
    Beyond fulfillment, the implementation for this intent demonstrates the following:
    1) Use of elicitSlot in slot validation and re-prompting
    2) Use of sessionAttributes to pass information that can be used to guide conversation
    """
    slots = intent_request['currentIntent']['slots']
    au_departing = slots['AU_Departing']
    au_destination = slots['AU_Destination']
    flight_date = slots['FlightDate']
    departure_time = slots['DepartureTime']
    cabin_class = slots['CabinClass']
    confirmation_status = intent_request['currentIntent']['confirmationStatus']
    session_attributes = intent_request['sessionAttributes'] if intent_request['sessionAttributes'] is not None else {}
    last_confirmed_reservation = try_ex(lambda: session_attributes['lastConfirmedReservation'])
    if last_confirmed_reservation:
        last_confirmed_reservation = json.loads(last_confirmed_reservation)
    confirmation_context = try_ex(lambda: session_attributes['confirmationContext'])

    # Load confirmation history and track the current reservation.
    reservation = json.dumps({
        'ReservationType': 'Flight',
        'AU_Departing': au_departing,
        'AU_Destination': au_destination,
        'FlightDate': flight_date,
        'DepartureTime': departure_time,
        'CabinClass': cabin_class
    })
    session_attributes['currentReservation'] = reservation

    if intent_request['invocationSource'] == 'DialogCodeHook':
        # Validate any slots which have been specified.  If any are invalid, re-elicit for their value
        validation_result = validate_flight(intent_request['currentIntent']['slots'])
        if not validation_result['isValid']:
            slots[validation_result['violatedSlot']] = None
            return elicit_slot(
                session_attributes,
                intent_request['currentIntent']['name'],
                slots,
                validation_result['violatedSlot'],
                validation_result['message']
            )

        # Determine if the intent (and current slot settings) has been denied.  The messaging will be different
        # if the user is denying a reservation they initiated or an auto-populated suggestion.
        if confirmation_status == 'Denied':
            # Clear out auto-population flag for subsequent turns.
            try_ex(lambda: session_attributes.pop('confirmationContext'))
            try_ex(lambda: session_attributes.pop('currentReservation'))
            if confirmation_context == 'AutoPopulate':
                return elicit_slot(
                    session_attributes,
                    intent_request['currentIntent']['name'],
                    {
                        'AU_Departing': None,
                        'AU_Destination': None,
                        'FlightDate': None,
                        'DepartureTime': None,
                        'CabinClass': None
                    },
                    'AU_Departing',
                    {
                        'contentType': 'PlainText',
                        'content': 'What Australian airport are you departing from?'
                    }
                )

            return delegate(session_attributes, intent_request['currentIntent']['slots'])

        if confirmation_status == 'None':
            # If we are currently auto-populating but have not gotten confirmation, keep requesting for confirmation.
            if (not au_departing and not au_destination and not flight_date and not departure_time and not cabin_class)\
                    or confirmation_context == 'AutoPopulate':
                if last_confirmed_reservation and try_ex(lambda: last_confirmed_reservation['ReservationType']) == 'Hotel':
                    # If the user's previous reservation was a hotel - prompt for a rental with
                    # auto-populated values to match this reservation.
                    session_attributes['confirmationContext'] = 'AutoPopulate'
                    return confirm_intent(
                        session_attributes,
                        intent_request['currentIntent']['name'],
                        {
                            'AU_Destination': last_confirmed_reservation['AU_Location'],
                            'FlightDate': last_confirmed_reservation['CheckInDate'],
                            'AU_Departing': None,
                            'DepartureTime': None,
                            'CabinClass': None
                        },
                        {
                            'contentType': 'PlainText',
                            'content': 'Is this flight for your {} night stay in {} on {}?'.format(
                                last_confirmed_reservation['Nights'],
                                last_confirmed_reservation['AU_Location'],
                                last_confirmed_reservation['CheckInDate']
                            )
                        }
                    )
              

            # Otherwise, let native DM rules determine how to elicit for slots and/or drive confirmation.
            return delegate(session_attributes, intent_request['currentIntent']['slots'])

        # If confirmation has occurred, continue filling any unfilled slot values or pass to fulfillment.
        if confirmation_status == 'Confirmed':
            # Remove confirmationContext from sessionAttributes so it does not confuse future requests
            try_ex(lambda: session_attributes.pop('confirmationContext'))
            if confirmation_context == 'AutoPopulate':
                if not departure_time:
                    return elicit_slot(
                        session_attributes,
                        intent_request['currentIntent']['name'],
                        intent_request['currentIntent']['slots'],
                        'DepartureTime',
                        {
                            'contentType': 'PlainText',
                            'content': 'What time do you want to depart? I can give you a morning or afternoon flight.'
                        }
                    )
                elif not cabin_class:
                    return elicit_slot(
                        session_attributes,
                        intent_request['currentIntent']['name'],
                        intent_request['currentIntent']['slots'],
                        'CabinClass',
                        {
                            'contentType': 'PlainText',
                            'content': 'Which cabin class would you like? I have economy, business, and first class options.'
                        }
                    )

            return delegate(session_attributes, intent_request['currentIntent']['slots'])

    # Booking the car.  In a real application, this would likely involve a call to a backend service.
    logger.debug('bookFlight at={}'.format(reservation))
    del session_attributes['currentReservation']
    session_attributes['lastConfirmedReservation'] = reservation
    return close(
        session_attributes,
        'Fulfilled',
        {
            'contentType': 'PlainText',
            'content': 'Thanks, I have placed your reservation.'
        }
    )

def book_car(intent_request):
    """
    Performs dialog management and fulfillment for booking a car.
    Beyond fulfillment, the implementation for this intent demonstrates the following:
    1) Use of elicitSlot in slot validation and re-prompting
    2) Use of sessionAttributes to pass information that can be used to guide conversation
    """
    slots = intent_request['currentIntent']['slots']
    pickup_city = slots['PickUpCity']
    pickup_date = slots['PickUpDate']
    return_date = slots['ReturnDate']
    driver_age = slots['DriverAge']
    car_type = slots['CarType']
    confirmation_status = intent_request['currentIntent']['confirmationStatus']
    session_attributes = intent_request['sessionAttributes'] if intent_request['sessionAttributes'] is not None else {}
    last_confirmed_reservation = try_ex(lambda: session_attributes['lastConfirmedReservation'])
    if last_confirmed_reservation:
        last_confirmed_reservation = json.loads(last_confirmed_reservation)
    confirmation_context = try_ex(lambda: session_attributes['confirmationContext'])

    # Load confirmation history and track the current reservation.
    reservation = json.dumps({
        'ReservationType': 'Car',
        'PickUpCity': pickup_city,
        'PickUpDate': pickup_date,
        'ReturnDate': return_date,
        'DriverAge': driver_age,
        'CarType': car_type
    })
    session_attributes['currentReservation'] = reservation

    if intent_request['invocationSource'] == 'DialogCodeHook':
        # Validate any slots which have been specified.  If any are invalid, re-elicit for their value
        validation_result = validate_book_car(intent_request['currentIntent']['slots'])
        if not validation_result['isValid']:
            slots[validation_result['violatedSlot']] = None
            return elicit_slot(
                session_attributes,
                intent_request['currentIntent']['name'],
                slots,
                validation_result['violatedSlot'],
                validation_result['message']
            )

        # Determine if the intent (and current slot settings) has been denied.  The messaging will be different
        # if the user is denying a reservation they initiated or an auto-populated suggestion.
        if confirmation_status == 'Denied':
            # Clear out auto-population flag for subsequent turns.
            try_ex(lambda: session_attributes.pop('confirmationContext'))
            try_ex(lambda: session_attributes.pop('currentReservation'))
            if confirmation_context == 'AutoPopulate':
                return elicit_slot(
                    session_attributes,
                    intent_request['currentIntent']['name'],
                    {
                        'PickUpCity': None,
                        'PickUpDate': None,
                        'ReturnDate': None,
                        'DriverAge': None,
                        'CarType': None
                    },
                    'PickUpCity',
                    {
                        'contentType': 'PlainText',
                        'content': 'Where would you like to make your car reservation?'
                    }
                )

            return delegate(session_attributes, intent_request['currentIntent']['slots'])

        if confirmation_status == 'None':
            # If we are currently auto-populating but have not gotten confirmation, keep requesting for confirmation.
            if (not pickup_city and not pickup_date and not return_date and not driver_age and not car_type)\
                    or confirmation_context == 'AutoPopulate':
                if last_confirmed_reservation and try_ex(lambda: last_confirmed_reservation['ReservationType']) == 'Hotel':
                    # If the user's previous reservation was a hotel - prompt for a rental with
                    # auto-populated values to match this reservation.
                    session_attributes['confirmationContext'] = 'AutoPopulate'
                    return confirm_intent(
                        session_attributes,
                        intent_request['currentIntent']['name'],
                        {
                            'PickUpCity': last_confirmed_reservation['AU_Location'],
                            'PickUpDate': last_confirmed_reservation['CheckInDate'],
                            'ReturnDate': add_days(
                                last_confirmed_reservation['CheckInDate'], last_confirmed_reservation['Nights']
                            ),
                            'CarType': None,
                            'DriverAge': None
                        },
                        {
                            'contentType': 'PlainText',
                            'content': 'Is this car rental for your {} night stay in {} on {}?'.format(
                                last_confirmed_reservation['Nights'],
                                last_confirmed_reservation['AU_Location'],
                                last_confirmed_reservation['CheckInDate']
                            )
                        }
                    )

            # Otherwise, let native DM rules determine how to elicit for slots and/or drive confirmation.
            return delegate(session_attributes, intent_request['currentIntent']['slots'])

        # If confirmation has occurred, continue filling any unfilled slot values or pass to fulfillment.
        if confirmation_status == 'Confirmed':
            # Remove confirmationContext from sessionAttributes so it does not confuse future requests
            try_ex(lambda: session_attributes.pop('confirmationContext'))
            if confirmation_context == 'AutoPopulate':
                if not driver_age:
                    return elicit_slot(
                        session_attributes,
                        intent_request['currentIntent']['name'],
                        intent_request['currentIntent']['slots'],
                        'DriverAge',
                        {
                            'contentType': 'PlainText',
                            'content': 'How old is the driver of this car rental?'
                        }
                    )
                elif not car_type:
                    return elicit_slot(
                        session_attributes,
                        intent_request['currentIntent']['name'],
                        intent_request['currentIntent']['slots'],
                        'CarType',
                        {
                            'contentType': 'PlainText',
                            'content': 'What type of car would you like? Popular models are '
                                       'economy, midsize, and luxury.'
                        }
                    )

            return delegate(session_attributes, intent_request['currentIntent']['slots'])

    # Booking the car.  In a real application, this would likely involve a call to a backend service.
    logger.debug('bookCar at={}'.format(reservation))
    del session_attributes['currentReservation']
    session_attributes['lastConfirmedReservation'] = reservation
    return close(
        session_attributes,
        'Fulfilled',
        {
            'contentType': 'PlainText',
            'content': 'Thanks, I have placed your reservation.'
        }
    )


# --- Intents ---


def dispatch(intent_request):
    """
    Called when the user specifies an intent for this bot.
    """

    logger.debug('dispatch userId={}, intentName={}'.format(intent_request['userId'], intent_request['currentIntent']['name']))

    intent_name = intent_request['currentIntent']['name']

    # Dispatch to your bot's intent handlers
    if intent_name == 'BookHotel':
        return book_hotel(intent_request)
    elif intent_name == 'BookCar':
        return book_car(intent_request)
    elif intent_name == 'BookFlight':
        return book_flight(intent_request)

    raise Exception('Intent with name ' + intent_name + ' not supported')
    

# --- Main handler sample code to edit---
def lambda_handler(event, context):
    """
    Route the incoming request based on intent.
    The JSON body of the request is provided in the event slot.
    """
    # By default, treat the user request as coming from the America/New_York time zone.
    os.environ['TZ'] = 'Australia/Sydney'
    time.tzset()
    logger.debug('event.bot.name={}'.format(event['bot']['name']))

    return dispatch(event)
  
