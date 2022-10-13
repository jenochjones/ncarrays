import pyproj


def _create_transform_crs(grid_mapping_variable):
    grid_mapping_variable = grid_mapping_variable['dataset']

    if grid_mapping_variable is None:
        crs = pyproj.crs.CRS(4326)
    else:
        parameter_array = grid_mapping_variable.__dict__
        '''
        netcdf_to_proj_conversion = {
            'azimuth_of_central_line': 'alpha',
            'standard_parallel': 'lat_1',
            'latitude_of_projection_origin': 'lat_0',
            'longitude_of_projection_origin': 'lon_0',
            'longitude_of_central_meridian': 'lon_0',
            'perspective_point_height': 'h',
            'sweep_angle_axis': 'sweep',
            'false_easting': 'x_0',
            'false_northing': 'y_0',
            'scale_factor_at_projection_origin': 'k_0'
        }

        projection_specifiers = {
            'albers_conical_equal_area': {
                'epsg': None,
                'proj': 'aea',
                'params': {'lat_1': 0, 'lat_2': 0, 'lon_0': 0, 'ellps': 'GRS80', 'R': None, 'x_0': 0, 'y_0': 0}
            },
            'azimuthal_equidistant': {
                'epsg': None,
                'proj': 'aeqd',
                'params': {'guam': False, 'lat_0': 0, 'lon_0': 0, 'ellps': 'GRS80', 'R': None, 'x_0': 0, 'y_0': 0}
            },
            'geostationary': {
                'epsg': None,
                'proj': 'geos',
                'params': {'h': None, 'sweep': 'y', 'lon_0': 0, 'ellps': 'GRS80', 'R': None, 'x_0': 0, 'y_0': 0}
            },
            'lambert_azimuthal_equal_area': {
                'epsg': None,
                'proj': 'laea',
                'params': {'lon_0': 0, 'lat_0': 0, 'ellps': 'GRS80', 'R': None, 'x_0': 0, 'y_0': 0}
            },
            'lambert_conformal_conic': {
                'epsg': None,
                'proj': 'lcc',
                'params': {'lat_1': 0, 'lon_0': 0, 'lat_0': 0, 'lat_2': 0, 'ellps': 'GRS80', 'R': None, 'x_0': 0, 'y_0': 0, 'k_0': 1}
            },
            'lambert_cylindrical_equal_area': {'epsg': 9835},
            'latitude_longitude': {'epsg': 4326},
            'mercator': {
                'epsg': None,
                'proj': 'merc',
                'params': {'lat_ts': 0, 'k_0': 1, 'lon_0': 0, 'x_0': 0, 'y_0': 0, 'ellps': 'GRS80'}
            },
            'oblique_mercator': {
                'epsg': None,
                'proj': 'omerc',
                'params': {'alpha': 'no_default', 'gamma': None, 'lonc': 'no_default', 'lat0': 'no_default', 'no_off': False, 'k_0': 1, 'lon_0': 0, 'x_0': 0, 'y_0': 0}
            },
            'orthographic': {
                'epsg': None,
                'proj': 'ortho',
                'params': {'lon_0': 0, 'lat_0': 0, 'ellps': 'GRS80', 'R': None, 'x_0': 0, 'y_0': 0}
            },
            'polar_stereographic': {
                'epsg': None,
                'proj': 'ups',
                'params': {'south': None, 'lon_0': 0, 'ellps': 'GRS80', 'R': None, 'x_0': 0, 'y_0': 0}
            },
            'rotated_latitude_longitude': {
                'epsg': None,
                'required': None
            },
            'sinusoidal': {
                'epsg': None,
                'proj': 'gn_sinu',
                'params': {'lon_0': 0, 'R': None, 'x_0': 0, 'y_0': 0}
            },
            'stereographic': {
                'epsg': None,
                'proj': 'stere',
                'params': {'lat_0': 0, 'lat_ts': None, 'R': None, 'x_0': 0, 'y_0': 0}
            },
            'transverse_mercator': {
                'epsg': None,
                'proj': 'tmerc',
                'params': {'approx': None, 'algo': None, 'lon_0': 0, 'lat_0': 0, 'ellps': 'GRS80', 'R': None, 'k_0': 1, 'x_0': 0, 'y_0': 0}
            },
            'vertical_perspective': {
                'epsg': 9838
            }
        }

        if 'grid_mapping_name' in grid_mapping_variable.__dict__:
            grid_mapping_name = grid_mapping_variable.grid_mapping_name
            grid_mapping_attributes = grid_mapping_variable.__dict__

            if grid_mapping_name in projection_specifiers:
                proj_attributes = projection_specifiers[grid_mapping_name]
                if proj_attributes['epsg'] is not None:
                    crs_input = proj_attributes['epsg']
                else:
                    proj = proj_attributes['proj']
                    proj_string = f'+proj={proj}'
                    params = projection_specifiers[grid_mapping_name]['params']

                    for attribute in grid_mapping_attributes:
                        if attribute in netcdf_to_proj_conversion:
                            proj_name = netcdf_to_proj_conversion[attribute]

                            if proj_name in params:
                                proj_string += f' +{proj_name}={grid_mapping_attributes[attribute]}'
                                del params[proj_name]

                    for param in params:
                        if params[param] is not None and params[param] is not False:
                            if param is True:
                                proj_string += f' +{param}'
                            else:
                                proj_string += f' +{param}={params[param]}'

                    crs_input = proj_string

        crs = pyproj.crs.CRS(crs_input)
        '''
        crs = pyproj.CRS.from_cf(parameter_array)
    return crs
