import numpy
import netCDF4


def _get_statistics(array: numpy.array, axis: tuple, statistic: str = 'mean'):
    if statistic == 'mean':
        series = numpy.mean(array, axis)

    return series


def _add_dimensional_axis(axis_dimension, axis_dimension_values, computed_series, axis_dimension_type,
                          datetime_to_string, datetime_format):
    if axis_dimension_type == 'T':
        axis_values = []

        if 'calendar' in axis_dimension.__dict__:
            calendar = axis_dimension.__dict__['calendar']
        else:
            calendar = 'standard'

        if 'units' in axis_dimension.__dict__:
            units = axis_dimension.__dict__['units']
        else:
            units = 'days since 2000-1-1 0:0:0'

        new_axis_values = netCDF4.num2date(axis_dimension_values[:], units, calendar)

        if datetime_to_string:
            if isinstance(new_axis_values, numpy.ma.core.MaskedArray):
                for date_value in new_axis_values:
                    axis_values.append(date_value.strftime(datetime_format))
            else:
                axis_values.append(new_axis_values.strftime(datetime_format))

    else:
        axis_values = axis_dimension_values[:]

    # if not numpy.array(axis_values).shape == computed_series.shape:
    #     computed_series = computed_series[:, 0, 0]

    series = numpy.column_stack((axis_values, computed_series))
    return series


def _scale_and_add_offset(variable: netCDF4.Dataset, array: numpy.array):
    if hasattr(variable, 'scale_factor'):
        scale_factor = variable.scale_factor
    else:
        scale_factor = 1
    if hasattr(variable, 'add_offset'):
        add_offset = variable.add_offset
    else:
        add_offset = 0

    new_array = (array * scale_factor) + add_offset

    return new_array
