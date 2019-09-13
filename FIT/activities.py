# Copyright 2019 Joan Puig
# See LICENSE for details


from typing import Tuple, Type

import FIT
from FIT.decoder import Decoder
from FIT.messages import FileId, Sport, Record
from FIT.model import Message
from FIT.types import File
import pandas as pd

class FITFileUnrecognizedActivityError(Exception):
    pass


class ActivityDecoder:
    @staticmethod
    def can_decode(messages: Tuple[Message]) -> bool:
        pass

    @staticmethod
    def decode(messages: Tuple[Message]):
        pass

    @staticmethod
    def decode_activity(file_name: str, error_on_undocumented_message: bool = False, error_on_undocumented_field: bool = False, error_on_invalid_enum_value: bool = False, activity_decoders: Tuple["ActivityDecoder"] = None):
        messages = Decoder.decode_fit_messages(file_name, error_on_undocumented_message, error_on_undocumented_field, error_on_invalid_enum_value)

        if activity_decoders is None:
            activity_decoders = default_decoders()

        for decoder in activity_decoders:
            if decoder.can_decode(messages):
                return decoder.decode(messages)

        raise FITFileUnrecognizedActivityError()


class RunningDecoder(ActivityDecoder):
    @staticmethod
    def can_decode(messages: Tuple[Message]):
        file_id_flag = False
        sport_flag = False
        record_flag = False

        for message in messages:
            file_id_flag = file_id_flag or isinstance(message, FileId) and message.type == File.Activity
            sport_flag = sport_flag or isinstance(message, Sport) and message.sport == FIT.types.Sport.Running
            record_flag = record_flag or isinstance(message, Record)

            if file_id_flag and sport_flag and record_flag:
                return True
        return False

    @staticmethod
    def decode(messages: Tuple[Message]):
        if not RunningDecoder.can_decode(messages):
            raise FITFileUnrecognizedActivityError('RunningDecoder is unable to decode the input messages')

        records = [message for message in messages if isinstance(message, Record)]

        fields_to_extract = (
            'timestamp',
            'position_lat',
            'position_long',
            'altitude',
            'heart_rate',
            'cadence',
            'distance',
            'speed',
            'temperature',
            'vertical_oscillation',
            'stance_time_percent',
            'stance_time',
            'fractional_cadence',
            'vertical_ratio',
            'stance_time_balance',
            'step_length',
        )

        output = pd.DataFrame()
        for field_to_extract in fields_to_extract:
            output[field_to_extract] = [record.__dict__[field_to_extract] for record in records]

        return output


def default_decoders() -> Tuple[Type[RunningDecoder]]:
    return (
        RunningDecoder,
    )

