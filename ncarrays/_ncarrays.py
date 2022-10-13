import netCDF4
import numpy
import geopandas

from ._geospatial_functions import _geojson_to_raster
from ._post_processing import _get_statistics, _add_dimensional_axis, _scale_and_add_offset
from ._variable_interpretation import _determine_variable_types, _retrieve_sub_variables


class ARRAY:
    def __init__(self, opendap_url: str, variable: str or list):
        main_variable = netCDF4.Dataset(opendap_url + '?' + variable).variables[variable]
        variables, variable_type_lists = _retrieve_sub_variables(opendap_url, main_variable)
        variables[variable] = {'dataset': main_variable, 'datatype': 'D'}

        variables = _determine_variable_types(variables, variable_type_lists)
        dim_order = main_variable.dimensions

        y_dim = []
        x_dim = []

        for dim in dim_order:
            if variables[dim]['datatype'] == 'Y':
                y_dim = variables[dim]['dataset'][:]
                # _scale_and_add_offset(variables[dim]['dataset'], variables[dim]['dataset'][:])
            elif variables[dim]['datatype'] == 'X':
                x_dim = variables[dim]['dataset'][:]
                # _scale_and_add_offset(variables[dim]['dataset'], variables[dim]['dataset'][:])

        self.dim_order = dim_order
        self.main_variable = main_variable
        self.opendap_url = opendap_url
        self.variable = variable
        self.variable_type_lists = variable_type_lists
        self.variables = variables
        self.x_dim = x_dim
        self.y_dim = y_dim

        if variable_type_lists['grid_mapping'] is not None:
            self.grid_mapping_variable = variables[variable_type_lists['grid_mapping']]
            if 'grid_mapping_name' in self.grid_mapping_variable['dataset'].__dict__:
                if self.grid_mapping_variable['dataset'].__dict__['grid_mapping_name'] == 'geostationary':
                    if 'perspective_point_height' in self.grid_mapping_variable['dataset'].__dict__:
                        height = self.grid_mapping_variable['dataset'].__dict__['perspective_point_height']
                        self.x_dim = self.x_dim * height
                        self.y_dim = self.y_dim * height
        else:
            self.grid_mapping_variable = None

    def get_series(self, path_to_geojson: str or None = None, axis: list or str = [], statistic: str = 'mean',
                   datetime_to_string: bool = True, datetime_format: str = '%m-%d-%Y %H:%M:%S'):
        subset_for_main_variable = []
        axis_dimension_type = None

        if path_to_geojson is not None:
            if len(self.y_dim) >= 0 or len(self.x_dim) >= 0:
                x_y_array, extents = _geojson_to_raster(path_to_geojson, self.x_dim, self.y_dim,
                                                        self.grid_mapping_variable)

                if len(x_y_array) > 0:
                    sub_x_y_array = x_y_array[extents[0]:extents[1], extents[2]:extents[3]]
                    sub_x_y_array = sub_x_y_array == False
            else:
                print('X and Y dimensions not found')

            if axis is not None:
                if axis in self.variables:
                    axis_dimension_type = self.variables[axis]['datatype']

            if len(x_y_array) <= 0:

                for dim in self.dim_order:
                    y_index = extents[0]
                    x_index = extents[1]

                    if axis is not None:
                        if dim == axis:
                            axis_dimension_type = self.variables[dim]['datatype']

                    if self.variables[dim]['datatype'] == 'Y':
                        subset_for_main_variable.append(slice(y_index - 1, y_index, 1))
                    elif self.variables[dim]['datatype'] == 'X':
                        subset_for_main_variable.append(slice(x_index - 1, x_index, 1))
                    else:
                        subset_for_main_variable.append(slice(None, None, 1))

                subset_for_main_variable = tuple(subset_for_main_variable)

                series = self.main_variable[subset_for_main_variable]

            else:
                array_shape_for_tile = []
                dim_type_order = []

                for dim in self.dim_order:
                    print(dim)
                    dim_type_order.append(self.variables[dim]['datatype'])

                    if self.variables[dim]['datatype'] == 'Y':
                        self.y_dim = self.variables[dim]['dataset'][:]
                        array_shape_for_tile.append(1)
                        subset_for_main_variable.append(slice(extents[0], extents[1], 1))
                    elif self.variables[dim]['datatype'] == 'X':
                        self.x_dim = self.variables[dim]['dataset'][:]
                        array_shape_for_tile.append(1)
                        subset_for_main_variable.append(slice(extents[2], extents[3], 1))
                    else:
                        # if dim in dimensional_values:
                        #     subset_for_main_variable.append(dimensional_values[dim])
                        #
                        #     if isinstance(dimensional_values[dim], int):
                        #         array_shape_for_tile.append(1)
                        #     elif isinstance(dimensional_values[dim], slice):
                        #         array_shape_for_tile.append(len(self.variables[dim]['dataset'][dimensional_values[dim]]))
                        #     else:
                        #         array_shape_for_tile.append(len(self.variables[dim]['dataset'][:]))
                        # else:
                        subset_for_main_variable.append(slice(None, None, 1))
                        array_shape_for_tile.append(len(self.variables[dim]['dataset'][:]))

            array_shape_for_tile = tuple(array_shape_for_tile)
            dim_type_order = tuple(dim_type_order)
            subset_for_main_variable = tuple(subset_for_main_variable)

            sub_main_array = self.main_variable[subset_for_main_variable]
            full_dimensional_array = numpy.tile(sub_x_y_array, array_shape_for_tile)

            masked_array = numpy.ma.masked_array(sub_main_array, mask=full_dimensional_array)

            axis_list = []

            for index, dim in enumerate(self.dim_order):
                if dim not in axis:
                    axis_list.append(index)

            axis_tuple = tuple(axis_list)

            series = _get_statistics(masked_array, axis_tuple, statistic)

        else:
            subset_for_main_variable = []

            for dim in self.dim_order:

                if self.axis is not None:
                    if dim == self.axis:
                        axis_dimension_type = self.variables[dim]['datatype']

                # if dim in dimensional_values:
                #     subset_for_main_variable.append(dimensional_values[dim])
                # else:
                subset_for_main_variable.append(slice(None, None, 1))

            subset_for_main_variable = tuple(subset_for_main_variable)
            sub_main_array = self.main_variable[subset_for_main_variable]

            axis_list = []

            for index, dim in enumerate(self.dim_order):
                if dim not in axis:
                    axis_list.append(index)

            axis_tuple = tuple(axis_list)

            series = _get_statistics(sub_main_array, axis_tuple, statistic)

        if (isinstance(axis, str) and axis is not None) or (isinstance(axis, list) and len(axis) == 1):
            if isinstance(axis, list):
                axis_name = axis[0]
            else:
                axis_name = axis
            # if axis_name in dimensional_values:
            #     axis_dimension_values = self.variables[axis_name]['dataset'][dimensional_values[axis_name]]
            # else:
            if len(self.variables[axis_name]['dataset'].shape) == 0:
                axis_dimension_values = self.variables[axis_name]['dataset']
            else:
                axis_dimension_values = self.variables[axis_name]['dataset'][:]

            series = _add_dimensional_axis(self.variables[axis_name]['dataset'], axis_dimension_values, series,
                                           axis_dimension_type, datetime_to_string, datetime_format)
        elif isinstance(axis, str) and axis is not None:
            print('still figuring this out')

        return series

    def get_spatial_info(self):
        min_x_dim = min(self.x_dim)
        max_x_dim = max(self.x_dim)
        min_y_dim = min(self.y_dim)
        max_y_dim = max(self.y_dim)
        x_interval = numpy.average((self.x_dim - numpy.append(self.x_dim[1:], self.x_dim[0]))[:-1])
        y_interval = numpy.average((self.y_dim - numpy.append(self.y_dim[1:], self.y_dim[0]))[:-1])

        if 'grid_mapping' in self.variable_type_lists:
            grid_mapping_name = self.variables[self.variable_type_lists['grid_mapping']]['dataset'].grid_mapping_name

        print(f'The projection used is {grid_mapping_name}')
        print(f'The x dimension spans form {min_x_dim} to {max_x_dim} at an average interval of {x_interval}.')
        print(f'The y dimension spans from {min_y_dim} to {max_y_dim} at an average interval of {y_interval}.')
        return {'x_dim': {'max': max_x_dim, 'min': min_x_dim, 'interval': x_interval},
                'y_dim': {'max': max_y_dim, 'min': min_y_dim, 'interval': y_interval}}


def get_geojson_info(path_to_geojson):
    print(path_to_geojson)


def convert_shapefile_to_geojson(path_to_shapefile: str, path_to_geojson: str):
    geojson = geopandas.read_file(path_to_shapefile)
    geojson.to_file(path_to_geojson, driver="GeoJSON")
