from timepro_timesheet.utils import convert_time_string_and_minutes_to_hours


def test_convert_time_string_and_minutes_to_hours():
    assert convert_time_string_and_minutes_to_hours('13') == 13.0
    assert convert_time_string_and_minutes_to_hours('13:00') == 13.0
    assert convert_time_string_and_minutes_to_hours('13.5') == 13.5
    assert convert_time_string_and_minutes_to_hours('13:30') == 13.5

    exception = None
    try:
        convert_time_string_and_minutes_to_hours('13:30:30')
    except Exception as e:
        exception = e

    assert isinstance(exception, ValueError)
